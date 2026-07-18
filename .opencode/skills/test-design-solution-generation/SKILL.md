---
name: test-design-solution-generation
description: 基于已评审测试分析方案、需求/设计依据和可见动态来源，按每个已冻结 TP 填写 TC 切片并合并为 schema 2.0 测试设计方案。
---

# 测试设计方案生成

本 skill 负责测试设计生成阶段，但不再整包一次性生成所有 TC。它按 `process/test-case-work-items.json` 中的每个 `TP-*` 初始化并填写 `process/test-case-slices/<TP-ID>.json`，再由 workflow 调用 `bin/merge-staged-slices.py --scope design` 统一合并为 `deliverables/test-design-solution.json`。

## 何时使用

在 `test-design-workflow` 已绑定并校验 `deliverables/test-analysis-solution.json`、且已生成 `process/test-case-work-items.json` 后使用。不要在缺少完整分析 JSON 时使用，也不要用它重新生成 SC/TP。

## 必读上下文

- `deliverables/test-analysis-solution.json`
- `process/test-case-work-items.json`
- `process/test-case-slices/<TP-ID>.json`
- 当前 `process/test-case-slices/<TP-ID>.json` 内的 `generationContext`
- 归一化后的需求 Markdown 和可选设计方案 Markdown
- `process/rules-pack.json`
- `process/context-pack.json`
- `knowledge/test-design-solution-standard.md`
- `knowledge/test-case-writing-standard.md`
- `knowledge/test-case-writing-styles/README.md`
- `templates/test-design-solution-json-template.json`
- 对本阶段可见的 project/personal 动态来源

## 生成检查清单

Progress:
- [ ] Step 1: 确认完整分析方案已绑定并通过 schema `2.0` 校验
- [ ] Step 2: 读取当前 TP 工作项和 TC 切片中的 `generationContext`
- [ ] Step 3: 读取适用 rules、可见动态来源和 relevant facts
- [ ] Step 4: 识别当前 TP 的必选因子、候选因子和模型补充必要因子，再形成最小充分 TC 集合
- [ ] Step 5: 只填写当前 `process/test-case-slices/<TP-ID>.json` 的 `testPoint.testCases[]`
- [ ] Step 6: 通过 TC 切片 review 后用固定脚本合并并统一 TC 编号
- [ ] Step 7: 合并后运行 `python bin/lint-run-json.py outputs/runs/<run-id>`
- [ ] Step 8: 交给 `test-case-writing` 渲染 Markdown，不手工写 Markdown

## 计划-校验-执行模式

计划阶段由完整分析方案、TP 工作项和 `generationContext` 限定当前 TP 范围；校验阶段包括 TC 切片 review、最终设计 review、coverage-review 和 `lint-run-json.py`；执行阶段只允许固定脚本合并切片并统一 TC 编号。任何校验失败都回到当前 TP 的 TC 切片，不直接改最终交付件或 Markdown。

## 易错点

- 不要在一个 TC 的 steps 中枚举多组互斥输入、角色、状态、配置或接口参数变体。
- 不要把检查项、断言项或系统内部行为写成 `steps[].action`。
- 不要因为输入依据不足而补造 GUI 控件、接口路径、错误码、提示文案或阈值。
- 不要把已加载的因子库、checklist、knowledge 或方法参考当作封闭全集；除非更高优先级指令明确限定仅使用指定因子集合，否则必须继续判断当前 TP 下是否存在这些来源未显式列出的必要测试实例。

## 执行步骤与生成原则

