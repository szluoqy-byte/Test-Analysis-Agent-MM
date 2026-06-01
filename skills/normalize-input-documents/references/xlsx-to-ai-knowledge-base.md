# XLSX 转 AI 可用项目知识参考

本文件是 `normalize-input-documents` 的内置参考，用于把 Excel 里的测试设计因子库、业务测试模式库、checklist 或方法材料整理成 AI Agent 可读取的项目知识。它不是主流程强制格式；项目知识文件名和格式仍可自理解识别。

## 目标

普通 Excel 表格转 Markdown 只能保留数据。测试分析和测试设计真正需要的是可应用的知识：

- 什么时候加载这份知识。
- 每列是什么意思。
- 哪些内容是测试输入、条件、状态、组合。
- 哪些内容是预期结果或检查目标。
- 哪些内容只是前置导航、操作背景或历史备注。
- 哪些场景应该合并，哪些因子应该保留原子粒度。

## 推荐归档位置

项目级知识建议放在：

```text
knowledge/projects/<project-key>/<自定义文件名>.md
```

如果是强制规则，不应放入 knowledge，应放入：

```text
rules/projects/<project-key>/<自定义文件名>.md
```

如果是个人关注点或个人偏好，放入：

```text
knowledge/user/<自定义文件名>.md
```

## 推荐文件结构

```markdown
# <项目名> 测试设计因子库

## 使用说明

- 适用阶段：testing-method-router / testpoint-generation / test-analysis-solution-generation / test-design-solution-generation / coverage-review
- 适用范围：<业务域、接口域、产品域>
- 使用方式：<生成测试点、生成测试设计项或校验遗漏时如何引用>

## 字段说明

| 字段 | 含义 | Agent 应用方式 |
| --- | --- | --- |
| 场景 | 业务场景或规则域 | 用于匹配 SC 或 TP |
| 测试因子 | 代表性条件、输入、状态、组合或操作 | 用于生成 TP 明细或 TDI |
| 说明 | 验证目标或预期关注点 | 用于补充预期结果或 review |

## 1. <业务场景>

> 场景说明：<该场景覆盖什么业务活动、规则或风险>

| 场景 | 测试因子 | 说明 |
| --- | --- | --- |
| <场景> | <条件/输入/状态/组合> | <验证目标> |
```

## 测试因子字段语义

测试因子描述的是“拿什么去覆盖”，不是“期望看到什么”。

正确方向：

- 文件大小超过限制。
- 订单 ID 长度等于 13 位。
- 订单 ID 长度小于 13 位。
- 接口返回超时。
- 用户无对应菜单权限。

错误方向：

- 功能正确。
- 界面显示正常。
- 下发失败。
- 数据校验正确。

如果 Excel 中的 `name` 列是预期结果式描述，应从 `factorOperation`、`operation`、`input`、`condition` 等列中抽取真正的测试动作或输入条件。

## 从操作列抽取测试因子

Portal、GUI 或流程类表格常把登录、进入菜单、点击路径、检查点写在同一列。抽取时应去掉导航和准备动作，只保留测试相关动作、输入和条件。

保留动词示例：

- 检查、输入、提交、删除、修改、新增、填写、查询、发布、关闭、审批、拒绝、回滚。

过滤动词示例：

- 登录、进入、打开、选择菜单、跳转到、发起到某页面。

抽取示例：

```text
原始操作：操作员登录后点击 X->Y 菜单，选择对应输入条件，订单ID长度小于13位，查询
测试因子：订单ID长度小于13位查询
```

如果一行包含多个独立代表值，可以合并在同一个测试因子里用 `/` 分隔；不要把一个 Excel 数据行拆成多条无来源关系的知识行。

## 说明字段抽取

说明字段用于表达“为什么测”和“检查什么”，优先来自 expected result / expectResult / assertion 类列。

处理规则：

- 过滤通用前置结果：登录成功、页面显示正常、菜单显示正确、打开成功、不报错。
- 保留业务判定：状态变化、错误提示、错误码、金额变化、记录落库、消息发送、回调结果。
- 只截取 2 到 3 条核心验证目标，避免把完整测试步骤写进知识库。
- 如果没有明确判定依据，写“待人工分析确认”，不要编造错误码或提示文案。

## 场景合并规则

Excel 中的场景名不一定等于测试分析中的真实测试场景。以下类型通常是伪场景，应合并到更大的业务上下文：

- 单一实体类型：Bank、Group、Till、Operator。
- 单一检查点：PIN 校验、GUI 检查、字段校验。
- 查询子类型：精确查询、模糊查询、组合查询、性能查询。
- 生命周期碎片：激活、关闭、休眠、手机号回收。
- CRUD 子动作：新增、修改、删除、查询。

判断标准：

```text
这个名称是否描述了用户正在完成的业务过程？
```

如果答案是否，它更可能是测试点、测试因子或检查项，而不是测试场景。

## 空壳行过滤

测试因子库中经常存在只有 ID 或标题、没有执行内容的占位行。满足以下条件时应过滤：

- preRequisites 为空。
- factorOperation 为空。
- expectResult 为空。
- aw_precondition 为空。
- aw_operation 为空。
- aw_expectResult 为空。

过滤数量应写入转换说明，方便追踪为什么知识行数少于原始 Excel 行数。

## 分块与索引

当转换结果超过约 100KB 时，按业务域、一级分类或场景边界拆分，避免一个知识文件过大。

推荐同时生成一个 README 或索引段：

```markdown
# <项目> 知识索引

| 文件 | 覆盖范围 | 适用阶段 |
| --- | --- | --- |
| payment-factor-library.md | 支付、退款、冲正 | 测试分析、测试设计、coverage-review |
```

拆分时不要从表格中间切断。每个分块都应保留字段说明和使用说明，确保单独读取时可理解。

## 与本项目流程的绑定

context pack 阶段不需要提前判断具体命中哪个测试点，只需要识别知识类型和建议应用阶段。

建议绑定：

- 测试设计因子库：`testing-method-router`、`testpoint-generation`、`test-analysis-solution-generation`、`test-design-solution-generation`。
- 业务测试设计模式库：`testing-method-router`、`testpoint-generation`、`test-design-solution-generation`。
- checklist：默认绑定 `coverage-review`；只有明确用于语义评审时才绑定 review skill。
- Oracle 或预期结果依据：`test-analysis-solution-generation`、`test-design-solution-generation`、review skill。
