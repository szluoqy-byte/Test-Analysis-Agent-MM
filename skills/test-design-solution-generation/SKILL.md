---
name: test-design-solution-generation
description: 基于已评审测试分析方案、需求/设计依据和可见动态来源，生成 schema 2.0 的 SC/TP/TC 测试设计方案。
---

# 测试设计方案生成

本 skill 负责生成 `deliverables/test-design-solution.json`。它继承测试分析方案中的 `SC-*` 场景树和 `TP-*` 测试点，并在每个测试点下生成完整步骤级 `TC-*` 测试用例。

## 必读上下文

- `deliverables/test-analysis-solution.json`
- 归一化后的需求 Markdown 和可选设计方案 Markdown
- `process/context-pack.json`
- `knowledge/test-design-solution-standard.md`
- `templates/test-design-solution-json-template.json`
- 对本阶段可见的 project/personal 动态来源

## 生成原则

1. 完整继承分析方案的 `SC-*` 场景树和 `TP-*` 测试点，不新增、删除、合并或改写分析层级。
2. 每个 `TP-*` 至少生成 1 个 `TC-*`。
3. `TC-*` 全局连续编号，不按场景或测试点重置。
4. TC 必须具体到可执行实例：明确用例级别、前置条件、测试数据、操作步骤、步骤预期和最终预期。
5. 每个 TC 必须填写 `level`，取值只能是 `Level 0`、`Level 1`、`Level 2`、`Level 3`、`Level 4`，定义以 `knowledge/test-design-solution-standard.md` 为准。
6. `testData[]` 使用 `{name, value, description}` 数组，必须给出具体值或稳定数据槽位。
7. `steps[]` 使用 `{stepNo, action, expected}` 数组，`stepNo` 从 1 连续。
8. `expectedResult` 只能来自当前用户明确指令、适用 rules、需求、设计方案、分析方案或可直接推出的业务不变量。
9. 依据不足时使用保守预期，例如“请求被拒绝，系统不产生成功态数据变更”，不补写未说明的错误码、提示文案或状态值。
10. 接口类用例不得写完整裸 URL；拆成 `接口=METHOD /path`、`参数名=参数值`、`响应状态=...` 等字段片段。
11. 遵守 TC 原子性原则：一个 TC 只覆盖一个可独立执行、独立判定的测试实例。该原则适用于接口、页面、业务流程、权限、状态、配置、批处理、消息、外部依赖、数据组合和异常处理等所有测试类型。
12. 不同输入条件、数据组合、等价类、边界点、角色、权限、状态、配置、外部依赖返回、消息顺序、异常类型或接口参数变体都应拆成独立 TC。
13. `steps[]` 只表达同一个测试实例内的顺序动作与观察点，不得用多条步骤枚举多个互斥请求、多组替代数据、多种角色/状态/配置切换或多条独立路径。例如 `orderNo` 缺失、`channel` 缺失、`amount` 缺失、`clientRequestId` 缺失必须生成 4 个 TC，而不是 1 个 TC 的 4 个步骤；不同角色取消订单、不同订单状态取消订单、不同开关配置下创建订单也同理拆分。
14. `steps[].action` 只写用户、测试人员、外部调用方或测试工具可执行的操作或取数动作，不单独写检查项、断言项、观察结论或系统内部行为；字段值、状态、记录、事件、响应内容等检查要求，以及系统判断、系统处理、系统返回、系统取消、系统释放、系统写入等行为必须写入同一步的 `expected`。
15. 不得把系统行为写成测试步骤动作，例如不要写 `MM系统判断count=0后取消交易`、`系统返回错误提示`、`服务端释放库存`、`定时任务触发补偿`；应改为 `测试人员提交count=0的交易请求` / `调用接口=POST /xxx` / `查询交易状态或库存记录`，并在 `expected` 中描述系统判断、返回、释放、补偿等预期。
16. 如果需要验证响应体、数据库、消息、日志或领域事件，`action` 写“获取/查询/读取/订阅/拉取对象”，`expected` 写具体字段、状态、记录或事件要求。例如不要写 `检查响应体字段` 作为独立步骤，应写在调用接口步骤的 `expected` 或下一步查询动作的 `expected` 中。

## JSON 结构

主输出必须写入：

```text
outputs/runs/<run-id>/deliverables/test-design-solution.json
```

结构要求：

- `artifactType`: `test-design-solution`
- `schemaVersion`: `2.0`
- `inputs[]`: 设计输入说明
- `scenarios[]`: 继承分析方案场景树
- 叶子场景的 `testPoints[]` 继承 `id`、`title`、`objective`、`basisRefs[]`
- 每个测试点下生成 `testCases[]`

大文件分批模式下，输入是 `process/design-slices/<batch>.json`，输出是 `process/design-slices/<batch>-design.json`。`<batch>-design.json` 必须先由 `python bin/init-design-slice.py outputs/runs/<run-id> --batch <batch>` 生成骨架；生成阶段只填写该骨架中既有 TP 的 `testCases[]`，不得新增、删除、合并或改写 `SC-*` 与 `TP-*`。

```text
outputs/runs/<run-id>/process/design-slices/<batch>-design.json
```

局部 JSON 由 `python bin/merge-design-slice.py outputs/runs/<run-id> --slice <slice-json>` 合并回主交付件；不要手工拼接主 JSON，不要临时创建 Python/JavaScript/PowerShell 脚本处理 JSON。

每个 TC 必须包含：

- `id`
- `title`
- `level`
- `preconditions[]`
- `testData[]`
- `steps[]`
- `expectedResult`
- `sourceRefs[]`

## 禁止项

- 不手工写 Markdown、CSV、平台导入文件或其他派生表达格式。
- 不写 schemaVersion 2.0 之外的字段。
- 不输出自动化脚本或真实生产数据。
- 不在生成过程中创建临时 `.py`、`.js`、`.ps1` 或其他可执行脚本。
- 派生表达由 `test-case-writing` 读取 canonical JSON 后生成。