1. 完整继承分析方案的 `SC-*` 场景树和 `TP-*` 测试点，不新增、删除、合并或改写分析层级。
2. 生成前必须确认当前 `process/test-case-slices/<TP-ID>.json` 已由固定脚本写入 `generationContext`；若缺失，先运行 `skills/test-design-solution-generation/scripts/init-test-case-slice.py` 或 `bin/build-generation-context.py` 生成，不手工拼写。
3. 优先读取 `generationContext.applicableRules[]` 中已内联的本阶段 rules 正文；TC 粒度、覆盖策略、数据表达、预期依据和禁止项必须遵守适用 rules。
4. 按 `generationContext.visibleSources[]` 判断本阶段可见动态来源；只读取与当前 TP 的测试用例设计有关的正文。
5. 使用 `generationContext.relevantFacts[]` 作为当前 TP 的优先事实候选；如候选不足，可回读输入事实模型、需求或设计方案，但不得改写 SC/TP。
6. 每次只处理一个 `process/test-case-slices/<TP-ID>.json`，只填写当前 `testPoint.testCases[]`。
7. 每个 `TP-*` 至少生成 1 个 `TC-*`，但不得把“至少 1 个”当作充分覆盖。TP 是验证目标簇，必须生成覆盖该 TP 适用测试设计因子的最小充分 TC 集合。
8. 填写 TC 前，先在思考中完成当前 TP 的测试实例拆解：识别必选因子、候选因子和基于 TP 目标补充推导的必要因子。必选因子来自 rules、当前用户明确指令和输入文档明确事实；候选因子来自 knowledge、project/personal 动态来源、方法参考和 `generationContext.visibleSources[]`；补充因子来自对当前 TP 目标、业务规则、接口契约、状态、权限、数据、异常、边界、组合和可观察结果差异的测试设计判断。
9. 已加载来源中的既有测试设计因子是必选覆盖项或启发来源，不是封闭上限。除非更高优先级指令明确限定仅使用指定因子集合，否则不得因为因子库、checklist、knowledge 或方法参考未列出某类情况，就忽略该 TP 下有判定意义的独立测试实例。
10. 只把有输入依据、适用规则、业务不变量或合理测试设计推导支撑的实例写入 `testCases[]`；模型补充因子不得覆盖或违背 rules、当前用户明确指令、输入文档明确事实或分析方案。
11. 如果当前 TP 只生成 1 个 TC，必须能从输入依据、业务不变量、模型测试经验或切片评审说明中解释该 TP 不存在可支持的额外独立因子拆分；否则应继续拆分代表性成功、拒绝/失败、边界/异常、状态/权限/配置差异或关键组合 TC。
12. 不要求穷举所有无业务意义的笛卡尔积；“最小充分”不是“最少”，而是覆盖所有对该 TP 判定有意义的独立测试实例，并优先覆盖高风险、关键规则、明确需求、明确设计和代表性等价类/边界。
13. `TC-*` 最终由 `skills/test-design-solution-generation/scripts/merge-test-case-slice.py` 分配 run 内全局唯一、增量稳定的编号；既有 TC 保留 ID，新 TC 从历史最大值后追加，退役编号不复用。
14. TC 必须具体到可执行实例：明确用例级别、前置条件、测试数据、操作步骤、步骤预期和最终预期。
15. 每个 TC 必须填写 `level`，取值只能是 `Level 0`、`Level 1`、`Level 2`、`Level 3`、`Level 4`，定义以 `knowledge/test-design-solution-standard.md` 为准。
16. `testData[]` 使用 `{name, value, description}` 数组，必须给出具体值或稳定数据槽位。
17. `steps[]` 使用 `{stepNo, action, expected}` 数组，`stepNo` 从 1 连续。
18. `expectedResult` 只能来自当前用户明确指令、适用 rules、需求、设计方案、分析方案或可直接推出的业务不变量。
19. 依据不足时使用保守预期，例如“请求被拒绝，系统不产生成功态数据变更”，不补写未说明的错误码、提示文案或状态值。
20. 生成每个 TC 前必须先读取并遵守 `knowledge/test-case-writing-standard.md` 的公共写作规范，再判断主执行形态，并按需读取 `knowledge/test-case-writing-styles/` 下的对应风格文件：GUI 读取 `gui-test-case-style.md`，API 读取 `api-test-case-style.md`，CLI 读取 `cli-test-case-style.md`；无法唯一判断时读取 `README.md` 的通用约束，不强行补造执行细节。
21. GUI 用例 action 必须明确页面/菜单路径、控件类型、控件可见文本、输入值和点击/选择/上传等动作；不得写“完成新增”“进行查询”“系统创建”这类抽象动作或系统行为。
22. API 用例不得写完整裸 URL；action 使用 `接口=METHOD /path`、`Header.X=...`、`Query.X=...`、`Body.X=...` 等字段片段；expected 写响应状态、响应字段、错误码、幂等结果或数据副作用。
23. CLI 用例 action 必须写明执行主机/容器/工作目录、用户或环境变量，以及实际执行命令；expected 写退出码、stdout/stderr、输出文件、日志或查询状态。
24. 依据不足时不得编造 GUI 菜单、控件标签、接口路径、命令名或命令参数；只能使用需求/设计/规则/分析方案中已有事实或稳定数据槽位。
25. 遵守 TC 原子性原则：一个 TC 只覆盖一个可独立执行、独立判定的测试实例。该原则适用于接口、页面、业务流程、权限、状态、配置、批处理、消息、外部依赖、数据组合和异常处理等所有测试类型。
26. 不同输入条件、数据组合、等价类、边界点、角色、权限、状态、配置、外部依赖返回、消息顺序、异常类型或接口参数变体都应拆成独立 TC。
27. `steps[]` 只表达同一个测试实例内的顺序动作与观察点，不得用多条步骤枚举多个互斥请求、多组替代数据、多种角色/状态/配置切换或多条独立路径。例如 `orderNo` 缺失、`channel` 缺失、`amount` 缺失、`clientRequestId` 缺失必须生成 4 个 TC，而不是 1 个 TC 的 4 个步骤；不同角色取消订单、不同订单状态取消订单、不同开关配置下创建订单也同理拆分。
28. `steps[].action` 只写用户、测试人员、外部调用方或测试工具可执行的操作或取数动作，不单独写检查项、断言项、观察结论或系统内部行为；字段值、状态、记录、事件、响应内容等检查要求，以及系统判断、系统处理、系统返回、系统取消、系统释放、系统写入等行为必须写入同一步的 `expected`。
29. 不得把系统行为写成测试步骤动作，例如不要写 `MM系统判断count=0后取消交易`、`系统返回错误提示`、`服务端释放库存`、`定时任务触发补偿`；应改为 `测试人员提交count=0的交易请求` / `调用接口=POST /xxx` / `查询交易状态或库存记录`，并在 `expected` 中描述系统判断、返回、释放、补偿等预期。
30. 如果需要验证响应体、数据库、消息、日志或领域事件，`action` 写“获取/查询/读取/订阅/拉取对象”，`expected` 写具体字段、状态、记录或事件要求。例如不要写 `检查响应体字段` 作为独立步骤，应写在调用接口步骤的 `expected` 或下一步查询动作的 `expected` 中。

