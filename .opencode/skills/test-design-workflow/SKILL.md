---
name: test-design-workflow
description: 当用户提供已评审 schema 2.0 测试分析 JSON 并要求生成 SC/TP/TC 测试设计方案时，使用 Markdown TC 切片完成设计，只在阶段边界生成测试设计 JSON。
---

# 测试设计 Workflow

## 何时使用

用于把完整 `test-analysis-solution.json` 扩展为 `SC -> TP -> TC`。本 workflow 不自动运行测试分析；缺少分析 JSON 时停止并要求先完成分析或使用全流程 workflow。

## 核心契约

- TC 生成、评审和覆盖过程件使用 Markdown。
- 测试分析 JSON 是结构化输入，测试设计 JSON 是结构化输出。
- TC work-items 和 ID registry 是脚本控制 JSON，模型不得编辑。
- 返工只修改 TC Markdown 切片，再重新固化最终结果。

## 执行阶段

- [ ] Step 1: 确定输出目录与分析结果
- [ ] Step 2: 加载 Markdown 上下文
- [ ] Step 3: 建立 TC 工作项
- [ ] Step 4: 生成并评审 TC 切片
- [ ] Step 5: 固化设计结果 JSON
- [ ] Step 6: 完成整体语义评审
- [ ] Step 7: 完成覆盖闭环与最终报告
- [ ] Step 8: 校验并结束 run

> 阶段索引是执行契约，不再维护重复的阶段状态文件。

## 各阶段执行要求

### Step 1: 确定输出目录与分析结果

本阶段不执行 Python、bash 或其他 shell 命令。先确定完整 `test-analysis-solution.json`：用户显式指定时直接使用该路径；未指定时读取 `outputs/runs/<runid>/deliverables/test-analysis-solution.json`。如果分析结果本身位于某个 run 的 `deliverables/`，默认复用该 run；否则按用户提供的 `runid` 选择目录，仍未提供时生成时间戳 runid。

不复制或绑定分析 JSON，后续工作项直接记录其来源路径。若目标目录已存在 `deliverables/test-design-solution.json`，默认停止并改用新 runid；只有当前 workflow 内部返工重新固化时才允许替换。

### Step 2: 加载 Markdown 上下文

读取或生成 `process/rules-pack.md` 和 `process/context-pack.md`，补读用户提供的需求、设计输入以及分析 JSON。规则正文按阶段可见性读取；不生成 rules/context JSON 副本。

### Step 3: 建立 TC 工作项

运行 `extract-test-case-work-items.py outputs/runs/<run-id> --analysis <analysis-json>` 校验分析结果并生成 `process/test-case-work-items.json`；该控制文件记录真实分析来源。再运行 `bin/init-staged-slices.py --scope design --pending` 初始化每个 `process/test-case-slices/<TP-ID>.md`。

### Step 4: 生成并评审 TC 切片

使用 `test-design-solution-generation` 逐 TP 填写 Markdown TC 切片，识别必选与必要测试因子并形成最小充分 TC 集。使用 `test-design-solution-review` 编写 `process/reviews/test-case-reviews/<TP-ID>.md`；通过后运行 `complete-staged-items.py --scope design --ids <TP-ID>`。过程切片不分配 TC 编号。

### Step 5: 固化设计结果 JSON

所有 TP 工作项完成后，基于分析 JSON 和 TC 切片一次性写出 `deliverables/test-design-solution.draft.json`。运行 `finalize-deliverable.py --scope design --draft outputs/runs/<run-id>/deliverables/test-design-solution.draft.json`，复用或追加稳定 TC 编号并生成 `deliverables/test-design-solution.json/.md`；成功后草稿自动删除。设计结果必须完整继承分析 SC/TP。

### Step 6: 完成整体语义评审

直接编写 `process/reviews/test-design-solution-review.md`。存在 blocking 问题时用 `reopen-run-items.py --scope design --ids ...` 重开 TP，修复 TC Markdown 切片、重新完成工作项，并以 `finalize-deliverable.py --scope design --replace` 重新固化设计结果。

### Step 7: 完成覆盖闭环与最终报告

使用 `coverage-review` 编写 `process/design-fact-coverage-map.md` 与 `process/reviews/design-coverage-review.md`，covered 链路必须包含真实 TC。覆盖通过后使用 `final-report-generation` 编写 `reports/design-final-report.md`；报告不生成 JSON。

### Step 8: 校验并结束 run

运行 `bin/check-staged-run.py --scope design`。无需额外生命周期收尾命令。TestAgent 卡片上报如启用，只消费设计结果 JSON 和最终报告 Markdown；平台失败不影响本地交付。

## 输出

- 结果：`deliverables/test-design-solution.json/.md`。
- 最终人审报告：`reports/design-final-report.md`。
- 过程：TC slices、reviews、coverage 均为 Markdown。
- 控制：TC work-items 和 ID registry 为 JSON。

## 约束

- 不把“每个 TP 一个 TC”当作充分覆盖。
- GUI/API/CLI 用例遵守对应写作风格；action 只写可执行动作，检查要求写 expected。
- 不为过程 Markdown 建立复杂解析 schema，不生成过程 JSON 镜像。
