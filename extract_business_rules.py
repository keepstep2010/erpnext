#!/usr/bin/env python3
import os
import sys
import json
import ast
import re

COMMON_LIFECYCLE_HOOKS = {
    "setup", "onload", "refresh", "validate", "on_submit", "before_save", "onload_post_render"
}

JS_KEYWORDS = {
    "if", "else", "for", "while", "do", "switch", "case", "break", "continue", "return",
    "function", "var", "let", "const", "class", "this", "new", "typeof", "instanceof",
    "in", "of", "try", "catch", "finally", "throw", "debugger", "import", "export",
    "default", "null", "undefined", "true", "false", "extends", "super", "with",
    "yield", "await", "async", "setup", "onload", "refresh", "validate", "on_submit",
    "before_save", "onload_post_render", "frm", "me", "doc", "cdt", "cdn", "args"
}

# Resolve the repository root dynamically (portable across environments)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = SCRIPT_DIR if os.path.exists(os.path.join(SCRIPT_DIR, "erpnext")) else os.getcwd()

DOCTYPES_RELATIVE = {
    "Customer": "erpnext/selling/doctype/customer",
    "Sales Order": "erpnext/selling/doctype/sales_order",
    "Delivery Note": "erpnext/stock/doctype/delivery_note",
    "Sales Invoice": "erpnext/accounts/doctype/sales_invoice",
    "Purchase Order": "erpnext/buying/doctype/purchase_order"
}

DOCTYPES = {}
for key, rel_path in DOCTYPES_RELATIVE.items():
    abs_path = os.path.join(REPO_ROOT, rel_path)
    # Handle possible extra nested erpnext/erpnext
    if not os.path.exists(abs_path):
        alternative = os.path.join(REPO_ROOT, "erpnext", rel_path)
        if os.path.exists(alternative):
            abs_path = alternative
    DOCTYPES[key] = abs_path

print("Resolved paths:", DOCTYPES)

