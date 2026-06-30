---
name: test-case-writing-styles
description: 定义 GUI、API 和 CLI 测试用例在 canonical JSON 中的字段写作风格。
---

# 测试用例写作风格

本目录定义 `test-design-solution.json` 中测试用例事实字段的执行形态写作风格。公共写作规范以 `knowledge/test-case-writing-standard.md` 为准；本目录只补充 GUI、API、CLI 的差异化表达要求，不改变 schemaVersion 2.0 字段结构。

本目录中的示例只说明字段写法，不构成业务事实、接口契约、页面结构、菜单路径、控件标签、命令名称或测试数据依据。生成 TC 时只能使用当前用户指令、rules、需求、设计、分析方案或可见动态来源中的事实。

## 执行形态路由

生成或评审每个 TC 前，必须先判断主执行形态，并读取对应文件：

| 主执行形态 | 适用对象 | 风格文件 |
|---|---|---|
| GUI | Web、APP、Portal、菜单、页面、表单、按钮、列表和弹窗操作 | `knowledge/test-case-writing-styles/gui-test-case-style.md` |
| API | HTTP/RPC API、回调、消息契约、第三方接口、服务间集成 | `knowledge/test-case-writing-styles/api-test-case-style.md` |
| CLI | 命令行工具、运维命令、批处理命令、脚本入口的黑盒执行 | `knowledge/test-case-writing-styles/cli-test-case-style.md` |

批处理、消息队列、数据库验证、后台任务和日志核查不是独立主风格。它们通常作为 API、CLI 或 GUI 用例的验证手段存在；如果当前 TC 直接通过命令触发批处理，则按 CLI；直接发送消息或调用接口触发，则按 API；从页面触发后再查询批处理结果，则按 GUI。

## 判定优先级

1. 优先依据当前用户明确指令。
2. 其次依据当前 `TP-*` 标题、`objective`、`basisRefs[]`、`generationContext.relevantFacts[]` 和需求/设计来源。
3. 如果一个 TC 同时包含 GUI 操作和接口/数据库验证，按测试人员实际发起动作确定主风格：从页面发起则为 GUI，用接口或数据库步骤作为取数验证动作；直接调用接口则为 API；直接执行命令则为 CLI。
4. 不因为验证手段改变主风格。例如：GUI 提交交易后查询数据库确认状态，仍是 GUI 用例；API 创建交易后查询数据库确认副作用，仍是 API 用例；CLI 执行批处理命令后读取日志，仍是 CLI 用例。
5. 如果无法唯一判断，不强行补造 GUI 菜单、接口路径或 CLI 命令；使用通用可执行动作规范，并在可见事实不足处使用稳定数据槽位或保守预期。

## 共同约束

- `steps[].action` 只写用户、测试人员、外部调用方或测试工具可执行的动作或取数动作。
- 系统判断、系统处理、系统返回、状态变化、数据写入和校验结论写入同一步 `steps[].expected`，不得单独写成 action。
- `preconditions[]` 写执行前必须已满足的环境、账号、权限、数据状态或配置开关。
- `testData[]` 写具体值或稳定数据槽位，不写抽象标签。
- `expectedResult` 写最终业务判定，必须有当前用户指令、rules、需求、设计、分析方案或可直接推出的业务不变量支撑。
- 当关键执行细节缺少依据时，不用“执行操作”“调用接口”“运行命令”掩盖缺口；应写输入可支撑的稳定槽位，例如 `菜单路径=待人工确认`、`接口=待人工确认`、`命令=待人工确认`，并保持预期为保守判定。
