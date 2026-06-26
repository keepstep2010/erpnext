# ERPNext 核心业务对象业务规则整理报告
本报告通过自动化脚本静态解析 ERPNext (元数据 JSON、Python 控制器 AST、Javascript 脚本) 提取核心业务对象的业务规则，并按「基础属性与控制规则」、「前置校验与约束条件」、「后置联动与过账逻辑」、「逆向/作废控制规则」、「前端交互与客户端规则」五个维度整理成**业务规则矩阵 (Business Rules Matrix)**。

---

## Customer 业务规则矩阵 (Business Rules Matrix)

### 1. 基础属性与控制规则
*   **模块**: Selling
*   **命名规则 (Naming)**: `naming_series:`
*   **是否可提交 (Is Submittable)**: 否 (No)
*   **继承基类 (Base Controller)**: `TransactionBase`

#### 字段约束条件:
*   **必填字段 (Mandatory)**:
    *   `customer_name` (Customer Name) [Data]
    *   `customer_type` (Customer Type) [Select]
    *   `customer_group` (Customer Group) [Link]
    *   `territory` (Territory) [Link]
*   **只读字段 (Read Only)**:
    *   `address_html` (Address HTML)
    *   `contact_html` (Contact HTML)
    *   `primary_address` (Primary Address)
    *   `loyalty_program_tier` (Loyalty Program Tier)
    *   `customer_pos_id` (Customer POS id)
*   **自动带入规则 (Fetch From)**:
    *   `mobile_no` (Mobile No) <- `customer_primary_contact.mobile_no`
    *   `email_id` (Email Id) <- `customer_primary_contact.email_id`
*   **动态可见性与条件控制 (Depends On)**:
    *   `salutation` (Salutation) depends on: `eval:doc.customer_type!='Company'`
    *   `gender` (Gender) depends on: `eval:doc.customer_type != 'Company'`
    *   `represents_company` (Represents Company) depends on: `is_internal_customer`
    *   `companies` (Allowed To Transact With) depends on: `represents_company`
    *   `address_contacts` (Address and Contact) depends on: `eval:!doc.__islocal`
    *   `address_html` (Address HTML) depends on: `eval: !doc.__islocal`
    *   `contact_html` (Contact HTML) depends on: `eval: !doc.__islocal`

### 2. 前置校验与约束条件 (Validation Rules)
#### `validate` 生命钩子执行校验流:
在该钩子中依次调用了以下内部校验/处理函数:
1.  `self.validate_credit_limit_on_change()`
1.  `self.set_loyalty_program()`
1.  `self.validate_default_bank_account()`
1.  `self.validate_internal_customer()`
直属抛错校验:
    *   **[Throw]**: Total contribution percentage should be equal to 100

#### 核心控制校验函数与报错信息:
*   `get_customer_name`:
    *   **[Msgprint]**: Dynamic message
*   `check_customer_group_change`:
    *   执行特定条件判定 (无硬性抛错/动态抛错)
*   `validate_default_bank_account`:
    *   **[Throw]**: Dynamic message
*   `validate_internal_customer`:
    *   **[Throw]**: Dynamic message
*   `validate_name_with_customer_group`:
    *   **[Throw]**: A Customer Group exists with same name please change the Customer name or rename the Customer Group
*   `validate_credit_limit_on_change`:
    *   **[Throw]**: Dynamic message
    *   **[Throw]**: Dynamic message
*   `set_loyalty_program`:
    *   **[Msgprint]**: Dynamic message

### 3. 后置联动与过账逻辑 (Execution / Submission Rules)
该单据无特定的 `on_submit` 提交过账逻辑。

### 4. 逆向/作废控制规则 (Cancellation Rules)
该单据无特定的 `on_cancel` 作废/回滚逻辑。

### 5. 前端交互与客户端规则 (Client-Side Interactivity)
#### 页面绑定: `Customer`
*   **生命周期触发器**: `setup`

---

## Sales Order 业务规则矩阵 (Business Rules Matrix)

### 1. 基础属性与控制规则
*   **模块**: Selling
*   **命名规则 (Naming)**: `naming_series:`
*   **是否可提交 (Is Submittable)**: 是 (Yes)
*   **继承基类 (Base Controller)**: `SellingController`

#### 字段约束条件:
*   **必填字段 (Mandatory)**:
    *   `naming_series` (Series) [Select]
    *   `customer` (Customer) [Link]
    *   `order_type` (Order Type) [Select]
    *   `company` (Company) [Link]
    *   `transaction_date` (Date) [Date]
    *   `currency` (Currency) [Link]
    *   `conversion_rate` (Exchange Rate) [Float]
    *   `selling_price_list` (Price List) [Link]
    *   `price_list_currency` (Price List Currency) [Link]
    *   `plc_conversion_rate` (Price List Exchange Rate) [Float]
    *   `items` (Items) [Table]
    *   `status` (Status) [Select]
