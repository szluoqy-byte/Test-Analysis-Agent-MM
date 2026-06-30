---
name: gui-test-case-style
description: 定义 GUI 测试用例的前置条件、测试数据、步骤和预期写法。
---

# GUI 测试用例写作风格

GUI 用例面向人工执行或 GUI 自动化 Agent 执行。步骤必须描述页面上可定位、可操作、可观察的动作。

本文示例只说明 GUI 字段写法，不构成真实菜单、页面、控件或测试数据依据。

## preconditions[]

- 写清登录状态、角色权限、入口页面、浏览器或 APP 环境、必要配置和初始数据状态。
- 如果需要特定账号或数据，使用稳定数据槽位，例如 `用户=AGT_USER_001`、`订单=ORDER_PENDING_001`。
- 不把具体点击路径写成前置条件；点击路径应进入 `steps[].action`。
- 如果页面入口、菜单路径或控件标签没有输入依据，写稳定槽位或待人工确认，不编造真实页面结构。

## testData[]

- 使用页面字段、业务字段或稳定数据槽位命名，例如 `Merchant Name`、`MSISDN`、`amount`。
- `value` 必须是具体值或稳定槽位，避免只写“有效金额”“错误 PIN”。
- `description` 说明该值对应的业务含义、边界或状态。

## steps[].action

GUI action 必须写用户或自动化 Agent 可执行的页面动作，优先使用以下格式：

- `进入菜单「A > B > C」`
- `在页面「Merchant List」点击按钮「Add Merchant」`
- `在页面「Add Merchant」的输入框「Merchant Name」输入「AGT Merchant 001」`
- `在页面「Add Merchant」的下拉框「Status」选择「Active」`
- `在页面「Add Merchant」勾选复选框「Accept Terms」`
- `在页面「Merchant List」切换页签「Active」`
- `在页面「Merchant List」点击开关「Auto Settlement」切换为「On」`
- `在页面「Merchant List」上传控件「Import File」选择文件「merchant_import_valid.xlsx」`
- `在页面「Merchant List」的日期控件「Start Date」选择「2026-06-30」`
- `在页面「Merchant List」筛选字段「Merchant Name」为「AGT Merchant 001」`
- `打开列表「Merchant List」中记录「AGT Merchant 001」的详情页`
- `在弹窗「Confirm」点击按钮「OK」`

GUI action 应尽量包含页面/菜单路径、控件类型、控件可见文本或字段标签、输入值和具体动作。不得写成“完成新增”“进行查询”“系统创建商户”“页面校验成功”等抽象动作或系统行为。

不要使用不稳定定位方式，例如坐标、颜色、相对布局或视觉描述：`点击右上角蓝色按钮`、`点击第二个按钮`、`点击左侧区域` 都不合格，除非输入事实只提供了这类描述且无更稳定定位。

## steps[].expected

- 写页面可观察结果，例如页面标题、成功提示、错误提示、页面跳转、弹窗、列表行、字段值、按钮状态、可见/不可见状态。
- 系统处理结果必须落到可观察对象上，例如 `页面显示提示「保存成功」`、`列表出现 Merchant Name=AGT Merchant 001 的记录`。
- 如果输入没有说明具体提示文案，不编造文案，只写保守预期，例如 `页面显示失败提示，且不生成成功态记录`。
- 不写“页面正常”“校验通过”“系统内部处理完成”这类不可观察结论。

## expectedResult

- 汇总最终业务判定，例如数据保存成功、交易被拒绝、状态保持不变或记录可查询。
- 不重复枚举所有点击步骤。

## 示例

```json
{
  "preconditions": ["测试人员已使用角色=商户管理员登录 Portal", "商户 AGT Merchant 001 不存在"],
  "testData": [
    {"name": "Merchant Name", "value": "AGT Merchant 001", "description": "新增商户名称"}
  ],
  "steps": [
    {"stepNo": 1, "action": "进入菜单「Merchant Management > Merchant List」", "expected": "页面显示 Merchant List 列表"},
    {"stepNo": 2, "action": "在页面「Merchant List」点击按钮「Add Merchant」", "expected": "页面打开 Add Merchant 表单"},
    {"stepNo": 3, "action": "在页面「Add Merchant」的输入框「Merchant Name」输入「AGT Merchant 001」", "expected": "输入框显示 AGT Merchant 001"},
    {"stepNo": 4, "action": "在页面「Add Merchant」点击按钮「Submit」", "expected": "页面显示保存成功提示"}
  ],
  "expectedResult": "商户 AGT Merchant 001 创建成功，并可在 Merchant List 查询到。"
}
```

## 反例

- `action`: `系统创建商户`
- `action`: `完成商户新增`
- `action`: `检查列表数据`
- `action`: `点击右上角蓝色按钮`
- `action`: `等待系统处理完成`
- `expected`: `系统内部校验通过`
- `expected`: `页面正常`
