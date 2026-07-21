---
name: test-design-workflow
description: 当用户提供已评审测试分析方案并要求扩展 TC 测试用例时使用；该 skill 编排测试分析方案校验、依据补读、测试设计方案 JSON 生成、写作渲染和独立评审。
---

# 测试分析方案到测试设计方案主入口

本 skill 是 `test-design-agent` 的完整链路入口。目标是从 `$ARGUMENTS` 指定的已评审 `测试分析方案` 出发，生成 `测试设计方案`。

测试设计方案回答 how to test：继承 `SC-*` 场景树和 `TP-*` 测试点，并在每个测试点下生成完整步骤级 `TC-*` 测试用例。

## 必需输入

- `$ARGUMENTS`：可显式指定一份 `test-analysis-solution.json`；若指定，必须优先使用该文件。
- 可选：原始需求文档路径、设计方案文档路径或 `project=<project-key>`；personal rules 来自 `rules/user/**/*.md`，personal 动态补充来源来自 `knowledge/user/**/*.md`。
- 可选 `runid=<requirement-id>` 和 `mode=auto|resume|extend|rebuild`；指定已有 run 时优先继承 manifest 输入和同一 run 下的分析方案。
- 如果用户只提供需求文档和可选设计方案文档，并明确要求生成测试设计方案，本 skill 不自动调用 `test-analysis-workflow`；必须失败并提示用户先提供或生成 `test-analysis-solution.json`。
- 如果输入包含 `.docx` 或 `.xlsx`，不得在本 workflow 中转换；必须先由 `@file-normalization-agent` 归一化为 Markdown。
- 新模型不支持旧格式自动迁移；输入分析方案必须符合 schema `2.0`。

## 执行阶段

- [ ] Step 1: 准备持久 run 并绑定完整分析方案
- [ ] Step 2: 初始化设计任务、工作项和共享上下文
- [ ] Step 3: 初始化并填写当前 TP 的 TC 切片
- [ ] Step 4: 评审并合并 TC 切片
- [ ] Step 5: 执行确定性校验和 Markdown 写作
- [ ] Step 6: 执行最终设计评审与 coverage 闭环
- [ ] Step 7: 生成设计最终报告
- [ ] Step 8: 收口 run 并固化生命周期状态
- [ ] Step 9: 上报测试用例卡片至testagent

> 阶段索引是静态执行契约，不表示本次 run 的实时完成状态。实时状态只写入 `process/design-task-list.json`。

## 职责边界

- 本 skill 只负责编排设计链路和写出测试设计方案。
- 测试分析层事实来自已评审测试分析方案；不得把设计阶段发现的新范围直接写成新的 `SC-*` 或 `TP-*`。
- 需求与设计方案只用于校验和补强测试用例依据；不得覆盖分析方案中的已评审层级。
- 强制规则由 `process/rules-pack.json` 独立索引，后续每个阶段必须筛选当前阶段可见的 `ruleSources[]`，读取对应 Markdown 正文并遵守适用 rules。
- `test-design-solution-generation` 负责按每个已冻结 `TP-*` 生成 `test-case-slice`，再合并为 `testCases[]`。
- `test-case-writing` 负责把 canonical JSON 写作为标准 Markdown 或后续扩展的不同交付风格，不改变测试用例事实。
- `test-design-solution-review` 负责独立评审测试用例步骤、测试数据、预期结果依据和分析方案承接。
- `coverage-review` 负责基于 `process/design-fact-coverage-map.json` 执行 FACT 到 SC/TP/TC 的覆盖门禁。
- `final-report-generation` 负责在 coverage-review 闭环后基于已审查的覆盖证据图生成最终人审报告，只展示 FACT 到 SC/TP/TC 的最终覆盖关系，不触发返工。
- 主交付件事实源是 `outputs/runs/<run-id>/deliverables/test-design-solution.json`；人读版由 `test-case-writing` 调用 `bin/render-run-markdown.py` 生成。

## 易错点