*   **只读字段 (Read Only)**:
    *   `customer_name` (Customer Name)
    *   `amended_from` (Amended From)
    *   `tax_id` (Tax Id)
    *   `address_display` (Address)
    *   `contact_display` (Contact)
    *   `contact_mobile` (Mobile No)
    *   `contact_email` (Contact Email)
    *   `company_address_display` (Company Address)
    *   `shipping_address` (Shipping Address)
    *   `price_list_currency` (Price List Currency)
    *   `pricing_rules` (Pricing Rule Detail)
    *   `total_qty` (Total Quantity)
    *   `base_total` (Total (Company Currency))
    *   `base_net_total` (Net Total (Company Currency))
    *   `total` (Total)
    *   `net_total` (Net Total)
    *   `total_net_weight` (Total Net Weight)
    *   `other_charges_calculation` (Taxes and Charges Calculation)
    *   `base_total_taxes_and_charges` (Total Taxes and Charges (Company Currency))
    *   `total_taxes_and_charges` (Total Taxes and Charges)
    *   `loyalty_points` (Loyalty Points)
    *   `loyalty_amount` (Loyalty Amount)
    *   `base_discount_amount` (Additional Discount Amount (Company Currency))
    *   `base_grand_total` (Grand Total (Company Currency))
    *   `base_rounding_adjustment` (Rounding Adjustment (Company Currency))
    *   `base_rounded_total` (Rounded Total (Company Currency))
    *   `base_in_words` (In Words (Company Currency))
    *   `grand_total` (Grand Total)
    *   `rounding_adjustment` (Rounding Adjustment)
    *   `rounded_total` (Rounded Total)
    *   `in_words` (In Words)
    *   `advance_paid` (Advance Paid)
    *   `inter_company_order_reference` (Inter Company Order Reference)
    *   `party_account_currency` (Party Account Currency)
    *   `language` (Print Language)
    *   `status` (Status)
    *   `per_delivered` (%  Delivered)
    *   `per_billed` (% Amount Billed)
    *   `subscription_section` (Auto Repeat)
    *   `contact_phone` (Phone)
    *   `is_internal_customer` (Is Internal Customer)
    *   `represents_company` (Represents Company)
    *   `dispatch_address` (Dispatch Address)
    *   `amount_eligible_for_commission` (Amount Eligible for Commission)
    *   `per_picked` (% Picked)
*   **自动带入规则 (Fetch From)**:
    *   `customer_name` (Customer Name) <- `customer.customer_name`
    *   `tax_id` (Tax Id) <- `customer.tax_id`
    *   `commission_rate` (Commission Rate) <- `sales_partner.commission_rate`
    *   `is_internal_customer` (Is Internal Customer) <- `customer.is_internal_customer`
    *   `represents_company` (Represents Company) <- `customer.represents_company`