## JSON 结构

切片输出必须写入：

```text
outputs/runs/<run-id>/process/test-case-slices/<TP-ID>.json
```

最终主输出由 workflow 使用 `bin/merge-staged-slices.py --scope design` 调用底层切片合并脚本后写入：

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

局部 JSON 由 workflow 使用 `python bin/merge-staged-slices.py outputs/runs/<run-id> --scope design --ids <TP-ID>` 或 `--all` 合并回主交付件；不要手工拼接主 JSON，不要临时创建 Python/JavaScript/PowerShell 脚本处理 JSON。

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
- 不删除或手工伪造 `generationContext`；上下文缺失或过期时运行固定脚本刷新。
- 不写 schemaVersion 2.0 之外的字段。
- 不在 TC 切片阶段改写 SC/TP。
- 不输出自动化脚本或真实生产数据。
- 不在生成过程中创建临时 `.py`、`.js`、`.ps1` 或其他可执行脚本。
- 派生表达由 `test-case-writing` 读取 canonical JSON 后生成。

## 验证闭环

每个 TP 切片填写后先进入 `test-design-solution-review`。评审通过后运行 `python bin/merge-staged-slices.py outputs/runs/<run-id> --scope design --ids <TP-ID>`；全部完成后运行 `--all` 合并并统一 TC 编号，再运行 `python bin/lint-run-json.py outputs/runs/<run-id>`。失败时回到对应切片或 canonical JSON 修复，不手工编辑 Markdown。