- 不要在缺少完整 `test-analysis-solution.json` 时自动运行分析；设计 workflow 只能绑定已有分析 JSON 或失败退出。
- 不要依赖碎片化 TP 输入作为用户入口；设计阶段以完整分析方案为事实源。
- 不要在设计阶段新增、删除、合并或改写 SC/TP；只能填写当前 TP 的 TC 切片。
- 不要把“每个 TP 至少 1 个 TC”当成充分覆盖；必须识别必选因子、候选因子和基于 TP 目标补充推导的必要因子，再生成最小充分 TC 集合。已加载来源中的既有测试设计因子是必选覆盖项或启发来源，不是封闭上限。
- 不要绕过 run plan 直接覆盖已有设计；analysis hash、输入/context/framework 指纹变化时必须重开受影响 TP，失败退出前释放 run lock。

## 各阶段执行要求

### Step 1: 准备持久 run 并绑定完整分析方案

1. 校验输入：识别测试分析方案、Markdown 需求文档和可选 Markdown 设计方案文档。
2. 固定 `PROJECT_ROOT`，把 `runid`、`mode`、project、requirement/design 和 `remove-source` 参数传给 `python bin/manage-run.py prepare --flow design ...`。未显式 runid 且 analysis 位于已有 run 时使用该 run 的目录名。读取 `process/run-plan.json`：`reuse` 只做一致性检查并返回；其他 action 持锁继续，`extend/rebuild` 必须已有 revision 快照。
3. 绑定分析方案输入：
   - 如果用户显式指定 `test-analysis-solution.json`，运行 `python skills/test-design-solution-generation/scripts/bind-analysis-solution.py outputs/runs/<run-id> --analysis <analysis-json>`，将它校验并写入当前 run 的 `deliverables/test-analysis-solution.json`。
   - 如果用户未显式指定，则只检查当前 run 是否已存在 `deliverables/test-analysis-solution.json`。
   - 如果两者都不存在，停止流程并输出失败原因：测试设计必须先取得完整 `test-analysis-solution.json`，本 workflow 不自动生成测试分析方案。
4. 运行 `python bin/update-run-task.py outputs/runs/<run-id> --flow design --stage 固定 PROJECT_ROOT 与运行目录 --action start --evidence outputs/runs/<run-id>/` 创建或补齐 `process/design-task-list.json`，后续继续用同一脚本维护阶段状态；复用分析 run 时不得覆盖 `process/analysis-task-list.json`。
5. 以 `--stage 测试分析方案校验 --action start` 更新任务清单后，读取并校验 `deliverables/test-analysis-solution.json`；未通过 schema `2.0` 时不进入测试设计生成，直接输出失败原因和“需用当前测试分析 workflow 重新生成分析方案”的建议，不尝试旧格式迁移。通过后以该 JSON 为证据标记 `测试分析方案校验` 为 `done`，并以 `process/run-plan.json` 为证据标记 `固定 PROJECT_ROOT 与运行目录` 为 `done`。

### Step 2: 初始化设计任务、工作项和共享上下文

6. 运行 `python skills/test-design-solution-generation/scripts/extract-test-case-work-items.py outputs/runs/<run-id>` 写入 `process/test-case-work-items.json`；每个 `TP-*` 都必须成为独立 TC 生成工作项。TP 内容 hash 变化会自动重开；analysis hash、design framework 或上下文变化时按 `run-plan.json` 使用 `bin/reopen-run-items.py --scope design` 重开受影响 TP，无法可靠定位时重开全部。
7. 以 `--stage 强制规则加载 --action start` 更新任务清单后，读取或生成 `process/rules-pack.json`；如果缺失，必须调用 `bin/build-rules-pack.py` 生成，不能手工拼写 JSON。成功后以 `process/rules-pack.json` 为证据标记 `强制规则加载` 为 `done`。
8. 以 `--stage 上下文来源索引 --action start` 更新任务清单后，读取或生成 `process/context-pack.json`；如果缺失，必须调用 `context-source-indexing` 脚本生成，不能手工拼写 JSON。成功后以 `process/context-pack.json` 为证据标记 `上下文来源索引` 为 `done`。
9. 以 `--stage 设计依据补读 --action start` 更新任务清单后，受控补读 `process/run-manifest.json` 中全部可用 requirement/design 输入和结构化过程记录中与当前分析方案相关的依据；本次未重复传入的历史输入仍然有效，除非已通过 `remove-source` 显式删除。完成补读后以补读记录标记该阶段为 `done`；没有新增补读需要时必须显式标记为 `skipped`。

