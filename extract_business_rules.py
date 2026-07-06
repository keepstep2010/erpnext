#!/usr/bin/env python3
import ast
import glob
import json
import os
import re
import sys
from collections import defaultdict

COMMON_LIFECYCLE_HOOKS = {
    "setup",
    "onload",
    "refresh",
    "validate",
    "on_submit",
    "before_save",
    "before_insert",
    "before_submit",
    "on_cancel",
    "onload_post_render",
}

JS_KEYWORDS = {
    "if",
    "else",
    "for",
    "while",
    "do",
    "switch",
    "case",
    "break",
    "continue",
    "return",
    "function",
    "var",
    "let",
    "const",
    "class",
    "this",
    "new",
    "typeof",
    "instanceof",
    "in",
    "of",
    "try",
    "catch",
    "finally",
    "throw",
    "debugger",
    "import",
    "export",
    "default",
    "null",
    "undefined",
    "true",
    "false",
    "extends",
    "super",
    "with",
    "yield",
    "await",
    "async",
    "setup",
    "onload",
    "refresh",
    "validate",
    "on_submit",
    "before_save",
    "before_insert",
    "before_submit",
    "on_cancel",
    "onload_post_render",
    "frm",
    "me",
    "doc",
    "cdt",
    "cdn",
    "args",
}

