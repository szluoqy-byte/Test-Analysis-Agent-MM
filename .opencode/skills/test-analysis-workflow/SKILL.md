---
name: test-analysis-workflow
description: 当用户提供 Markdown 需求和可选设计方案并要求生成 SC/TP 测试分析方案时，使用 Markdown 过程件完成事实建模、场景与测试点分析，只在阶段边界生成测试分析 JSON。
---

# 测试分析 Workflow

## 何时使用

用于从 Markdown 需求和可选设计方案生成 `SC -> TP` 测试分析方案。Office 输入必须先归一化。若用户直接要求测试用例而没有完整分析方案，不由本 workflow 自动进入测试设计。

## 核心契约

- 模型编写的语义过程件只使用 Markdown，不生成同名 JSON，也不执行 JSON→Markdown 渲染。
- `id-registry.json` 和 TP work-items 是脚本控制状态，模型不得手工编辑。
- 阶段结果只通过 `deliverables/test-analysis-solution.json` 传递；其 Markdown 是结果人读版。
- Review 或 coverage 返工必须回到对应 Markdown 切片，不直接修最终结果 Markdown。

## 输入

- 一份或多份 Markdown 需求文档。
- 可选 Markdown 设计方案。
- 可选 `runid`、`project-key`。

## 执行阶段

- [ ] Step 1: 确定输出目录
- [ ] Step 2: 建立 Markdown 输入上下文
- [ ] Step 3: 完成事实建模与方法分析
- [ ] Step 4: 冻结 Markdown 场景树
- [ ] Step 5: 生成并评审 TP 切片
- [ ] Step 6: 固化分析结果 JSON
- [ ] Step 7: 完成整体语义评审
- [ ] Step 8: 完成覆盖闭环
- [ ] Step 9: 生成最终人审报告
- [ ] Step 10: 校验并结束 run

> 阶段索引是执行契约，不再维护重复的阶段状态文件。

## 各阶段执行要求

### Step 1: 确定输出目录

本阶段不执行 Python、bash 或其他 shell 命令。用户提供 `runid` 时直接使用 `outputs/runs/<runid>/`；未提供时由当前会话按本地时间生成 `<YYYYMMDD-HHMMSS>`，若目录已存在则追加 `-01`、`-02`。`runid` 仍须满足 1-64 位字母、数字、点、下划线和连字符，并以字母或数字开头。目录由后续首次写入按需创建。

若目标目录已经存在 `deliverables/test-analysis-solution.json`，默认停止并改用新 runid，不接受生命周期 mode 或静默覆盖。仅当前 workflow 内部因 review/coverage 返工而重新固化结果时允许复用同一目录。

### Step 2: 建立 Markdown 输入上下文

运行 `bin/build-rules-pack.py` 生成 `process/rules-pack.md`，再运行 `context-source-indexing` 的固定脚本生成 `process/context-pack.md`。按阶段可见性读取其中列出的规则和动态来源正文，不把索引复制成新的 JSON。

### Step 3: 完成事实建模与方法分析

使用 `input-fact-modeling` 直接编写 `process/input-fact-model.md`，FACT 从 `FACT-001` 连续编号。使用 `testing-method-router` 将方法选择、专项分析和补读说明写入 `process/testing-method-routing.md`；这些内容不得进入最终分析 JSON 的 schema。

### Step 4: 冻结 Markdown 场景树

运行 `init-scenario-tree.py` 初始化 `process/scenario-tree.md`，填写最多三层的 `###/####/##### SC-*` 场景树，再运行 `lint-scenario-tree.py`。使用 `test-analysis-solution-review` 编写 `process/reviews/scenario-tree-review.md`；结论通过后不得在 TP 阶段改写 SC。

### Step 5: 生成并评审 TP 切片

运行 `extract-test-point-work-items.py` 生成脚本控制的 `process/test-point-work-items.json`，再用 `bin/init-staged-slices.py --scope analysis --pending` 初始化 `process/test-point-slices/<SC-ID>.md`。逐叶子 SC 填写测试点并在 `process/reviews/test-point-reviews/<SC-ID>.md` 评审。通过后运行 `bin/complete-staged-items.py --scope analysis --ids <SC-ID>`。过程切片不分配 TP 编号。

### Step 6: 固化分析结果 JSON

所有工作项完成后，基于场景树和 TP 切片一次性写出 `deliverables/test-analysis-solution.draft.json`，结构只允许 schema 2.0 的 `SC -> TP`。运行 `python bin/finalize-deliverable.py outputs/runs/<run-id> --scope analysis --draft outputs/runs/<run-id>/deliverables/test-analysis-solution.draft.json` 复用或追加稳定 TP 编号并写入 `deliverables/test-analysis-solution.json/.md`；成功后草稿自动删除。随后运行 JSON lint 和分析方案 Markdown lint；不得把过程 Markdown 反复转换为 JSON。

### Step 7: 完成整体语义评审

使用 `test-analysis-solution-review` 直接编写 `process/reviews/test-analysis-solution-review.md`。若结论为需修正或失败，根据发现项运行 `reopen-run-items.py --scope analysis --ids ...`，修复对应 TP Markdown 切片后重新完成工作项，并以 `finalize-deliverable.py --scope analysis --replace` 重新固化结果。

### Step 8: 完成覆盖闭环

使用 `coverage-review` 基于输入事实和最终分析 JSON 编写 `process/analysis-fact-coverage-map.md` 与 `process/reviews/analysis-coverage-review.md`。缺口返工位置必须指向 TP Markdown 切片；重开、修复、重新评审并重新固化结果后，再更新覆盖 Markdown。

### Step 9: 生成最终人审报告

coverage-review 通过后，使用 `final-report-generation` 从已审查的覆盖 Markdown 编写 `reports/analysis-final-report.md`。报告不生成 JSON，不新增缺口判断，也不触发返工。

### Step 10: 校验并结束 run

运行 `bin/check-staged-run.py --scope analysis`，其中只校验 work-items / ID registry、结果 JSON、结果 Markdown 和语义过程 Markdown 的一致性。无需额外生命周期收尾命令。TestAgent 卡片上报如启用，只消费分析结果 JSON 和最终报告 Markdown；平台失败不影响本地交付。

## 输出

- 结果：`deliverables/test-analysis-solution.json/.md`。
- 最终人审报告：`reports/analysis-final-report.md`。
- 语义过程件：`process/*.md`、`process/test-point-slices/*.md`、`process/reviews/**/*.md`。
- 脚本控制状态：ID registry、TP work-items JSON。

## 约束

- 分析阶段不输出 TC、步骤、测试数据或预期结果。
- 每个叶子 SC 必须包含 `E2E场景测试`。
- 不为过程 Markdown 建立等价 JSON schema；只约定少量标题、编号和表格列。
- 不临时创建脚本处理过程件；固定脚本不足时修改仓库脚本。
