---
name: test-design-workflow
description: 当用户提供已评审测试分析方案并要求扩展 TC 测试用例时使用；该 skill 编排测试分析方案校验、依据补读、测试设计方案 JSON 生成、写作渲染和独立评审。
---

# 测试分析方案到测试设计方案主入口

本 skill 是 `test-design-agent` 的完整链路入口。目标是从 `$ARGUMENTS` 指定的已评审 `测试分析方案` 出发，生成 `测试设计方案`。

测试设计方案回答 how to test：继承 `SC-*` 场景树和 `TP-*` 测试点，并在每个测试点下生成完整步骤级 `TC-*` 测试用例。

## 必需输入

- `$ARGUMENTS`：可显式指定一份 `test-analysis-solution.json`；若指定，必须优先使用该文件。
- 可选：原始需求文档路径、设计方案文档路径或 `project=<project-key>`；personal rules 来自 `rules/user/**/*.md`，personal 动态补充来源来自 `knowledge/user/**/*.md` 和 `memory/user/**/*.md`。
- 如果用户只提供需求文档和可选设计方案文档，并明确要求生成测试设计方案，本 skill 不自动调用 `test-analysis-workflow`；必须失败并提示用户先提供或生成 `test-analysis-solution.json`。
- 如果输入包含 `.docx` 或 `.xlsx`，不得在本 workflow 中转换；必须先由 `@file-normalization-agent` 归一化为 Markdown。
- 新模型不支持旧格式自动迁移；输入分析方案必须符合 schema `2.0`。

## 职责边界

- 本 skill 只负责编排设计链路和写出测试设计方案。
- 测试分析层事实来自已评审测试分析方案；不得把设计阶段发现的新范围直接写成新的 `SC-*` 或 `TP-*`。
- 需求与设计方案只用于校验和补强测试用例依据；不得覆盖分析方案中的已评审层级。
- 强制规则由 `process/rules-pack.json` 独立索引，后续每个阶段必须筛选当前阶段可见的 `ruleSources[]`，读取对应 Markdown 正文并遵守适用 rules。
- `test-design-solution-generation` 负责按每个已冻结 `TP-*` 生成 `test-case-slice`，再合并为 `testCases[]`。
- `test-case-writing` 负责把 canonical JSON 写作为标准 Markdown 或后续扩展的不同交付风格，不改变测试用例事实。
- `test-design-solution-review` 负责独立评审测试用例步骤、测试数据、预期结果依据和分析方案承接。
- `final-report-generation` 负责在 coverage-review 闭环后填写最终人审报告，只展示 FACT 到 SC/TP/TC 的最终覆盖关系，不触发返工。
- 主交付件事实源是 `outputs/runs/<run-id>/deliverables/test-design-solution.json`；人读版由 `test-case-writing` 调用 `bin/render-run-markdown.py` 生成。

## 执行流程

1. 校验输入：识别测试分析方案、Markdown 需求文档和可选 Markdown 设计方案文档。
2. 固定 `PROJECT_ROOT` 和 `<run-id>`；如果显式分析方案位于已有 run 的 `deliverables/test-analysis-solution.json`，优先复用该 run，否则新建或使用用户指定 run。
3. 绑定分析方案输入：
   - 如果用户显式指定 `test-analysis-solution.json`，运行 `python skills/test-design-solution-generation/scripts/bind-analysis-solution.py outputs/runs/<run-id> --analysis <analysis-json>`，将它校验并写入当前 run 的 `deliverables/test-analysis-solution.json`。
   - 如果用户未显式指定，则只检查当前 run 是否已存在 `deliverables/test-analysis-solution.json`。
   - 如果两者都不存在，停止流程并输出失败原因：测试设计必须先取得完整 `test-analysis-solution.json`，本 workflow 不自动生成测试分析方案。