RELEVANT_METHOD_PREFIXES = (
    "validate_",
    "check_",
    "before_",
    "after_",
    "on_",
    "set_",
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = SCRIPT_DIR if os.path.exists(os.path.join(SCRIPT_DIR, "erpnext")) else os.getcwd()
DOCTYPE_ROOT = os.path.join(REPO_ROOT, "erpnext")


def truthy(value):
    return value in (1, True, "1", "true", "True")


def normalize_name(name):
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


class RuleExtractor:
    def __init__(self, doctype, json_path, data):
        self.doctype = doctype
        self.json_path = json_path
        self.path = os.path.dirname(json_path)
        self.data = data
        self.base_name = os.path.splitext(os.path.basename(json_path))[0]
        self.py_path = os.path.join(self.path, f"{self.base_name}.py")
        self.js_path = os.path.join(self.path, f"{self.base_name}.js")

    def _expr_text(self, node):
        if node is None:
            return ""
        try:
            return ast.unparse(node)
        except Exception:
            return ast.dump(node, annotate_fields=False, include_attributes=False)

    def _normalize_text(self, value):
        return re.sub(r"\s+", " ", value or "").strip()

    def _get_string_values(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return [node.value]
        if isinstance(node, ast.Str):
            return [node.s]
        if isinstance(node, ast.Call):
            strings = []
            for arg in node.args:
                strings.extend(self._get_string_values(arg))
            for kw in node.keywords:
                strings.extend(self._get_string_values(kw.value))
            return strings
        if isinstance(node, ast.BinOp):
            return self._get_string_values(node.left) + self._get_string_values(node.right)
        if isinstance(node, ast.FormattedValue):
            return self._get_string_values(node.value)
        if isinstance(node, ast.JoinedStr):
            strings = []
            for val in node.values:
                strings.extend(self._get_string_values(val))
            return strings
        return []

    def _format_message(self, node):
        strings = []
        if isinstance(node, ast.Call):
            for arg in node.args:
                strings.extend(self._get_string_values(arg))
            for kw in node.keywords:
                strings.extend(self._get_string_values(kw.value))
            if strings:
                return self._normalize_text(" | ".join(s for s in strings if s and s.strip()))
            if node.args:
                return self._normalize_text(self._expr_text(node.args[0]))
        elif isinstance(node, ast.Raise):
            if node.exc:
                return self._format_message(node.exc) if isinstance(node.exc, ast.Call) else self._normalize_text(
                    self._expr_text(node.exc)
                )
        return ""

    def _is_message_call(self, node):
        if not isinstance(node, ast.Call):
            return None
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "frappe":
            if func.attr in ("throw", "msgprint"):
                return func.attr.capitalize()
        if isinstance(func, ast.Name) and func.id in ("throw", "msgprint"):
            return func.id.capitalize()
        return None

    def _collect_messages(self, nodes, conditions=None):
        if conditions is None:
            conditions = []
        if nodes is None:
            return []
        if not isinstance(nodes, list):
            nodes = [nodes]

        results = []
        for node in nodes:
            results.extend(self._collect_messages_from_node(node, conditions))
        return results

    def _collect_messages_from_node(self, node, conditions):
        results = []
        if node is None:
            return results

        if isinstance(node, ast.If):
            condition = self._normalize_text(self._expr_text(node.test))
            results.extend(self._collect_messages(node.body, conditions + [condition]))
            if node.orelse:
                results.extend(self._collect_messages(node.orelse, conditions + [f"not ({condition})"]))
            return results

        if isinstance(node, ast.Try):
            results.extend(self._collect_messages(node.body, conditions))
            for handler in node.handlers:
                handler_label = "except"
                if handler.type:
                    handler_label = f"except {self._normalize_text(self._expr_text(handler.type))}"
                results.extend(self._collect_messages(handler.body, conditions + [handler_label]))
            results.extend(self._collect_messages(node.orelse, conditions))
            results.extend(self._collect_messages(node.finalbody, conditions))
            return results

        if isinstance(node, ast.With):
            results.extend(self._collect_messages(node.body, conditions))
            return results

        if isinstance(node, ast.Raise):
            message = self._format_message(node)
            if message:
                results.append({"kind": "Raise", "message": message, "conditions": list(conditions)})
            for child in ast.iter_child_nodes(node):
                if child is not node.exc:
                    results.extend(self._collect_messages_from_node(child, conditions))
            return results

        kind = self._is_message_call(node)
        if kind:
            message = self._format_message(node)
            if message:
                results.append({"kind": kind, "message": message, "conditions": list(conditions)})

        for child in ast.iter_child_nodes(node):
            results.extend(self._collect_messages_from_node(child, conditions))
        return results

    def _collect_self_calls(self, node):
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                if isinstance(child.func.value, ast.Name) and child.func.value.id == "self":
                    calls.append((getattr(child, "lineno", 0), getattr(child, "col_offset", 0), child.func.attr))
        ordered = []
        seen = set()
        for _, _, name in sorted(calls):
            if name not in seen:
                ordered.append(name)
                seen.add(name)
        return ordered

    def _is_relevant_method(self, name, info):
        if name == "validate":
            return True
        if name.startswith(RELEVANT_METHOD_PREFIXES):
            return True
        return bool(info.get("messages"))

    def _method_info(self, node):
        return {
            "docstring": ast.get_docstring(node) or "",
            "self_calls": self._collect_self_calls(node),
            "messages": self._collect_messages(node.body),
            "lineno": getattr(node, "lineno", 0),
        }

    def _extract_docstring(self, node):
        doc = ast.get_docstring(node) or ""
        if not doc:
            return ""
        first_line = doc.strip().splitlines()[0].strip()
        return first_line

    def _select_primary_class(self, classes):
        if not classes:
            return None
        target = normalize_name(self.doctype)
        file_target = normalize_name(self.base_name)

        for cls in classes:
            normalized = normalize_name(cls["name"])
            if normalized == target or normalized == file_target:
                return cls

        for cls in classes:
            normalized = normalize_name(cls["name"])
            if target and (target in normalized or normalized in target):
                return cls

        return max(classes, key=lambda item: len(item.get("methods", {})))

    def extract_metadata(self):
        data = self.data
        fields = data.get("fields", [])
        categories = defaultdict(list)

        for field in fields:
            fname = field.get("fieldname")
            if not fname:
                continue
            flabel = field.get("label") or fname
            ftype = field.get("fieldtype") or "Data"
            display = f"`{fname}` ({flabel}) [{ftype}]"

            if field.get("reqd"):
                categories["mandatory"].append(display)
            if field.get("mandatory_depends_on"):
                categories["mandatory_conditional"].append(
                    f"`{fname}` ({flabel}) depends on: `{field.get('mandatory_depends_on')}`"
                )
            if field.get("read_only"):
                categories["read_only"].append(f"`{fname}` ({flabel})")
            if field.get("read_only_depends_on"):
                categories["read_only_conditional"].append(
                    f"`{fname}` ({flabel}) depends on: `{field.get('read_only_depends_on')}`"
                )
            if field.get("hidden"):
                categories["hidden"].append(f"`{fname}` ({flabel})")
            if field.get("hidden_depends_on"):
                categories["hidden_conditional"].append(
                    f"`{fname}` ({flabel}) depends on: `{field.get('hidden_depends_on')}`"
                )
            if field.get("fetch_from"):
                categories["fetch_from"].append(
                    f"`{fname}` ({flabel}) <- `{field.get('fetch_from')}`"
                )
            if field.get("depends_on"):
                categories["depends_on"].append(
                    f"`{fname}` ({flabel}) depends on: `{field.get('depends_on')}`"
                )
            if field.get("unique"):
                categories["unique"].append(f"`{fname}` ({flabel})")
            if field.get("set_only_once"):
                categories["set_only_once"].append(f"`{fname}` ({flabel})")
            if field.get("allow_on_submit"):
                categories["allow_on_submit"].append(f"`{fname}` ({flabel})")
            if field.get("no_copy"):
                categories["no_copy"].append(f"`{fname}` ({flabel})")
            if field.get("in_list_view"):
                categories["in_list_view"].append(f"`{fname}` ({flabel})")
            if field.get("in_standard_filter"):
                categories["in_standard_filter"].append(f"`{fname}` ({flabel})")
            if field.get("default") not in (None, ""):
                default_value = self._normalize_text(str(field.get("default")))
                categories["defaults"].append(f"`{fname}` ({flabel}) = `{default_value}`")
            if field.get("options") and ftype in {"Select", "Link", "Table", "Table MultiSelect"}:
                categories["options"].append(
                    f"`{fname}` ({flabel}) options: `{field.get('options')}`"
                )

        doc_flags = []
        for key in (
            "allow_import",
            "allow_auto_repeat",
            "editable_grid",
            "is_tree",
            "track_changes",
            "quick_entry",
            "allow_rename",
            "sort_field",
            "sort_order",
            "beta",
            "custom",
        ):
            value = data.get(key)
            if isinstance(value, bool) and value:
                doc_flags.append(f"{key}: Yes")
            elif isinstance(value, int) and value:
                doc_flags.append(f"{key}: Yes")
            elif isinstance(value, str) and value and key in {"sort_field", "sort_order"}:
                doc_flags.append(f"{key}: `{value}`")

        return {
            "name": data.get("name") or self.doctype,
            "module": data.get("module") or "Unknown",
            "naming": data.get("autoname") or "自动递增 ID",
            "document_type": data.get("document_type") or data.get("doctype") or "Document",
            "is_submittable": truthy(data.get("is_submittable")),
            "field_count": len(fields),
            "doctype_flags": doc_flags,
            "categories": categories,
        }

    def extract_python_rules(self):
        if not os.path.exists(self.py_path):
            return {"classes": [], "module_functions": {}}

        with open(self.py_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=self.py_path)

        classes = []
        module_functions = {}

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                base_classes = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_classes.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        if isinstance(base.value, ast.Name):
                            base_classes.append(f"{base.value.id}.{base.attr}")
                        else:
                            base_classes.append(base.attr)

                class_methods = {}
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        class_methods[item.name] = self._method_info(item)
                classes.append(
                    {
                        "name": node.name,
                        "bases": base_classes,
                        "methods": class_methods,
                    }
                )
            elif isinstance(node, ast.FunctionDef):
                module_functions[node.name] = self._method_info(node)

        return {"classes": classes, "module_functions": module_functions}

    def _format_control_messages(self, messages, indent="    "):
        lines = []
        for item in messages:
            if item.get("conditions"):
                lines.append(f"{indent}*   条件: `{' && '.join(item['conditions'])}`")
            lines.append(f"{indent}*   **[{item['kind']}]**: {item['message']}")
        return lines

    def _append_rule_section(self, report, title, methods):
        if not methods:
            return False

        added = False
        for name, info in methods:
            if not self._is_relevant_method(name, info):
                continue
            if not added:
                if title:
                    report.append(title)
                added = True
            doc = self._extract_docstring(info)
            suffix = f" ({doc})" if doc else ""
            report.append(f"*   `{name}`{suffix}:")
            if info.get("self_calls"):
                report.append("    *   调用链:")
                for call in info["self_calls"]:
                    report.append(f"        *   `self.{call}()`")
            if info.get("messages"):
                report.extend(self._format_control_messages(info["messages"], indent="    "))
            if not info.get("self_calls") and not info.get("messages"):
                report.append("    *   未提取到显式规则逻辑")
        if added:
            report.append("")
        return added

    def generate_report(self):
        meta = self.extract_metadata()
        py = self.extract_python_rules()
        js = self.extract_js_rules()

        report = []
        report.append(f"## {self.doctype} 业务规则矩阵 (Business Rules Matrix)")
        report.append("")

        main_class = self._select_primary_class(py.get("classes", []))

        report.append("### 1. 基础属性与控制规则")
        report.append(f"*   **模块**: {meta.get('module', 'Unknown')}")
        report.append(f"*   **字段总数**: {meta.get('field_count', 0)}")
        report.append(f"*   **命名规则 (Naming)**: `{meta.get('naming', '自动递增 ID')}`")
        report.append(f"*   **文档类型 (Document Type)**: `{meta.get('document_type', 'Document')}`")
        report.append(f"*   **是否可提交 (Is Submittable)**: {'是 (Yes)' if meta.get('is_submittable') else '否 (No)'}")

        if meta.get("doctype_flags"):
            report.append("*   **DocType 级控制标记**:")
            for flag in meta["doctype_flags"]:
                report.append(f"    *   {flag}")

        base_ctrl = "Document"
        if main_class:
            bases = main_class.get("bases", [])
            if bases:
                base_ctrl = ", ".join(bases)
        report.append(f"*   **继承基类 (Base Controller)**: `{base_ctrl}`")
        report.append("")

        report.append("#### 字段约束条件:")
        categories = meta.get("categories", {})
        category_titles = [
            ("mandatory", "*   **必填字段 (Mandatory)**:"),
            ("mandatory_conditional", "*   **条件必填字段**:"),
            ("read_only", "*   **只读字段 (Read Only)**:"),
            ("read_only_conditional", "*   **条件只读字段**:"),
            ("hidden", "*   **隐藏字段 (Hidden)**:"),
            ("hidden_conditional", "*   **条件隐藏字段**:"),
            ("fetch_from", "*   **自动带入规则 (Fetch From)**:"),
            ("depends_on", "*   **动态可见性与条件控制 (Depends On)**:"),
            ("unique", "*   **唯一性约束 (Unique)**:"),
            ("set_only_once", "*   **仅允许设置一次**:"),
            ("allow_on_submit", "*   **提交后仍可修改**:"),
            ("no_copy", "*   **复制时不带出**:"),
            ("in_list_view", "*   **列表视图字段**:"),
            ("in_standard_filter", "*   **标准筛选字段**:"),
            ("defaults", "*   **默认值 (Default)**:"),
            ("options", "*   **字段选项 (Options)**:"),
        ]
        for key, title in category_titles:
            values = categories.get(key, [])
            if values:
                report.append(title)
                for item in values:
                    report.append(f"    *   {item}")
        if not any(categories.values()):
            report.append("*   无可提取字段约束")
        report.append("")

        report.append("### 2. 前置校验与约束条件 (Validation Rules)")

        class_methods = []
        if main_class:
            class_methods = sorted(main_class.get("methods", {}).items(), key=lambda item: item[1].get("lineno", 0))

            validate_info = main_class.get("methods", {}).get("validate")
            if validate_info:
                report.append("#### `validate` 生命钩子执行校验流:")
                if validate_info.get("self_calls"):
                    report.append("在该钩子中按源码顺序调用了以下内部校验/处理函数:")
                    for call in validate_info["self_calls"]:
                        report.append(f"1.  `self.{call}()`")
                else:
                    report.append("执行直接内联校验。")
                if validate_info.get("messages"):
                    report.append("直属校验结果:")
                    report.extend(self._format_control_messages(validate_info["messages"], indent="    "))
                report.append("")

        module_methods = sorted(py.get("module_functions", {}).items(), key=lambda item: item[1].get("lineno", 0))
        validation_methods = []
        seen = set()
        for name, info in class_methods + module_methods:
            if name == "validate":
                continue
            if self._is_relevant_method(name, info) and name not in seen:
                validation_methods.append((name, info))
                seen.add(name)

        if validation_methods:
            report.append("#### 核心控制校验函数与报错信息:")
            for name, info in validation_methods:
                report.append(f"*   `{name}`:")
                if info.get("self_calls"):
                    report.append("    *   调用链:")
                    for call in info["self_calls"]:
                        report.append(f"        *   `self.{call}()`")
                if info.get("messages"):
                    report.extend(self._format_control_messages(info["messages"], indent="    "))
                if not info.get("self_calls") and not info.get("messages"):
                    report.append("    *   执行特定条件判定 (无硬性抛错/动态抛错)")
            report.append("")
        elif not main_class:
            report.append("未在 Python 控制器中找到显式的 `validate` 校验。")
            report.append("")

        report.append("### 3. 后置联动与过账逻辑 (Execution / Submission Rules)")
        execution_methods = []
        if main_class:
            for hook in ["before_insert", "before_save", "before_submit", "on_submit"]:
                info = main_class.get("methods", {}).get(hook)
                if info:
                    execution_methods.append((hook, info))
        if execution_methods:
            self._append_rule_section(report, "", execution_methods)
        else:
            report.append("该单据无特定的 `on_submit` 提交过账逻辑。")
            report.append("")

        report.append("### 4. 逆向/作废控制规则 (Cancellation Rules)")
        if main_class and "on_cancel" in main_class.get("methods", {}):
            on_cancel_info = main_class["methods"]["on_cancel"]
            report.append("*   `on_cancel`:")
            if on_cancel_info.get("self_calls"):
                report.append("    *   逆向联动回滚函数:")
                for call in on_cancel_info["self_calls"]:
                    report.append(f"        *   `self.{call}()`")
            if on_cancel_info.get("messages"):
                report.extend(self._format_control_messages(on_cancel_info["messages"], indent="    "))
            if not on_cancel_info.get("self_calls") and not on_cancel_info.get("messages"):
                report.append("    *   未提取到显式逆向/作废逻辑")
            report.append("")
        else:
            report.append("该单据无特定的 `on_cancel` 作废/回滚逻辑。")
            report.append("")

        report.append("### 5. 前端交互与客户端规则 (Client-Side Interactivity)")
        if js.get("form_bindings"):
            for bind in js["form_bindings"]:
                report.append(f"#### 页面绑定: `{bind['target']}`")
                if bind.get("hooks"):
                    report.append(f"*   **生命周期触发器**: `{', '.join(bind['hooks'])}`")
                if bind.get("field_triggers"):
                    report.append("*   **字段值变更触发事件 (Field Listeners)**:")
                    for trigger in bind["field_triggers"]:
                        report.append(f"    *   `{trigger}` 字段改变时触发前端计算或联动")
        else:
            report.append("未找到显式前端页面交互 JS 绑定。")

        if js.get("js_messages"):
            report.append("*   **前端弹窗或校验提示 (UI Warnings)**:")
            for msg in js["js_messages"][:25]:
                report.append(f"    *   {msg}")
        report.append("")
        report.append("---")
        report.append("")
        return "\n".join(report)


def discover_doctypes():
    pattern = os.path.join(DOCTYPE_ROOT, "**", "doctype", "*", "*.json")
    doctypes = []
    for json_path in sorted(glob.iglob(pattern, recursive=True)):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        if data.get("doctype") != "DocType":
            continue
        doctypes.append({
            "doctype": data.get("name") or os.path.splitext(os.path.basename(json_path))[0].replace("_", " ").title(),
            "json_path": json_path,
            "data": data,
        })
    return doctypes


def main():
    full_report = [
        "# ERPNext 核心业务对象业务规则整理报告",
        "本报告通过自动化脚本静态解析 ERPNext (元数据 JSON、Python 控制器 AST、Javascript 脚本) 提取所有可发现的业务对象规则，并按「基础属性与控制规则」、「前置校验与约束条件」、「后置联动与过账逻辑」、「逆向/作废控制规则」、「前端交互与客户端规则」五个维度整理成**业务规则矩阵 (Business Rules Matrix)**。",
        "",
        "---",
        "",
    ]

    discovered = discover_doctypes()
    print(f"Discovered {len(discovered)} DocType definitions.")
    for entry in discovered:
        doctype = entry["doctype"]
        json_path = entry["json_path"]
        print(f"Extracting rules for {doctype}...")
        extractor = RuleExtractor(doctype, json_path, entry["data"])
        full_report.append(extractor.generate_report())

    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    else:
        output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "business_rules_matrix.md")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(full_report))

    print(f"Report successfully generated at: {output_file}")


if __name__ == "__main__":
    main()