### Step 3: 初始化并填写当前 TP 的 TC 切片

10. 以 `--stage 测试设计方案生成 --action start` 更新任务清单后，运行 `python bin/init-staged-slices.py outputs/runs/<run-id> --scope design --pending` 批量初始化带 `generationContext` 的 `process/test-case-slices/<TP-ID>.json`；需要查看状态时运行 `python bin/list-staged-work-items.py outputs/runs/<run-id> --scope design --status all`。
11. 使用 `test-design-solution-generation` 读取当前阶段可见 rules 正文和动态来源正文，只填写当前 TP 切片的 `testPoint.testCases[]`；不得新增、删除、合并或改写 SC/TP。

### Step 4: 评审并合并 TC 切片

12. 对每个 TC 切片先运行 `python bin/init-report-artifact.py outputs/runs/<run-id> --kind review --review-type test-case-review --target-id <TP-ID> --force` 初始化评审骨架，再使用 `test-design-solution-review` 独立评审；JSON 写入后立即运行 `python bin/render-run-markdown.py outputs/runs/<run-id> --artifact process/reviews/test-case-reviews/<TP-ID>.json`，通过后运行 `python bin/merge-staged-slices.py outputs/runs/<run-id> --scope design --ids <TP-ID>`。全部 TP 合并后，以 `deliverables/test-design-solution.json`、`process/test-case-work-items.json` 和切片评审结果为证据标记 `测试设计方案生成` 为 `done`。合并器先按最新 analysis 对齐 SC/TP，并保留既有 TC 编号；新增 TC 从历史最大编号后追加，退役编号不复用。

### Step 5: 执行确定性校验和 Markdown 写作

13. 以 `--stage 确定性校验 --action start` 更新任务清单后，运行 `bin/lint-run-json.py`；失败时只修正 JSON canonical，不进入 Markdown 写作、最终独立评审或覆盖审查。
14. 使用 `test-case-writing` 将 canonical JSON 写作为标准 Markdown，并运行 `python bin/render-run-markdown.py outputs/runs/<run-id> --check` 和 `python bin/lint-test-design-solution.py outputs/runs/<run-id>/deliverables/test-design-solution.md`；失败时回到 `test-design-solution.json` 修正后重新渲染，不手工编辑 Markdown。通过后以 lint 与渲染结果为证据标记 `确定性校验` 为 `done`。

### Step 6: 执行最终设计评审与 coverage 闭环

15. 以 `--stage 独立评审 --action start` 更新任务清单。运行 `python bin/init-report-artifact.py outputs/runs/<run-id> --kind review --review-type test-design-solution-review --force` 初始化最终评审骨架，再使用 `test-design-solution-review` 独立评审最终测试设计方案 JSON，结果写入 `process/reviews/test-design-solution-review.json`；如发现必须修正的问题，回到 Step 3 的操作 11 更新对应 TC 切片。JSON 写入后立即运行 `python bin/render-run-markdown.py outputs/runs/<run-id> --artifact process/reviews/test-design-solution-review.json`，再以该 JSON、Markdown 和评审结论为证据标记 `独立评审` 为 `done`。
16. 以 `--stage 覆盖审查 --action start` 更新任务清单。运行 `python bin/build-fact-coverage-map.py outputs/runs/<run-id> --scope design` 生成 `process/design-fact-coverage-map.json` 骨架；使用 `coverage-review` 前必须读取 `skills/coverage-review/references/fact-coverage-tree-contract.md`，逐 FACT 填写或修正既有行的 `coverageTree[]`、`coverageStatus` 和 `coverageReason`。design 的 `coverageStatus=covered` 链路固定为 `leafScenarioId -> testPoints[].testPointId -> testCases: [TC-*]`，且至少关联一个真实 TC；`gap` 或 `not_applicable` 必须使用空 `coverageTree[]`。修改后立即运行 `python bin/render-run-markdown.py outputs/runs/<run-id> --artifact process/design-fact-coverage-map.json`，再运行 `python bin/lint-run-json.py outputs/runs/<run-id>`。
17. 运行 `python bin/init-report-artifact.py outputs/runs/<run-id> --kind coverage --scope design --force` 初始化 coverage 骨架，再使用 `coverage-review` 基于 `process/design-fact-coverage-map.json` 检查需求到测试点、测试点到测试用例的覆盖关系，结果写入 `process/reviews/design-coverage-review.json`；JSON 写入后立即运行 `python bin/render-run-markdown.py outputs/runs/<run-id> --artifact process/reviews/design-coverage-review.json`，再运行 `python bin/lint-run-json.py outputs/runs/<run-id>`。如切片 review 或最终 review 存在 blocking findings/issues，先运行 `python bin/apply-review-findings.py outputs/runs/<run-id> --scope design --all` 重开对应工作项；如发现覆盖缺口，必须先运行 `python bin/apply-coverage-gaps.py outputs/runs/<run-id> --scope design`，再按被重开的 `process/test-case-slices/<TP-ID>.json` 修复。不得直接编辑最终 Markdown，也不得跳过切片回写直接手改 `deliverables/test-design-solution.json`；修复后重新执行对应 TC 切片 review、`bin/merge-staged-slices.py`、确定性校验、最终设计 review、`bin/build-fact-coverage-map.py`、coverage-review 和一致性检查；每次写入 review 或 coverage JSON 后都必须先渲染其对应 Markdown，再运行现有 lint。coverage-review 通过后以覆盖图、coverage review JSON/Markdown 和 lint 结果为证据标记 `覆盖审查` 为 `done`。

