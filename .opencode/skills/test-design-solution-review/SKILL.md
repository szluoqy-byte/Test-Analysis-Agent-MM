---
name: test-design-solution-review
description: 评审按 TP 生成的 TC 切片和最终 schema 2.0 测试设计方案的 TC 粒度、步骤可执行性、测试数据明确性、预期依据和分析方案承接。
---

# 测试设计方案语义评审

本 skill 是 `test-design-agent` 的产物级语义评审环节。结构、编号、JSON canonical 结构和 Markdown 语法以确定性脚本为准；本 skill 只评审语义质量。它先按 `process/test-case-slices/<TP-ID>.json` 评审单个 TP 下的 TC，再评审最终 `deliverables/test-design-solution.json`。

## 何时使用

在单个 TC 切片或最终设计方案已经生成、且评审 JSON skeleton 已由 `bin/init-report-artifact.py` 初始化后使用。不要用本 skill 做 deterministic lint，也不要直接改写测试用例事实。

## 输入

- `outputs/runs/<run-id>/deliverables/test-design-solution.json`
- `outputs/runs/<run-id>/deliverables/test-analysis-solution.json`
- `process/test-case-slices/<TP-ID>.json`
- `bin/lint-run-json.py`、`bin/render-run-markdown.py --check` 和 `bin/lint-test-design-solution.py` 的执行结果
- 归一化后的需求 Markdown 和可选设计方案 Markdown
- `process/rules-pack.json`
- `process/context-pack.json`
- 目标评审 JSON 内的 `generationContext`；缺失时先运行 `bin/init-report-artifact.py`
- `knowledge/test-design-solution-standard.md`
- `knowledge/test-case-writing-standard.md`
- `knowledge/test-case-writing-styles/README.md` 及当前 TC 主执行形态对应的 GUI/API/CLI 风格文件

## 审查步骤与重点

| 维度 | 检查内容 |
|---|---|
| 分析承接 | 设计方案是否完整继承 SC/TP，不新增、删除、合并或改写分析层级 |
| 用例覆盖 | 每个 TP 是否生成覆盖该验证目标适用测试设计因子的最小充分 TC 集合；是否先覆盖 rules、当前用户明确指令和输入文档明确事实中的必选因子，再结合 knowledge、动态来源和方法参考中的候选因子判断适用性；是否遗漏已加载来源未明说、但 TP 目标明显需要的输入条件、边界、状态、权限、配置、依赖、消息顺序、异常或数据组合；只生成 1 个 TC 时是否有依据说明没有可支持的额外独立因子拆分 |
| 用例粒度 | TC 是否具体到可执行实例，而不是抽象条件标签；是否把多个独立输入条件、数据组合、等价类、边界点、角色、权限、状态、配置、外部依赖返回、消息顺序或异常类型合并进一个 TC |
| 用例级别 | `level` 是否符合 `Level 0` 到 `Level 4` 定义，是否与失败后果、风险和覆盖优先级匹配 |
| 公共写作规范 | 是否遵守 `knowledge/test-case-writing-standard.md`，包括标题、前置条件、测试数据、步骤动作、步骤预期、最终预期和来源引用的公共写法 |
| 测试数据 | `testData[]` 是否给出具体值或稳定数据槽位，并说明含义 |
| 执行形态风格 | 是否按当前 TC 主执行形态读取并遵守 `knowledge/test-case-writing-styles/` 下的 GUI、API 或 CLI 风格；混合场景是否按测试人员实际发起动作确定主风格 |
| 步骤可执行性 | `steps[]` 是否按顺序表达同一个测试实例内由用户、测试人员、外部调用方或测试工具执行的动作和步骤预期，而不是枚举多个互斥请求、多组替代数据、多种角色/状态/配置切换或多条独立路径；`action` 是否只写可执行动作或取数动作，没有把检查项、断言项、观察结论或系统内部行为单独写成步骤 |
| GUI 表达 | GUI 用例是否明确页面/菜单路径、控件类型、控件可见文本、输入值和页面可观察结果；没有依据时是否避免编造菜单或控件 |
| API 表达 | API 用例是否使用 `接口=METHOD /path`、Header、Query、Body 等字段片段，expected 是否写响应状态、响应字段、错误码、幂等结果或数据副作用 |
| CLI 表达 | CLI 用例是否写明主机/容器/工作目录、用户或环境变量、执行命令，expected 是否写退出码、stdout/stderr、文件、日志或状态查询结果 |
| 最终预期 | `expectedResult` 是否有需求、设计、规则或分析方案依据 |
| 接口表达 | 接口类用例是否拆成字段片段，避免完整裸 URL |
| Rules 应用 | 是否从 `process/rules-pack.json` 的 `ruleSources[]` 筛选并读取了适用 rules 正文，是否已遵守，冲突时是否说明规则覆盖输入的原因 |
| 动态来源 | 可见 project/personal 来源是否被读取、应用或解释不适用 |

## 输出

单个 TP 的 TC 切片评审写入 `process/reviews/test-case-reviews/<TP-ID>.json`，汇总可写入 `process/reviews/test-case-review.json`；最终设计方案评审写入 `process/reviews/test-design-solution-review.json`。报告必须先由 `bin/init-report-artifact.py` 生成 skeleton 和 `generationContext`，AI 只填写语义结论字段；如需人读版，由 `bin/render-run-markdown.py` 渲染。

- `result` 只能填写 `通过`、`需修正`、`失败`、`警告` 或 `不适用`；`findings[]`、`blockingIssues[]`、`recommendations[]` 和 `evidenceRefs[]` 必须保留为数组。
- `blockingIssues[]` 中每项使用与 `findings[]` 相同的对象字段：`id`、`severity`、`dimension`、`location`、`description`、`evidence`、`recommendation`；`severity` 固定为 `blocking`，`location` 必须指向 `process/test-case-slices/<TP-ID>.json`，供返工脚本重开工作项，不能只写主交付 Markdown。

## 验证闭环

评审输出后确认 `result`、`findings[]`、`blockingIssues[]`、`recommendations[]` 和 `evidenceRefs[]` 已填写。若存在 blocking 项，workflow 必须运行 `python bin/apply-review-findings.py outputs/runs/<run-id> --scope design --all` 重开对应 TP 工作项，再回到 TC 切片修复、合并和最终评审。评审 JSON 结构校验失败时，先重新运行 `bin/init-report-artifact.py` 初始化 skeleton，再填写语义结论。

## 易错点

- 不要只检查每个 TP 是否至少有 1 个 TC；这只是结构底线，不是充分覆盖。
- 不要把已加载的因子库、checklist、knowledge 或方法参考当作覆盖上限；它们是必选覆盖项或启发来源，仍需检查模型是否遗漏当前 TP 下有判定意义的必要测试实例。
- 不要把多个独立测试实例合并成一个 TC 的多个 steps。
- 不要把写作风格问题当成覆盖充分性问题；覆盖由 TC 集合和 coverage-review 判断。

## 约束

- 不重复 deterministic lint 已覆盖的结构、编号和 Markdown 检查。
- 不新增、删除或改写 SC/TP。
- 不把 coverage 缺口判断写成最终报告；覆盖门禁交给 `coverage-review`。