*   **动态可见性与条件控制 (Depends On)**:
    *   `delivery_date` (Delivery Date) depends on: `eval:!doc.skip_delivery_note`
    *   `po_date` (Customer's Purchase Order Date) depends on: `eval:doc.po_no`
    *   `contact_info` (Address & Contact) depends on: `customer`
    *   `total_net_weight` (Total Net Weight) depends on: `total_net_weight`
    *   `base_rounding_adjustment` (Rounding Adjustment (Company Currency)) depends on: `eval:!doc.disable_rounded_total`
    *   `base_rounded_total` (Rounded Total (Company Currency)) depends on: `eval:!doc.disable_rounded_total`
    *   `rounding_adjustment` (Rounding Adjustment) depends on: `eval:!doc.disable_rounded_total`
    *   `rounded_total` (Rounded Total) depends on: `eval:!doc.disable_rounded_total`
    *   `packing_list` (Packing List) depends on: `packed_items`
    *   `packed_items` (Packed Items) depends on: `packed_items`
    *   `per_delivered` (%  Delivered) depends on: `eval:!doc.__islocal && !doc.skip_delivery_note_creation`
    *   `per_billed` (% Amount Billed) depends on: `eval:!doc.__islocal`
    *   `update_auto_repeat_reference` (Update Auto Repeat Reference) depends on: `eval: doc.auto_repeat`
    *   `disable_rounded_total` (Disable Rounded Total) depends on: `grand_total`
    *   `dispatch_address` (Dispatch Address) depends on: `dispatch_address_name`

### 2. 前置校验与约束条件 (Validation Rules)
#### `validate` 生命钩子执行校验流:
在该钩子中依次调用了以下内部校验/处理函数:
1.  `self.validate_delivery_date()`
1.  `self.validate_proj_cust()`
1.  `self.validate_po()`
1.  `self.validate_uom_is_integer()`
1.  `self.validate_uom_is_integer()`
1.  `self.validate_for_items()`
1.  `self.validate_warehouse()`
1.  `self.validate_drop_ship()`
1.  `self.validate_serial_no_based_delivery()`
1.  `self.validate_with_previous_doc()`
1.  `self.set_status()`

#### 核心控制校验函数与报错信息:
*   `validate_po`:
    *   **[Msgprint]**: Dynamic message
    *   **[Throw]**: Dynamic message
*   `validate_for_items`:
    *   执行特定条件判定 (无硬性抛错/动态抛错)
*   `validate_sales_mntc_quotation`:
    *   **[Msgprint]**: Dynamic message
*   `validate_delivery_date`:
    *   **[Throw]**: Please enter Delivery Date
    *   **[Msgprint]**: Expected Delivery Date should be after Sales Order Date
*   `validate_proj_cust`:
    *   **[Throw]**: Dynamic message
*   `validate_warehouse`:
    *   **[Throw]**: Dynamic message
*   `validate_with_previous_doc`:
    *   执行特定条件判定 (无硬性抛错/动态抛错)
*   `update_prevdoc_status`:
    *   **[Throw]**: Dynamic message
*   `validate_drop_ship`:
    *   **[Throw]**: Dynamic message
*   `on_cancel`:
    *   **[Throw]**: Closed order cannot be cancelled. Unclose to cancel.
*   `check_credit_limit`:
    *   执行特定条件判定 (无硬性抛错/动态抛错)
*   `check_nextdoc_docstatus`:
    *   **[Throw]**: Dynamic message
*   `check_modified_date`:
    *   **[Throw]**: Dynamic message
*   `validate_supplier_after_submit` (Check that supplier is the same after submit if PO is already made):
    *   **[Throw]**: Dynamic message
*   `validate_serial_no_based_delivery`:
    *   **[Throw]**: Dynamic message
    *   **[Throw]**: Dynamic message
    *   **[Throw]**: Dynamic message
    *   **[Throw]**: Dynamic message

### 3. 后置联动与过账逻辑 (Execution / Submission Rules)
#### `on_submit` (提交与过账核心规则):

### 4. 逆向/作废控制规则 (Cancellation Rules)
*   **作废限制条件 (不能作废的情况)**:
    *   **[Throw]**: Closed order cannot be cancelled. Unclose to cancel.

### 5. 前端交互与客户端规则 (Client-Side Interactivity)
#### 页面绑定: `Sales Order`
*   **生命周期触发器**: `setup`
*   **字段值变更触发事件 (Field Listeners)**:
    *   `set_indicator_formatter` 字段改变时触发前端计算或联动
#### 页面绑定: `Sales Order Item`
*   **字段值变更触发事件 (Field Listeners)**:
    *   `delivery_date` 字段改变时触发前端计算或联动
    *   `item_code` 字段改变时触发前端计算或联动
*   **前端弹窗或校验提示 (UI Warnings)**:
    *   Throw: Please set Company
    *   Msgprint: Material Request {0} submitted.

---

## Delivery Note 业务规则矩阵 (Business Rules Matrix)

### 1. 基础属性与控制规则
*   **模块**: Stock
*   **命名规则 (Naming)**: `naming_series:`
*   **是否可提交 (Is Submittable)**: 是 (Yes)
*   **继承基类 (Base Controller)**: `SellingController`

#### 字段约束条件:
*   **必填字段 (Mandatory)**:
    *   `naming_series` (Series) [Select]
    *   `customer` (Customer) [Link]
    *   `company` (Company) [Link]
    *   `posting_date` (Date) [Date]
    *   `posting_time` (Posting Time) [Time]
    *   `currency` (Currency) [Link]
    *   `conversion_rate` (Exchange Rate) [Float]
    *   `selling_price_list` (Price List) [Link]
    *   `price_list_currency` (Price List Currency) [Link]
    *   `plc_conversion_rate` (Price List Exchange Rate) [Float]
    *   `items` (items) [Table]
    *   `status` (Status) [Select]
*   **只读字段 (Read Only)**:
    *   `customer_name` (Customer Name)
    *   `amended_from` (Amended From)
    *   `is_return` (Is Return)
    *   `return_against` (Return Against Delivery Note)
    *   `shipping_address` (Shipping Address)
    *   `contact_display` (Contact)
    *   `contact_mobile` (Mobile No)
    *   `contact_email` (Contact Email)
    *   `tax_id` (Tax Id)
    *   `address_display` (Billing Address)
    *   `company_address_display` (Company Address)
    *   `price_list_currency` (Price List Currency)
    *   `pricing_rules` (Pricing Rule Detail)
    *   `total_qty` (Total Quantity)
    *   `base_total` (Total (Company Currency))
    *   `base_net_total` (Net Total (Company Currency))
    *   `total` (Total)
    *   `net_total` (Net Total)
    *   `total_net_weight` (Total Net Weight)
    *   `other_charges_calculation` (Taxes and Charges Calculation)
    *   `base_total_taxes_and_charges` (Total Taxes and Charges (Company Currency))
    *   `total_taxes_and_charges` (Total Taxes and Charges)
    *   `base_discount_amount` (Additional Discount Amount (Company Currency))
    *   `base_grand_total` (Grand Total (Company Currency))
    *   `base_rounding_adjustment` (Rounding Adjustment (Company Currency))
    *   `base_rounded_total` (Rounded Total (Company Currency))
    *   `base_in_words` (In Words (Company Currency))
    *   `grand_total` (Grand Total)
    *   `rounding_adjustment` (Rounding Adjustment)
    *   `rounded_total` (Rounded Total)
    *   `in_words` (In Words)
    *   `transporter_name` (Transporter Name)
    *   `per_billed` (% Amount Billed)
    *   `language` (Print Language)
    *   `status` (Status)
    *   `per_installed` (% Installed)
    *   `auto_repeat` (Auto Repeat)
    *   `pick_list` (Pick List)
    *   `is_internal_customer` (Is Internal Customer)
    *   `per_returned` (% Returned)
    *   `represents_company` (Represents Company)
    *   `dispatch_address` (Dispatch Address)
    *   `amount_eligible_for_commission` (Amount Eligible for Commission)
*   **自动带入规则 (Fetch From)**:
    *   `customer_name` (Customer Name) <- `customer.customer_name`
    *   `transporter_name` (Transporter Name) <- `transporter.name`
    *   `driver_name` (Driver Name) <- `driver.full_name`
    *   `commission_rate` (Commission Rate (%)) <- `sales_partner.commission_rate`
    *   `is_internal_customer` (Is Internal Customer) <- `customer.is_internal_customer`
    *   `represents_company` (Represents Company) <- `customer.represents_company`
*   **动态可见性与条件控制 (Depends On)**:
    *   `customer_name` (Customer Name) depends on: `customer`
    *   `set_posting_time` (Edit Posting Date and Time) depends on: `eval:doc.docstatus==0`
    *   `issue_credit_note` (Issue Credit Note) depends on: `is_return`
    *   `return_against` (Return Against Delivery Note) depends on: `is_return`
    *   `contact_info` (Billing Address) depends on: `customer`
    *   `customer_address` (Billing Address Name) depends on: `customer`
    *   `packing_list` (Packing List) depends on: `packed_items`
    *   `packed_items` (Packed Items) depends on: `packed_items`
    *   `total_net_weight` (Total Net Weight) depends on: `total_net_weight`
    *   `base_rounding_adjustment` (Rounding Adjustment (Company Currency)) depends on: `eval:!doc.disable_rounded_total`
    *   `base_rounded_total` (Rounded Total (Company Currency)) depends on: `eval:!doc.disable_rounded_total`
    *   `rounding_adjustment` (Rounding Adjustment) depends on: `eval:!doc.disable_rounded_total`
    *   `rounded_total` (Rounded Total) depends on: `eval:!doc.disable_rounded_total`
    *   `per_installed` (% Installed) depends on: `eval:!doc.__islocal`
    *   `per_returned` (% Returned) depends on: `eval:!doc.__islocal`
    *   `set_target_warehouse` (Set Target Warehouse) depends on: `eval: doc.is_internal_customer`
    *   `disable_rounded_total` (Disable Rounded Total) depends on: `grand_total`
    *   `dispatch_address` (Dispatch Address) depends on: `dispatch_address_name`

### 2. 前置校验与约束条件 (Validation Rules)
#### `validate` 生命钩子执行校验流:
在该钩子中依次调用了以下内部校验/处理函数:
1.  `self.validate_posting_time()`
1.  `self.set_status()`
1.  `self.validate_proj_cust()`
1.  `self.validate_warehouse()`
1.  `self.validate_uom_is_integer()`
1.  `self.validate_uom_is_integer()`
1.  `self.validate_with_previous_doc()`

#### 核心控制校验函数与报错信息:
*   `so_required` (check in manage account if sales order required or not):
    *   **[Throw]**: Dynamic message
*   `validate_with_previous_doc`:
    *   执行特定条件判定 (无硬性抛错/动态抛错)
*   `validate_proj_cust` (check for does customer belong to same project as entered..):
    *   **[Throw]**: Dynamic message
*   `validate_warehouse`:
    *   **[Throw]**: Dynamic message
*   `check_credit_limit`:
    *   执行特定条件判定 (无硬性抛错/动态抛错)
*   `validate_packed_qty` (Validate that if packed qty exists, it should be equal to qty):
    *   **[Msgprint]**: Dynamic message
*   `check_next_docstatus`:
    *   **[Throw]**: Dynamic message
    *   **[Throw]**: Dynamic message
*   `cancel_packing_slips` (Cancel submitted packing slips related to this delivery note):
    *   **[Msgprint]**: Packing Slip(s) cancelled
*   `make_return_invoice`:
    *   **[Msgprint]**: Dynamic message
    *   **[Throw]**: Could not create Credit Note automatically, please uncheck 'Issue Credit Note' and submit again

### 3. 后置联动与过账逻辑 (Execution / Submission Rules)
#### `on_submit` (提交与过账核心规则):
    *   **触发的下游逻辑 / 更新动作**:
        *   `self.validate_packed_qty()`

### 4. 逆向/作废控制规则 (Cancellation Rules)

### 5. 前端交互与客户端规则 (Client-Side Interactivity)
#### 页面绑定: `Delivery Note`
*   **生命周期触发器**: `setup`
*   **字段值变更触发事件 (Field Listeners)**:
    *   `set_indicator_formatter` 字段改变时触发前端计算或联动
#### 页面绑定: `Delivery Note Item`
*   **字段值变更触发事件 (Field Listeners)**:
    *   `cost_center` 字段改变时触发前端计算或联动
    *   `expense_account` 字段改变时触发前端计算或联动
#### 页面绑定: `Delivery Note`
*   **生命周期触发器**: `setup`
*   **字段值变更触发事件 (Field Listeners)**:
    *   `company` 字段改变时触发前端计算或联动
    *   `unhide_account_head` 字段改变时触发前端计算或联动

---

## Sales Invoice 业务规则矩阵 (Business Rules Matrix)

### 1. 基础属性与控制规则
*   **模块**: Accounts
*   **命名规则 (Naming)**: `naming_series:`
*   **是否可提交 (Is Submittable)**: 是 (Yes)
*   **继承基类 (Base Controller)**: `SellingController`

#### 字段约束条件:
*   **必填字段 (Mandatory)**:
    *   `naming_series` (Series) [Select]
    *   `company` (Company) [Link]
    *   `posting_date` (Date) [Date]
    *   `currency` (Currency) [Link]
    *   `conversion_rate` (Exchange Rate) [Float]
    *   `selling_price_list` (Price List) [Link]
    *   `price_list_currency` (Price List Currency) [Link]
    *   `plc_conversion_rate` (Price List Exchange Rate) [Float]
    *   `items` (items) [Table]
    *   `base_net_total` (Net Total (Company Currency)) [Currency]
    *   `base_grand_total` (Grand Total (Company Currency)) [Currency]
    *   `grand_total` (Grand Total) [Currency]
    *   `debit_to` (Debit To) [Link]
*   **只读字段 (Read Only)**:
    *   `customer_name` (Customer Name)
    *   `tax_id` (Tax Id)
    *   `amended_from` (Amended From)
    *   `address_display` (Address)
    *   `contact_display` (Contact)
    *   `contact_mobile` (Mobile No)
    *   `contact_email` (Contact Email)
    *   `shipping_address` (Shipping Address)
    *   `company_address_display` (Company Address)
    *   `price_list_currency` (Price List Currency)
    *   `pricing_rules` (Pricing Rule Detail)
    *   `total_billing_amount` (Total Billing Amount)
    *   `total_qty` (Total Quantity)
    *   `base_total` (Total (Company Currency))
    *   `base_net_total` (Net Total (Company Currency))
    *   `total` (Total)
    *   `net_total` (Net Total)
    *   `total_net_weight` (Total Net Weight)
    *   `other_charges_calculation` (Taxes and Charges Calculation)
    *   `base_total_taxes_and_charges` (Total Taxes and Charges (Company Currency))
    *   `total_taxes_and_charges` (Total Taxes and Charges)
    *   `loyalty_amount` (Loyalty Amount)
    *   `loyalty_program` (Loyalty Program)
    *   `base_discount_amount` (Additional Discount Amount (Company Currency))
    *   `base_grand_total` (Grand Total (Company Currency))
    *   `base_rounding_adjustment` (Rounding Adjustment (Company Currency))
    *   `base_rounded_total` (Rounded Total (Company Currency))
    *   `base_in_words` (In Words (Company Currency))
    *   `grand_total` (Grand Total)
    *   `rounding_adjustment` (Rounding Adjustment)
    *   `rounded_total` (Rounded Total)
    *   `in_words` (In Words)
    *   `total_advance` (Total Advance)
    *   `outstanding_amount` (Outstanding Amount)
    *   `base_paid_amount` (Paid Amount (Company Currency))
    *   `paid_amount` (Paid Amount)
    *   `base_change_amount` (Base Change Amount (Company Currency))
    *   `base_write_off_amount` (Write Off Amount (Company Currency))
    *   `language` (Print Language)
    *   `inter_company_invoice_reference` (Inter Company Invoice Reference)
    *   `is_discounted` (Is Discounted)
    *   `status` (Status)
    *   `party_account_currency` (Party Account Currency)
    *   `auto_repeat` (Auto Repeat)
    *   `is_consolidated` (Is Consolidated)
    *   `is_internal_customer` (Is Internal Customer)
    *   `company_tax_id` (Company Tax ID)
    *   `represents_company` (Represents Company)
    *   `dispatch_address` (Dispatch Address)
    *   `ignore_default_payment_terms_template` (Ignore Default Payment Terms Template)
    *   `total_billing_hours` (Total Billing Hours)
    *   `amount_eligible_for_commission` (Amount Eligible for Commission)
    *   `repost_required` (Repost Required)
*   **自动带入规则 (Fetch From)**:
    *   `customer_name` (Customer Name) <- `customer.customer_name`
    *   `loyalty_program` (Loyalty Program) <- `customer.loyalty_program`
    *   `is_internal_customer` (Is Internal Customer) <- `customer.is_internal_customer`
    *   `company_tax_id` (Company Tax ID) <- `company.tax_id`
    *   `represents_company` (Represents Company) <- `customer.represents_company`
*   **动态可见性与条件控制 (Depends On)**:
    *   `customer_name` (Customer Name) depends on: `customer`
    *   `pos_profile` (POS Profile) depends on: `is_pos`
    *   `set_posting_time` (Edit Posting Date and Time) depends on: `eval:doc.docstatus==0`
    *   `return_against` (Return Against) depends on: `eval:doc.return_against || doc.is_debit_note`
    *   `update_billed_amount_in_sales_order` (Update Billed Amount in Sales Order) depends on: `eval: doc.is_return`
    *   `currency_and_price_list` (Currency and Price List) depends on: `customer`
    *   `set_warehouse` (Source Warehouse) depends on: `update_stock`
    *   `packing_list` (Packing List) depends on: `packed_items`
    *   `packed_items` (Packed Items) depends on: `packed_items`
    *   `time_sheet_list` (Time Sheet List) depends on: `eval:!doc.is_return`
    *   `total_net_weight` (Total Net Weight) depends on: `total_net_weight`
    *   `loyalty_points` (Loyalty Points) depends on: `redeem_loyalty_points`
    *   `loyalty_amount` (Loyalty Amount) depends on: `redeem_loyalty_points`
    *   `loyalty_redemption_account` (Redemption Account) depends on: `redeem_loyalty_points`
    *   `loyalty_redemption_cost_center` (Redemption Cost Center) depends on: `redeem_loyalty_points`
    *   `base_rounding_adjustment` (Rounding Adjustment (Company Currency)) depends on: `eval:!doc.disable_rounded_total`
    *   `base_rounded_total` (Rounded Total (Company Currency)) depends on: `eval:!doc.disable_rounded_total`
    *   `rounding_adjustment` (Rounding Adjustment) depends on: `eval:!doc.disable_rounded_total`
    *   `rounded_total` (Rounded Total) depends on: `eval:!doc.disable_rounded_total`
    *   `get_advances` (Get Advances Received) depends on: `eval:!doc.allocate_advances_automatically`
    *   `payment_terms_template` (Payment Terms Template) depends on: `eval:(!doc.is_pos && !doc.is_return)`
    *   `payment_schedule` (Payment Schedule) depends on: `eval:(!doc.is_pos && !doc.is_return)`
    *   `payments_section` (Payments) depends on: `eval:doc.is_pos===1`
    *   `cash_bank_account` (Cash/Bank Account) depends on: `is_pos`
    *   `payments` (Sales Invoice Payment) depends on: `eval:doc.is_pos===1`
    *   `base_paid_amount` (Paid Amount (Company Currency)) depends on: `eval: doc.is_pos || doc.redeem_loyalty_points`
    *   `paid_amount` (Paid Amount) depends on: `eval: doc.is_pos || doc.redeem_loyalty_points`
    *   `section_break_88` (Changes) depends on: `is_pos`
    *   `base_change_amount` (Base Change Amount (Company Currency)) depends on: `is_pos`
    *   `change_amount` (Change Amount) depends on: `is_pos`
    *   `account_for_change_amount` (Account for Change Amount) depends on: `is_pos`
    *   `write_off_outstanding_amount_automatically` (Write Off Outstanding Amount) depends on: `is_pos`
    *   `more_information` (Additional Info) depends on: `customer`
    *   `update_auto_repeat_reference` (Update Auto Repeat Reference) depends on: `eval: doc.auto_repeat`
    *   `is_consolidated` (Is Consolidated) depends on: `eval:(doc.is_pos && doc.is_consolidated)`
    *   `unrealized_profit_loss_account` (Unrealized Profit / Loss Account) depends on: `eval:doc.is_internal_customer`
    *   `represents_company` (Represents Company) depends on: `eval:doc.is_internal_customer`
    *   `set_target_warehouse` (Set Target Warehouse) depends on: `eval: doc.is_internal_customer && doc.update_stock`
    *   `disable_rounded_total` (Disable Rounded Total) depends on: `grand_total`
    *   `is_cash_or_non_trade_discount` (Is Cash or Non Trade Discount) depends on: `eval: doc.apply_discount_on == "Grand Total"`
    *   `section_break_104` (section_break_104) depends on: `eval:(!doc.is_return && doc.total_billing_amount > 0)`
    *   `write_off_section` (Write Off) depends on: `is_pos`

### 2. 前置校验与约束条件 (Validation Rules)
#### `validate` 生命钩子执行校验流:
在该钩子中依次调用了以下内部校验/处理函数:
1.  `self.validate_auto_set_posting_time()`
1.  `self.set_tax_withholding()`
1.  `self.validate_proj_cust()`
1.  `self.validate_pos_return()`
1.  `self.validate_with_previous_doc()`
1.  `self.validate_uom_is_integer()`
1.  `self.validate_uom_is_integer()`
1.  `self.validate_debit_to_acc()`
1.  `self.validate_fixed_asset()`
1.  `self.set_income_account_for_fixed_assets()`
1.  `self.validate_item_cost_centers()`
1.  `self.validate_accounts()`
1.  `self.set_against_income_account()`
1.  `self.validate_time_sheets_are_submitted()`
1.  `self.validate_multiple_billing()`
1.  `self.set_billing_hours_and_amount()`
1.  `self.set_status()`
1.  `self.validate_pos()`
1.  `self.validate_dropship_item()`
1.  `self.validate_item_code()`
1.  `self.validate_warehouse()`
1.  `self.validate_delivery_note()`
1.  `self.validate_serial_numbers()`

#### 核心控制校验函数与报错信息:
*   `validate_accounts`:
    *   执行特定条件判定 (无硬性抛错/动态抛错)
*   `validate_fixed_asset`:
    *   **[Throw]**: 'Update Stock' cannot be checked for fixed asset sale
    *   **[Throw]**: Dynamic message
*   `validate_item_cost_centers`:
    *   **[Throw]**: Dynamic message
*   `validate_income_account`:
    *   执行特定条件判定 (无硬性抛错/动态抛错)
*   `validate_pos_return`:
    *   **[Throw]**: Dynamic message
*   `validate_pos_paid_amount`:
    *   **[Throw]**: At least one mode of payment is required for POS invoice.
*   `check_if_consolidated_invoice`:
    *   **[Throw]**: Dynamic message
*   `check_credit_limit`:
    *   执行特定条件判定 (无硬性抛错/动态抛错)
*   `on_update_after_submit`:
    *   **[Throw]**: Dynamic message
*   `check_if_child_table_updated`:
    *   执行特定条件判定 (无硬性抛错/动态抛错)
*   `repost_accounting_entries`:
    *   **[Throw]**: No updates pending for reposting
*   `validate_time_sheets_are_submitted`:
    *   **[Throw]**: Dynamic message
*   `validate_debit_to_acc`:
    *   **[Throw]**: Debit To is required
    *   **[Throw]**: Dynamic message
    *   **[Throw]**: Dynamic message
*   `validate_with_previous_doc`:
    *   执行特定条件判定 (无硬性抛错/动态抛错)
*   `validate_auto_set_posting_time`:
    *   执行特定条件判定 (无硬性抛错/动态抛错)
*   `so_dn_required` (check in manage account if sales order / delivery note required or not.):
    *   **[Msgprint]**: Dynamic message
*   `validate_proj_cust` (check for does customer belong to same project as entered..):
    *   **[Throw]**: Dynamic message
*   `validate_pos`:
    *   **[Throw]**: Paid amount + Write Off Amount can not be greater than Grand Total
*   `validate_item_code`:
    *   **[Msgprint]**: Dynamic message
*   `validate_warehouse`:
    *   **[Throw]**: Dynamic message
*   `validate_delivery_note`:
    *   **[Msgprint]**: Dynamic message
*   `validate_write_off_account`:
    *   **[Msgprint]**: Please enter Write Off Account
*   `validate_account_for_change_amount`:
    *   **[Msgprint]**: Please enter Account for Change Amount
*   `validate_dropship_item`:
    *   **[Throw]**: Could not update stock, invoice contains drop shipping item.
*   `get_warehouse`:
    *   **[Msgprint]**: POS Profile required to make POS Entry
*   `check_prev_docstatus`:
    *   **[Throw]**: Dynamic message
    *   **[Throw]**: Dynamic message
*   `get_asset`:
    *   **[Throw]**: Dynamic message
*   `make_gle_for_change_amount`:
    *   **[Throw]**: Select change amount account
*   `validate_serial_numbers` (validate serial number agains Delivery Note and Sales Invoice):
    *   执行特定条件判定 (无硬性抛错/动态抛错)
*   `validate_serial_against_delivery_note` (validate if the serial numbers in Sales Invoice Items are same as in):
    *   **[Throw]**: Dynamic message
    *   **[Throw]**: Dynamic message
*   `verify_payment_amount_is_positive`:
    *   **[Throw]**: Dynamic message
*   `verify_payment_amount_is_negative`:
    *   **[Throw]**: Dynamic message
*   `delete_loyalty_point_entry`:
    *   **[Throw]**: Dynamic message

### 3. 后置联动与过账逻辑 (Execution / Submission Rules)
#### `before_save` (保存/插入前前置计算):
#### `on_submit` (提交与过账核心规则):
    *   **触发的下游逻辑 / 更新动作**:
        *   `self.validate_pos_paid_amount()`

### 4. 逆向/作废控制规则 (Cancellation Rules)

### 5. 前端交互与客户端规则 (Client-Side Interactivity)
#### 页面绑定: `Sales Invoice`
*   **生命周期触发器**: `setup`
*   **字段值变更触发事件 (Field Listeners)**:
    *   `set_query` 字段改变时触发前端计算或联动
#### 页面绑定: `Sales Invoice Timesheet`
*   **字段值变更触发事件 (Field Listeners)**:
    *   `timesheets_remove` 字段改变时触发前端计算或联动
*   **前端弹窗或校验提示 (UI Warnings)**:
    *   Msgprint: Accounting Entries are reposted
    *   Msgprint: Please specify Company to proceed
    *   Throw: Please set Company
    *   Throw: You can only redeem max {0} points in this order.

---

## Purchase Order 业务规则矩阵 (Business Rules Matrix)

### 1. 基础属性与控制规则
*   **模块**: Buying
*   **命名规则 (Naming)**: `naming_series:`
*   **是否可提交 (Is Submittable)**: 是 (Yes)
*   **继承基类 (Base Controller)**: `BuyingController`

#### 字段约束条件:
*   **必填字段 (Mandatory)**:
    *   `title` (Title) [Data]
    *   `naming_series` (Series) [Select]
    *   `supplier` (Supplier) [Link]
    *   `company` (Company) [Link]
    *   `transaction_date` (Date) [Date]
    *   `currency` (Currency) [Link]
    *   `conversion_rate` (Exchange Rate) [Float]
    *   `items` (items) [Table]
    *   `status` (Status) [Select]
*   **只读字段 (Read Only)**:
    *   `supplier_name` (Supplier Name)
    *   `amended_from` (Amended From)
    *   `customer` (Customer)
    *   `customer_name` (Customer Name)
    *   `address_display` (Supplier Address Details)
    *   `contact_display` (Contact Name)
    *   `contact_mobile` (Contact Mobile No)
    *   `contact_email` (Contact Email)
    *   `shipping_address_display` (Shipping Address Details)
    *   `price_list_currency` (Price List Currency)
    *   `pricing_rules` (Purchase Order Pricing Rule)
    *   `supplied_items` (Supplied Items)
    *   `total_qty` (Total Quantity)
    *   `base_total` (Total (Company Currency))
    *   `base_net_total` (Net Total (Company Currency))
    *   `total` (Total)
    *   `net_total` (Net Total)
    *   `total_net_weight` (Total Net Weight)
    *   `other_charges_calculation` (Taxes and Charges Calculation)
    *   `base_taxes_and_charges_added` (Taxes and Charges Added (Company Currency))
    *   `base_taxes_and_charges_deducted` (Taxes and Charges Deducted (Company Currency))
    *   `base_total_taxes_and_charges` (Total Taxes and Charges (Company Currency))
    *   `taxes_and_charges_added` (Taxes and Charges Added)
    *   `taxes_and_charges_deducted` (Taxes and Charges Deducted)
    *   `total_taxes_and_charges` (Total Taxes and Charges)
    *   `base_discount_amount` (Additional Discount Amount (Company Currency))
    *   `base_grand_total` (Grand Total (Company Currency))
    *   `base_rounding_adjustment` (Rounding Adjustment (Company Currency))
    *   `base_in_words` (In Words (Company Currency))
    *   `base_rounded_total` (Rounded Total (Company Currency))
    *   `grand_total` (Grand Total)
    *   `rounding_adjustment` (Rounding Adjustment)
    *   `rounded_total` (Rounded Total)
    *   `in_words` (In Words)
    *   `advance_paid` (Advance Paid)
    *   `status` (Status)
    *   `ref_sq` (Supplier Quotation)
    *   `party_account_currency` (Party Account Currency)
    *   `inter_company_order_reference` (Inter Company Order Reference)
    *   `per_received` (% Received)
    *   `per_billed` (% Billed)
    *   `auto_repeat` (Auto Repeat)
    *   `billing_address_display` (Billing Address Details)
    *   `is_internal_supplier` (Is Internal Supplier)
    *   `represents_company` (Represents Company)
    *   `is_old_subcontracting_flow` (Is Old Subcontracting Flow)
    *   `tax_withholding_net_total` (Tax Withholding Net Total)
    *   `base_tax_withholding_net_total` (Base Tax Withholding Net Total)
*   **自动带入规则 (Fetch From)**:
    *   `supplier_name` (Supplier Name) <- `supplier.supplier_name`
    *   `is_internal_supplier` (Is Internal Supplier) <- `supplier.is_internal_supplier`
    *   `represents_company` (Represents Company) <- `supplier.represents_company`
*   **动态可见性与条件控制 (Depends On)**:
    *   `get_items_from_open_material_requests` (Get Items from Open Material Requests) depends on: `eval:doc.supplier && doc.docstatus===0 && (!(doc.items && doc.items.length) || (doc.items.length==1 && !doc.items[0].item_code))`
    *   `order_confirmation_no` (Order Confirmation No) depends on: `eval:doc.docstatus===1`
    *   `order_confirmation_date` (Order Confirmation Date) depends on: `eval:doc.order_confirmation_no`
    *   `drop_ship` (Drop Ship) depends on: `eval:doc.customer`
    *   `supplier_warehouse` (Supplier Warehouse) depends on: `eval:doc.is_subcontracted`
    *   `total_net_weight` (Total Net Weight) depends on: `total_net_weight`
    *   `base_taxes_and_charges_added` (Taxes and Charges Added (Company Currency)) depends on: `base_taxes_and_charges_added`
    *   `base_taxes_and_charges_deducted` (Taxes and Charges Deducted (Company Currency)) depends on: `base_taxes_and_charges_deducted`
    *   `base_total_taxes_and_charges` (Total Taxes and Charges (Company Currency)) depends on: `base_total_taxes_and_charges`
    *   `taxes_and_charges_added` (Taxes and Charges Added) depends on: `taxes_and_charges_added`
    *   `taxes_and_charges_deducted` (Taxes and Charges Deducted) depends on: `taxes_and_charges_deducted`
    *   `base_rounding_adjustment` (Rounding Adjustment (Company Currency)) depends on: `eval:!doc.disable_rounded_total`
    *   `rounding_adjustment` (Rounding Adjustment) depends on: `eval:!doc.disable_rounded_total`
    *   `per_received` (% Received) depends on: `eval:!doc.__islocal`
    *   `per_billed` (% Billed) depends on: `eval:!doc.__islocal`
    *   `update_auto_repeat_reference` (Update Auto Repeat Reference) depends on: `eval: doc.auto_repeat`
    *   `set_reserve_warehouse` (Set Reserve Warehouse) depends on: `supplied_items`
    *   `tax_withholding_category` (Tax Withholding Category) depends on: `eval: doc.apply_tds`
    *   `set_from_warehouse` (Set From Warehouse) depends on: `is_internal_supplier`

### 2. 前置校验与约束条件 (Validation Rules)
#### `validate` 生命钩子执行校验流:
在该钩子中依次调用了以下内部校验/处理函数:
1.  `self.set_status()`
1.  `self.set_tax_withholding()`
1.  `self.validate_supplier()`
1.  `self.validate_schedule_date()`
1.  `self.validate_uom_is_integer()`
1.  `self.validate_uom_is_integer()`
1.  `self.validate_with_previous_doc()`
1.  `self.validate_for_subcontracting()`
1.  `self.validate_minimum_order_qty()`
1.  `self.validate_fg_item_for_subcontracting()`
1.  `self.set_received_qty_for_drop_ship_items()`
1.  `self.validate_bom_for_subcontracting_items()`

#### 核心控制校验函数与报错信息:
*   `validate_with_previous_doc`:
    *   执行特定条件判定 (无硬性抛错/动态抛错)
*   `validate_supplier`:
    *   **[Msgprint]**: Dynamic message
    *   **[Throw]**: Dynamic message
*   `validate_minimum_order_qty`:
    *   **[Throw]**: Dynamic message
*   `validate_bom_for_subcontracting_items`:
    *   **[Throw]**: Dynamic message
*   `validate_fg_item_for_subcontracting`:
    *   **[Throw]**: Dynamic message
    *   **[Throw]**: Dynamic message
    *   **[Throw]**: Dynamic message
    *   **[Throw]**: Dynamic message
*   `check_on_hold_or_closed_status`:
    *   执行特定条件判定 (无硬性抛错/动态抛错)
*   `update_requested_qty`:
    *   **[Throw]**: Dynamic message
*   `check_modified_date`:
    *   **[Msgprint]**: Dynamic message

### 3. 后置联动与过账逻辑 (Execution / Submission Rules)
#### `on_submit` (提交与过账核心规则):
    *   **触发的下游逻辑 / 更新动作**:
        *   `self.validate_budget()`

### 4. 逆向/作废控制规则 (Cancellation Rules)

### 5. 前端交互与客户端规则 (Client-Side Interactivity)
#### 页面绑定: `Purchase Order`
*   **生命周期触发器**: `setup`
*   **字段值变更触发事件 (Field Listeners)**:
    *   `set_query` 字段改变时触发前端计算或联动
#### 页面绑定: `Purchase Order Item`
*   **字段值变更触发事件 (Field Listeners)**:
    *   `qty` 字段改变时触发前端计算或联动
    *   `schedule_date` 字段改变时触发前端计算或联动
*   **前端弹窗或校验提示 (UI Warnings)**:
    *   Msgprint: Assigning 
    *   Msgprint: Splitting 

---