### Step 7: 生成设计最终报告

18. 只有 `process/design-fact-coverage-map.json` 与 `process/reviews/design-coverage-review.json` 已完成 JSON 写入、Markdown 渲染并通过现有 lint 后，coverage-review 才可视为通过。之后使用 `final-report-generation` 运行 `python bin/build-final-report.py outputs/runs/<run-id> --scope design`，从 `process/design-fact-coverage-map.json` 生成 `reports/design-final-report.json` 并渲染 `reports/design-final-report.md`。最终报告只供人工审阅，不输出 `coverageGaps[]`，不触发返工。
19. 通过 `bin/update-run-task.py` 将 `process/design-task-list.json` 的 `最终报告生成` 阶段标记为 done，证据必须包含 `reports/design-final-report.json` 和 `reports/design-final-report.md`。

### Step 8: 收口 run 并固化生命周期状态

20. 最终输出前以 `deliverables/test-design-solution.json`、`reports/design-final-report.json` 和对应 Markdown 为证据标记 `输出收口` 为 `done`，再运行 `bin/check-staged-run.py outputs/runs/<run-id> --scope design`；通过后运行 `python bin/manage-run.py finalize outputs/runs/<run-id> --flow design`，记录 design hash 和它使用的 analysis hash。失败退出前运行 `python bin/manage-run.py abort outputs/runs/<run-id> --flow design` 释放锁。

### Step 9: 上报测试用例卡片至testagent

21. 先cd进入到skills/test-design-workflow/scripts路径，然后调用 `python card_generate.py "<designjson-file-path>" "<cidainfo-file-path>" "<designreport-file-path>"` 上报测试点生成卡片至 TestAgent 平台，注意python脚本不能包含路径，只能是python文件名称card_generate.py。先进入脚本所在目录，再重新执行python脚本。其中 `<designjson-file-path>` 为 `deliverables/test-design-solution.json` 的绝对路径字符串（例如 `D:\...\outputs\runs\<run-id>\deliverables\test-design-solution.json`）。`<cidainfo-file-path>`为 `deliverables/cloud_test_info.json` 的绝对路径字符串（例如 `D:\...\outputs\runs\<run-id>\deliverables\cloud_test_info.json`）。 `<designreport-file-path>`为 `reports/design-final-report.md` 的绝对路径字符串（例如 `D:\...\outputs\runs\<run-id>\reports\design-final-report.md`）。若 TestAgent 平台 API 不可用导致上报失败，不影响分析方案交付件本身。

## 按 TP 切片模式

测试设计默认且唯一主路径是按 TP 切片生成。它不改变最终 `test-design-solution.json` 结构，但每次只让模型处理一个已冻结 `TP-*`：

1. `process/test-case-work-items.json` 记录所有 TP 工作项。
2. `process/test-case-slices/<TP-ID>.json` 是单个 TP 的可编辑 TC 骨架。
3. `bin/merge-staged-slices.py --scope design` 合并切片，保留既有 `TC-*` 并为新增用例追加稳定编号。
4. 所有 TP 工作项完成后，再进入 lint、Markdown render、review 和 coverage。