4. 创建或刷新 `process/design-task-list.json`，并通过 `python bin/update-run-task.py outputs/runs/<run-id> --flow design ...` 维护状态；复用分析 run 时不得覆盖 `process/analysis-task-list.json`。
5. 读取并校验 `deliverables/test-analysis-solution.json`；未通过 schema `2.0` 时不进入测试设计生成，直接输出失败原因和“需用当前测试分析 workflow 重新生成分析方案”的建议，不尝试旧格式迁移。
6. 运行 `python skills/test-design-solution-generation/scripts/extract-test-case-work-items.py outputs/runs/<run-id>` 写入 `process/test-case-work-items.json`；每个 `TP-*` 都必须成为独立 TC 生成工作项。
7. 读取或生成 `process/rules-pack.json`；如果缺失，必须调用 `bin/build-rules-pack.py` 生成，不能手工拼写 JSON。
8. 读取或生成 `process/context-pack.json`；如果缺失，必须调用 `context-source-indexing` 脚本生成，不能手工拼写 JSON。
9. 受控补读归一化后的原始需求 Markdown、设计方案 Markdown 或结构化过程记录中与当前分析方案相关的依据。
10. 运行 `python bin/init-staged-slices.py outputs/runs/<run-id> --scope design --pending` 批量初始化带 `generationContext` 的 `process/test-case-slices/<TP-ID>.json`；需要查看状态时运行 `python bin/list-staged-work-items.py outputs/runs/<run-id> --scope design --status all`。
11. 使用 `test-design-solution-generation` 读取当前阶段可见 rules 正文和动态来源正文，只填写当前 TP 切片的 `testPoint.testCases[]`；不得新增、删除、合并或改写 SC/TP。
12. 对每个 TC 切片先运行 `python bin/init-report-artifact.py outputs/runs/<run-id> --kind review --review-type test-case-review --target-id <TP-ID> --force` 初始化评审骨架，再使用 `test-design-solution-review` 独立评审；通过后可运行 `python bin/merge-staged-slices.py outputs/runs/<run-id> --scope design --ids <TP-ID>`，所有切片完成后运行 `python bin/merge-staged-slices.py outputs/runs/<run-id> --scope design --all`，合并进 `deliverables/test-design-solution.json` 并统一全局 `TC-*` 编号。
13. 运行 `bin/lint-run-json.py`；失败时只修正 JSON canonical，不进入 Markdown 写作、最终独立评审或覆盖审查。
14. 使用 `test-case-writing` 将 canonical JSON 写作为标准 Markdown，并运行 `bin/render-run-markdown.py --check` 和 `bin/lint-test-design-solution.py`；失败时回到 `test-design-solution.json` 修正后重新渲染，不手工编辑 Markdown。
15. 运行 `python bin/init-report-artifact.py outputs/runs/<run-id> --kind review --review-type test-design-solution-review --force` 初始化最终评审骨架，再使用 `test-design-solution-review` 独立评审最终测试设计方案 JSON，结果写入 `reports/test-design-solution-review.json`；如发现必须修正的问题，回到第 11 步更新对应 TC 切片。
16. 运行 `python bin/init-report-artifact.py outputs/runs/<run-id> --kind coverage --scope design --force` 初始化 coverage 骨架，再使用 `coverage-review` 检查需求到测试点、测试点到测试用例的覆盖关系，结果写入 `reports/design-coverage-review.json`；如切片 review 或最终 review 存在 blocking findings/issues，先运行 `python bin/apply-review-findings.py outputs/runs/<run-id> --scope design --all` 重开对应工作项；如发现覆盖缺口，必须先运行 `python bin/apply-coverage-gaps.py outputs/runs/<run-id> --scope design`，再按被重开的 `process/test-case-slices/<TP-ID>.json` 修复。不得直接编辑最终 Markdown，也不得跳过切片回写直接手改 `deliverables/test-design-solution.json`；修复后重新执行对应 TC 切片 review、`bin/merge-staged-slices.py`、确定性校验、最终设计 review、coverage-review 和一致性检查。
17. coverage-review 通过且返工闭环完成后，运行 `python bin/build-final-report.py outputs/runs/<run-id> --scope design` 生成 `reports/design-final-report.json` 骨架，再使用 `final-report-generation` 填写 `coveredScenarios[]`、`coveredTestPoints[]`、`coveredTestCases[]`、`coverageStatus` 和 `reviewNote`；填写后再次运行同一脚本重新计算 `summary` 并渲染 `reports/design-final-report.md`。最终报告只供人工审阅，不输出 `coverageGaps[]`，不触发返工。
18. 最终输出前通过 `bin/update-run-task.py` 刷新 `process/design-task-list.json`，运行 `bin/check-staged-run.py outputs/runs/<run-id> --scope design`；失败时输出脚本失败项并修正对应 JSON 或 task-list，不停留在等待状态。

## 按 TP 切片模式

测试设计默认且唯一主路径是按 TP 切片生成。它不改变最终 `test-design-solution.json` 结构，但每次只让模型处理一个已冻结 `TP-*`：

1. `process/test-case-work-items.json` 记录所有 TP 工作项。
2. `process/test-case-slices/<TP-ID>.json` 是单个 TP 的可编辑 TC 骨架。
3. `bin/merge-staged-slices.py --scope design` 合并切片，并重新全局编号 `TC-*`。
4. 所有 TP 工作项完成后，再进入 lint、Markdown render、review 和 coverage。

旧的 design batch 过程产物不属于新流程兼容路径；新 run 不生成、不读取 `design-batch-decision.json`、`design-work-items.json` 或 `design-slices/`。

