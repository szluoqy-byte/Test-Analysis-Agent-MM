# Skills 架构优化说明

当前架构采用 JSON canonical + Markdown render，并以 `SC/TP/TC` 作为主交付模型。

## 分层

| 层 | Skill | 职责 | 输出 |
|---|---|---|---|
| 入口编排 | `test-analysis-workflow` | 创建 run、编排分析链路 | `test-analysis-solution.json` |
| 入口编排 | `test-design-workflow` | 复用或创建 run、编排设计链路 | `test-design-solution.json` |
| 全流程编排 | `test-analysis-design-workflow` | 优先用独立 subagent 执行分析和设计，通过分析 JSON 显式交接；不支持 subagent 时 fallback 为 workflow 串联 | 分析/设计交付件与 final-report |
| 强制规则索引 | `bin/build-rules-pack.py` | 索引 core/project/user rules 元数据；后续阶段按 `ruleSources[]` 读取适用规则正文并形成强约束事实 | `rules-pack.json` |
| 生成前工作包 | `bin/build-generation-context.py` / 初始化脚本 | 按阶段把适用 rules 正文、可见动态来源、事实候选和读入计划写入 `generationContext` | process/review/coverage JSON |
| 输入建模 | `input-fact-modeling` | 抽取需求事实、设计事实和来源应用 | `input-fact-model.json` |
| 上下文索引 | `context-source-indexing` | 索引 project/personal knowledge 和 memory 动态来源元数据 | `context-pack.json` |
| 方法路由 | `testing-method-router` | 判断适用测试技术 | 方法参考记录 |
| 分析生成 | `test-analysis-solution-generation` | 先生成冻结 SC 树，再按叶子 SC 生成 TP 切片并合并 | `scenario-tree.json` / 分析方案 |
| 设计生成 | `test-design-solution-generation` | 按每个 `TP-*` 生成 TC 切片并合并 | `test-case-slices/` / 设计方案 |
| 分段机械操作 | `bin/list-staged-work-items.py` / `bin/init-staged-slices.py` / `bin/merge-staged-slices.py` / `bin/check-staged-run.py` | 状态查看、批量初始化、批量合并和固定检查，避免临时脚本处理 JSON | work-items / slice / checks |
| 用例写作 | `test-case-writing` | 从 canonical JSON 生成标准 Markdown 或扩展写作风格 | 派生阅读版/导出格式 |
| 独立评审 | review skills | 语义质量评审 | review JSON |
| 覆盖证据图 | `bin/build-fact-coverage-map.py` | 逐 FACT 整理到 SC/TP/TC 的候选覆盖链路，供 coverage-review 审查 | fact-coverage-map JSON/Markdown |
| 覆盖收口 | `coverage-review` | 基于 fact-coverage-map 执行需求到 TP、TP 到 TC 的覆盖门禁 | coverage JSON |
| 最终人审报告 | `final-report-generation` / `bin/build-final-report.py` | 从已审查的 fact-coverage-map 展示 FACT 最终被哪些 SC/TP/TC 覆盖，不触发返工 | final-report JSON/Markdown |
| 返工定位 | `bin/apply-review-findings.py` / `bin/apply-coverage-gaps.py` | 将 review blocking 或 coverage gap 定位到具体 slice 并重开 work item | work-items JSON |

## 核心原则

- rules 由 `process/rules-pack.json` 独立索引强制语义，后续阶段必须读取适用 rules 正文。
- core knowledge、templates 和 skill 私有参考由 workflow 或 skill 固定读取。
- project/personal knowledge 和 memory 动态来源只通过 `context-pack.json` 暴露给后续阶段。
- `generationContext` 是生成前工作包：脚本准备上下文，AI 只填当前工作单元的语义内容；它不进入最终 deliverables。
- 分析阶段先冻结 SC 再展开 TP；设计阶段按 TP 展开 TC，且不改写分析层级。
- 确定性结构问题交给 Python 脚本；模型评审只处理语义质量。
- review 发现 blocking 或 coverage-review 发现覆盖缺口后，必须先运行 `bin/apply-review-findings.py` 或 `bin/apply-coverage-gaps.py`，通过结构化 location 回到对应 TP/TC 切片修复，再重新执行切片 review、脚本合并、最终 review、fact-coverage-map、coverage 和一致性检查；不得直接编辑最终 Markdown、绕过切片手改主交付件或临时创建脚本处理 JSON。
- final-report 是最终人审件，位于 coverage-review 通过并返工闭环之后；它只从已审查的 fact-coverage-map 展示输入 FACT 与最终 SC/TP/TC 覆盖关系，不输出 `coverageGaps[]`，不参与自动返工链路。
- e2e 全流程推荐 subagent-first：analysis 和 design 放入独立会话以降低上下文互相影响；workflow skill 仍是执行契约，阶段交接只依赖 canonical JSON 和固定报告文件。