旧的 design batch 过程产物不属于新流程兼容路径；新 run 不生成、不读取 `design-batch-decision.json`、`design-work-items.json` 或 `design-slices/`。

## 脚本稳定性规则

- design 流程不得临时创建 `.py`、`.js`、`.ps1`、`.bat` 或其他可执行脚本来拼接、修复或拆分 JSON。
- 只能调用仓库固定脚本：`bin/manage-run.py`、`bin/reopen-run-items.py`、`bin/build-rules-pack.py`、`skills/test-design-solution-generation/scripts/bind-analysis-solution.py`、`skills/test-design-solution-generation/scripts/extract-test-case-work-items.py`、`skills/test-design-solution-generation/scripts/init-test-case-slice.py`、`bin/init-staged-slices.py`、`bin/list-staged-work-items.py`、`bin/build-generation-context.py`、`bin/init-report-artifact.py`、`bin/build-fact-coverage-map.py`、`bin/build-final-report.py`、`bin/apply-review-findings.py`、`bin/apply-coverage-gaps.py`、`bin/update-run-task.py`、`skills/test-design-solution-generation/scripts/merge-test-case-slice.py`、`bin/merge-staged-slices.py`、`bin/check-staged-run.py`、`bin/lint-run-json.py`、`bin/render-run-markdown.py`、`bin/lint-test-design-solution.py` 和 `bin/check-artifact-consistency.py`。
- 正常 design run 不得调用 `bin/sync-opencode-skills.py`、`bin/validate-agent-runtime.py` 或 `bin/smoke-test-analysis.py`；它们是仓库开发校验，不属于本 workflow。
- 如果固定脚本能力不足，必须修改仓库 `bin/` 或对应 skill `scripts/` 下的固定脚本并运行校验；不得在 `outputs/`、`process/`、`reports/`、临时目录或当前工作目录写一次性脚本。

## 防卡住规则

- 不调用用户交互能力；除非输入文件不存在或无法访问，否则按上述失败分支自行推进。
- 不为旧 schema、缺少设计方案、缺少错误码/提示文案或动态来源未命中而暂停；旧 schema 阻断并给出重跑建议，其余情况使用输入可支撑的保守预期或记录 review/coverage 说明。
- 不重复运行同一个失败命令超过两次而不修改文件；第二次仍失败时，必须根据失败项修改 JSON、task-list 或相关流程说明。
- 不把 `process/reviews/design-coverage-review.json` 或 `process/reviews/test-design-solution-review.json` 缺失当作等待用户输入；需要时按模板生成结构化结论。

## 输出要求

- 当前 TP 的 `process/test-case-slices/<TP-ID>.json` 是唯一 live template；模型只填写 `testPoint.testCases[]`，主交付件由固定合并脚本生成，不读取或套用完整 `templates/test-design-solution-json-template.json`。
- 主输出必须继承分析方案中的 `SC-*` 场景树和 `TP-*` 测试点，不新增、删除、合并或改写分析层级。
- 每个 `TP-*` 必须包含至少 1 个 `TC-*`，但“至少 1 个”只是最低结构门槛，不代表覆盖充分。
- 每个 TP 下应生成覆盖该验证目标所有适用测试设计因子的最小充分 TC 集合；只有当输入依据、业务不变量和模型测试经验都不能支持额外独立因子拆分时，才允许该 TP 下只有 1 个 TC。
- 生成 TC 前必须先识别当前 TP 的测试设计因子，包括输入条件、等价类、边界点、角色权限、业务状态、配置开关、外部依赖返回、消息顺序、异常类型、接口参数变体、数据组合和预期结果差异。
- 已加载来源中的既有测试设计因子必须按强制性处理：rules、当前用户明确指令和输入文档明确事实中的因子是必选覆盖项；knowledge、project/personal 动态来源和方法参考中的因子是重要候选与启发，需要结合当前 TP 判断适用性。除非更高优先级指令明确限定仅使用指定因子集合，否则既有因子不是封闭上限，必须继续补充该 TP 下有判定意义的必要测试实例。
- `TC-*` 在 run 内全局唯一且增量稳定；既有编号保持不变，新编号追加且退役编号不复用。
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