## 脚本稳定性规则

- design 流程不得临时创建 `.py`、`.js`、`.ps1`、`.bat` 或其他可执行脚本来拼接、修复或拆分 JSON。
- 只能调用仓库固定脚本：`bin/build-rules-pack.py`、`skills/test-design-solution-generation/scripts/bind-analysis-solution.py`、`skills/test-design-solution-generation/scripts/extract-test-case-work-items.py`、`skills/test-design-solution-generation/scripts/init-test-case-slice.py`、`bin/init-staged-slices.py`、`bin/list-staged-work-items.py`、`bin/build-generation-context.py`、`bin/init-report-artifact.py`、`bin/build-final-report.py`、`bin/apply-review-findings.py`、`bin/apply-coverage-gaps.py`、`bin/update-run-task.py`、`skills/test-design-solution-generation/scripts/merge-test-case-slice.py`、`bin/merge-staged-slices.py`、`bin/check-staged-run.py`、`bin/lint-run-json.py`、`bin/render-run-markdown.py`、`bin/lint-test-design-solution.py` 和 `bin/check-artifact-consistency.py`。
- 如果固定脚本能力不足，必须修改仓库 `bin/` 或对应 skill `scripts/` 下的固定脚本并运行校验；不得在 `outputs/`、`process/`、`reports/`、临时目录或当前工作目录写一次性脚本。

## 防卡住规则

- 不调用用户交互能力；除非输入文件不存在或无法访问，否则按上述失败分支自行推进。
- 不为旧 schema、缺少设计方案、缺少错误码/提示文案或动态来源未命中而暂停；旧 schema 阻断并给出重跑建议，其余情况使用输入可支撑的保守预期或记录 review/coverage 说明。
- 不重复运行同一个失败命令超过两次而不修改文件；第二次仍失败时，必须根据失败项修改 JSON、task-list 或相关流程说明。
- 不把 `reports/design-coverage-review.json` 或 `reports/test-design-solution-review.json` 缺失当作等待用户输入；需要时按模板生成结构化结论。历史 `reports/coverage-review.json` 只作为兼容读取路径。

## 输出要求

- 主输出使用 `templates/test-design-solution-json-template.json` 生成 JSON。
- 主输出必须继承分析方案中的 `SC-*` 场景树和 `TP-*` 测试点，不新增、删除、合并或改写分析层级。
- 每个 `TP-*` 必须包含至少 1 个 `TC-*`，但“至少 1 个”只是最低结构门槛，不代表覆盖充分。
- 每个 TP 下应生成覆盖该验证目标所有适用测试设计因子的最小充分 TC 集合；只有当输入依据确实只支持一个独立测试实例时，才允许该 TP 下只有 1 个 TC。
- 生成 TC 前必须先识别当前 TP 的测试设计因子，包括输入条件、等价类、边界点、角色权限、业务状态、配置开关、外部依赖返回、消息顺序、异常类型、接口参数变体、数据组合和预期结果差异。
- `TC-*` 全局连续编号。
- TC 必须保持原子性：一个 TC 只覆盖一个可独立执行、独立判定的测试实例；该原则适用于接口、页面、业务流程、权限、状态、配置、批处理、消息、外部依赖、数据组合和异常处理等所有测试类型。
- 不同输入条件、数据组合、等价类、边界点、角色、权限、状态、配置、外部依赖返回、消息顺序、异常类型或接口参数变体必须拆成独立 TC。
- `steps[]` 只表达同一测试实例内的顺序动作和观察点，不得枚举多个互斥请求、多组替代数据、多种角色/状态/配置切换或多条独立路径。
- 每个 TC 必须包含：
  - `id`
  - `title`
  - `level`，取值为 `Level 0` 到 `Level 4`
  - `preconditions[]`
  - `testData[]`，每项包含 `name`、`value`、`description`
  - `steps[]`，每项包含 `stepNo`、`action`、`expected`
  - `expectedResult`
  - `sourceRefs[]`
- `steps[].action` 只写用户、测试人员、外部调用方或测试工具可执行的操作或取数动作；检查项、断言项、观察结论和系统内部行为写入对应 `steps[].expected`。不得出现 `MM系统判断count=0后取消交易`、`系统返回错误提示`、`服务端释放库存` 这类系统行为动作。
- 接口类 TC 不得写完整裸 URL；必须拆成字段片段。
- 不编造当前用户明确指令、适用 rules、需求、设计方案或分析方案中没有的业务事实、接口、字段、状态、角色、阈值、错误提示或错误码。
- 主输出不得使用 Markdown 加粗语法。
- 全流程不调用用户交互能力，不创建问题队列，不直接向用户提问，不暂停主流程。