class RuleExtractor:
    def __init__(self, doctype, path):
        self.doctype = doctype
        self.path = path
        self.json_path = os.path.join(path, f"{self.get_snake_case(doctype)}.json")
        self.py_path = os.path.join(path, f"{self.get_snake_case(doctype)}.py")
        self.js_path = os.path.join(path, f"{self.get_snake_case(doctype)}.js")
        
    def get_snake_case(self, name):
        return name.lower().replace(" ", "_")

    def extract_metadata(self):
        if not os.path.exists(self.json_path):
            return {}
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        fields = data.get("fields", [])
        mandatory = []
        read_only = []
        hidden = []
        fetch_from = []
        depends_on = []
        
        for field in fields:
            fname = field.get("fieldname")
            flabel = field.get("label") or fname
            ftype = field.get("fieldtype")
            
            if not fname:
                continue
                
            if field.get("reqd"):
                mandatory.append(f"`{fname}` ({flabel}) [{ftype}]")
            if field.get("read_only"):
                read_only.append(f"`{fname}` ({flabel})")
            if field.get("hidden"):
                hidden.append(f"`{fname}` ({flabel})")
            if field.get("fetch_from"):
                fetch_from.append(f"`{fname}` ({flabel}) <- `{field.get('fetch_from')}`")
            if field.get("depends_on"):
                depends_on.append(f"`{fname}` ({flabel}) depends on: `{field.get('depends_on')}`")
                
        is_submittable = data.get("is_submittable") in (1, True, "1")
        return {
            "name": data.get("name"),
            "module": data.get("module"),
            "naming": data.get("autoname"),
            "mandatory": mandatory,
            "read_only": read_only,
            "hidden": hidden,
            "fetch_from": fetch_from,
            "depends_on": depends_on,
            "is_submittable": is_submittable
        }

    def _get_string_values(self, node):
        """Recursively extract string literals from an AST node."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return [node.value]
        elif isinstance(node, ast.Str): # Older python compatibility
            return [node.s]
        elif isinstance(node, ast.Call):
            strings = []
            for arg in node.args:
                strings.extend(self._get_string_values(arg))
            for kw in node.keywords:
                strings.extend(self._get_string_values(kw.value))
            return strings
        elif isinstance(node, ast.BinOp):
            return self._get_string_values(node.left) + self._get_string_values(node.right)
        elif isinstance(node, ast.FormattedValue):
            return self._get_string_values(node.value)
        elif isinstance(node, ast.JoinedStr):
            strings = []
            for val in node.values:
                strings.extend(self._get_string_values(val))
            return strings
        return []

    def _find_throws(self, body_node):
        """Find all throw and msgprint calls in a function body."""
        throws = []
        for child in ast.walk(body_node):
            if isinstance(child, ast.Call):
                func = child.func
                is_throw = False
                is_msgprint = False
                
                # Check for frappe.throw or throw
                if isinstance(func, ast.Attribute):
                    if isinstance(func.value, ast.Name) and func.value.id == "frappe":
                        if func.attr == "throw":
                            is_throw = True
                        elif func.attr == "msgprint":
                            is_msgprint = True
                elif isinstance(func, ast.Name):
                    if func.id == "throw":
                        is_throw = True
                    elif func.id == "msgprint":
                        is_msgprint = True
                        
                if is_throw or is_msgprint:
                    strings = []
                    for arg in child.args:
                        strings.extend(self._get_string_values(arg))
                    msg = " | ".join([s.strip().replace("\n", " ") for s in strings if s.strip()])
                    call_type = "Throw" if is_throw else "Msgprint"
                    throws.append((call_type, msg or "Dynamic message"))
        return throws

    def _find_helper_calls(self, body_node):
        """Find calls to self.validate_... methods."""
        helpers = []
        for child in ast.walk(body_node):
            if isinstance(child, ast.Call):
                func = child.func
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "self":
                    if func.attr.startswith("validate_") or func.attr.startswith("set_"):
                        helpers.append(func.attr)
        return helpers

    def extract_python_rules(self):
        if not os.path.exists(self.py_path):
            return {}
            
        with open(self.py_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=self.py_path)
            
        classes = []
        module_functions = {}
        
        # Scan for functions and classes
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                base_classes = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_classes.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        base_classes.append(f"{base.value.id}.{base.attr}" if isinstance(base.value, ast.Name) else base.attr)
                
                class_methods = {}
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        # Extract throwing logic & helper calls
                        throws = self._find_throws(item)
                        helpers = self._find_helper_calls(item)
                        docstring = ast.get_docstring(item) or ""
                        class_methods[item.name] = {
                            "docstring": docstring,
                            "throws": throws,
                            "helpers": helpers
                        }
                classes.append({
                    "name": node.name,
                    "bases": base_classes,
                    "methods": class_methods
                })
            elif isinstance(node, ast.FunctionDef):
                throws = self._find_throws(node)
                docstring = ast.get_docstring(node) or ""
                module_functions[node.name] = {
                    "docstring": docstring,
                    "throws": throws
                }
                
        return {
            "classes": classes,
            "module_functions": module_functions
        }

    def extract_js_rules(self):
        if not os.path.exists(self.js_path):
            return {"form_bindings": [], "js_messages": []}
            
        with open(self.js_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        rules = []
        # Find frappe.ui.form.on bindings
        # e.g., frappe.ui.form.on('Sales Order', { ... })
        form_on_matches = re.findall(r"frappe\.ui\.form\.on\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*({[\s\S]+?})\s*\)", content)
        for doc_name, body in form_on_matches:
            # Try to find field triggers inside the JS object body
            # Simple heuristic: "field_name: function(frm) { ... }" or "field_name(frm) { ... }"
            triggers = re.findall(r"([a-zA-Z0-9_]+)\s*:\s*function\s*\([^\)]*\)\s*\{", body)
            triggers_modern = re.findall(r"([a-zA-Z0-9_]+)\s*\([^\)]*\)\s*\{", body)
            all_triggers = sorted(list(set(triggers + triggers_modern)))
            # Exclude common hooks and JS keywords from specific field triggers
            field_triggers = [t for t in all_triggers if t not in COMMON_LIFECYCLE_HOOKS and t not in JS_KEYWORDS]
            doc_hooks = [t for t in all_triggers if t in COMMON_LIFECYCLE_HOOKS]
            
            rules.append({
                "target": doc_name,
                "hooks": doc_hooks,
                "field_triggers": field_triggers
            })
            
        # Also look for msgprint or throw in JS (both translated and non-translated)
        js_throws_tr = re.findall(r"frappe\.(throw|msgprint)\s*\(\s*__\s*\(\s*['\"]([^'\"]+)['\"]", content)
        js_throws_raw = re.findall(r"frappe\.(throw|msgprint)\s*\(\s*['\"]([^'\"]+)['\"]", content)
        
        js_messages = []
        for t, msg in js_throws_tr:
            js_messages.append(f"{t.capitalize()}: {msg}")
        for t, msg in js_throws_raw:
            msg_str = f"{t.capitalize()}: {msg}"
            if msg_str not in js_messages:
                js_messages.append(msg_str)
        
        return {
            "form_bindings": rules,
            "js_messages": js_messages
        }

    def generate_report(self):
        meta = self.extract_metadata()
        py = self.extract_python_rules()
        js = self.extract_js_rules()
        
        report = []
        report.append(f"## {self.doctype} 业务规则矩阵 (Business Rules Matrix)")
        report.append("")
        
        # Identify the primary main class for this DocType
        main_class = None
        target_classname = self.doctype.replace(" ", "")
        for cls in py.get("classes", []):
            if cls["name"] == target_classname:
                main_class = cls
                break
        if not main_class and py.get("classes"):
            # fallback to the largest class or the last one in the file
            main_class = py["classes"][-1]
            
        # 1. 基础属性与控制规则
        report.append("### 1. 基础属性与控制规则")
        report.append(f"*   **模块**: {meta.get('module', 'Unknown')}")
        report.append(f"*   **命名规则 (Naming)**: `{meta.get('naming', '自动递增 ID')}`")
        report.append(f"*   **是否可提交 (Is Submittable)**: {'是 (Yes)' if meta.get('is_submittable') else '否 (No)'}")
        
        # Base Controller
        base_ctrl = "Document"
        if main_class:
            bases = main_class.get("bases", [])
            if bases:
                base_ctrl = ", ".join(bases)
        report.append(f"*   **继承基类 (Base Controller)**: `{base_ctrl}`")
        report.append("")
        
        # Mandatory & Read Only
        report.append("#### 字段约束条件:")
        if meta.get("mandatory"):
            report.append("*   **必填字段 (Mandatory)**:")
            for item in meta["mandatory"]:
                report.append(f"    *   {item}")
        else:
            report.append("*   **必填字段**: 无特定")
            
        if meta.get("read_only"):
            report.append("*   **只读字段 (Read Only)**:")
            for item in meta["read_only"]:
                report.append(f"    *   {item}")
                
        if meta.get("fetch_from"):
            report.append("*   **自动带入规则 (Fetch From)**:")
            for item in meta["fetch_from"]:
                report.append(f"    *   {item}")
                
        if meta.get("depends_on"):
            report.append("*   **动态可见性与条件控制 (Depends On)**:")
            for item in meta["depends_on"]:
                report.append(f"    *   {item}")
        report.append("")
        
        # 2. 前置校验与约束条件 (Validation Rules)
        report.append("### 2. 前置校验与约束条件 (Validation Rules)")
        
        # Look for validate or helper validation methods
        found_validation = False
        if main_class:
            methods = main_class.get("methods", {})
            
            # Print validate method flow
            if "validate" in methods:
                found_validation = True
                validate_info = methods["validate"]
                report.append("#### `validate` 生命钩子执行校验流:")
                if validate_info.get("helpers"):
                    report.append("在该钩子中依次调用了以下内部校验/处理函数:")
                    for helper in validate_info["helpers"]:
                        report.append(f"1.  `self.{helper}()`")
                else:
                    report.append("执行直接内联校验。")
                
                # Check for throws in validate itself
                if validate_info.get("throws"):
                    report.append("直属抛错校验:")
                    for call_type, msg in validate_info["throws"]:
                        report.append(f"    *   **[{call_type}]**: {msg}")
                report.append("")
                
            # Scan all other methods for throws and business checks
            has_other_checks = False
            for mname, minfo in methods.items():
                if mname == "validate":
                    continue
                if mname.startswith("validate_") or mname.startswith("check_") or minfo.get("throws"):
                    if not has_other_checks:
                        report.append("#### 核心控制校验函数与报错信息:")
                        has_other_checks = True
                    doc = ""
                    if minfo.get("docstring"):
                        lines = minfo["docstring"].strip().splitlines()
                        if lines:
                            doc = f" ({lines[0]})"
                    report.append(f"*   `{mname}`{doc}:")
                    if minfo.get("throws"):
                        for call_type, msg in minfo["throws"]:
                            report.append(f"    *   **[{call_type}]**: {msg}")
                    else:
                        report.append("    *   执行特定条件判定 (无硬性抛错/动态抛错)")
            
            if has_other_checks:
                report.append("")
                
        if not found_validation:
            report.append("未在 Python 控制器中找到显式的 `validate` 校验。")
            report.append("")
            
        # 3. 后置联动与过账逻辑 (Execution Rules)
        report.append("### 3. 后置联动与过账逻辑 (Execution / Submission Rules)")
        if main_class:
            methods = main_class.get("methods", {})
            
            # before_insert / before_save
            for hook in ["before_insert", "before_save", "before_submit"]:
                if hook in methods:
                    report.append(f"#### `{hook}` (保存/插入前前置计算):")
                    minfo = methods[hook]
                    if minfo.get("docstring"):
                        report.append(f"    *   {minfo['docstring'].strip()}")
                    if minfo.get("helpers"):
                        for h in minfo["helpers"]:
                            report.append(f"    *   调用 `self.{h}()`")
                    if minfo.get("throws"):
                        for call_type, msg in minfo["throws"]:
                            report.append(f"    *   **[{call_type}]**: {msg}")
                            
            # on_submit
            if "on_submit" in methods:
                report.append("#### `on_submit` (提交与过账核心规则):")
                submit_info = methods["on_submit"]
                if submit_info.get("docstring"):
                    report.append(f"    *   **说明**: {submit_info['docstring'].strip()}")
                if submit_info.get("helpers"):
                    report.append("    *   **触发的下游逻辑 / 更新动作**:")
                    for helper in submit_info["helpers"]:
                        report.append(f"        *   `self.{helper}()`")
                if submit_info.get("throws"):
                    report.append("    *   **提交限制条件**:")
                    for call_type, msg in submit_info["throws"]:
                        report.append(f"        *   **[{call_type}]**: {msg}")
            else:
                report.append("该单据无特定的 `on_submit` 提交过账逻辑。")
            report.append("")
            
        # 4. 逆向/作废控制规则 (Cancellation Rules)
        report.append("### 4. 逆向/作废控制规则 (Cancellation Rules)")
        if main_class:
            methods = main_class.get("methods", {})
            if "on_cancel" in methods:
                cancel_info = methods["on_cancel"]
                if cancel_info.get("docstring"):
                    report.append(f"*   **说明**: {cancel_info['docstring'].strip()}")
                if cancel_info.get("helpers"):
                    report.append("*   **逆向联动回滚函数**:")
                    for helper in cancel_info["helpers"]:
                        report.append(f"    *   `self.{helper}()`")
                if cancel_info.get("throws"):
                    report.append("*   **作废限制条件 (不能作废的情况)**:")
                    for call_type, msg in cancel_info["throws"]:
                        report.append(f"    *   **[{call_type}]**: {msg}")
            else:
                report.append("该单据无特定的 `on_cancel` 作废/回滚逻辑。")
            report.append("")
            
        # 5. 前端交互与客户端规则 (Client-Side Interactivity)
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
            for msg in js["js_messages"][:15]:  # Limit to first 15 for readability
                report.append(f"    *   {msg}")
        report.append("")
        report.append("---")
        report.append("")
        return "\n".join(report)

def main():
    full_report = [
        "# ERPNext 核心业务对象业务规则整理报告",
        "本报告通过自动化脚本静态解析 ERPNext (元数据 JSON、Python 控制器 AST、Javascript 脚本) 提取核心业务对象的业务规则，并按「基础属性与控制规则」、「前置校验与约束条件」、「后置联动与过账逻辑」、「逆向/作废控制规则」、「前端交互与客户端规则」五个维度整理成**业务规则矩阵 (Business Rules Matrix)**。",
        "",
        "---",
        ""
    ]
    
    for doctype, path in DOCTYPES.items():
        if os.path.exists(path):
            print(f"Extracting rules for {doctype}...")
            extractor = RuleExtractor(doctype, path)
            full_report.append(extractor.generate_report())
        else:
            print(f"Skipping {doctype}, path not found: {path}")
            
    # Allow configuring output path via CLI arg
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    else:
        output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "business_rules_matrix.md")
        
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(full_report))
        
    print(f"Report successfully generated at: {output_file}")

if __name__ == "__main__":
    main()
