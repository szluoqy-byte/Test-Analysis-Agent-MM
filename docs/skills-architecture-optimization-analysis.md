# Skills 架构优化说明

当前架构采用 JSON canonical + Markdown render，并以 `SC/TP/TC` 作为主交付模型。

## 分层

| 层 | Skill | 职责 | 输出 |
|---|---|---|---|
| 入口编排 | `test-analysis-workflow` | 创建 run、编排分析链路 | `test-analysis-solution.json` |
| 入口编排 | `test-design-workflow` | 复用或创建 run、编排设计链路 | `test-design-solution.json` |
| 强制规则索引 | `bin/build-rules-pack.py` | 索引 core/project/user rules 元数据；后续阶段按 `ruleSources[]` 读取适用规则正文并形成强约束事实 | `rules-pack.json` |
| 生成前工作包 | `bin/build-generation-context.py` / 初始化脚本 | 按阶段把适用 rules 正文、可见动态来源、事实候选和读入计划写入 `generationContext` | process/review/coverage JSON |
| 输入建模 | `input-fact-modeling` | 抽取需求事实、设计事实和来源应用 | `input-fact-model.json` |
| 上下文索引 | `context-source-indexing` | 索引 project/personal knowledge 和 memory 动态来源元数据 | `context-pack.json` |
| 方法路由 | `testing-method-router` | 判断适用测试技术 | 方法参考记录 |
| 分析生成 | `test-analysis-solution-generation` | 先生成冻结 SC 树，再按叶子 SC 生成 TP 切片并合并 | `scenario-tree.json` / 分析方案 |
| 设计生成 | `test-design-solution-generation` | 按每个 `TP-*` 生成 TC 切片并合并 | `test-case-slices/` / 设计方案 |
| 用例写作 | `test-case-writing` | 从 canonical JSON 生成标准 Markdown 或扩展写作风格 | 派生阅读版/导出格式 |
| 独立评审 | review skills | 语义质量评审 | review JSON |
| 覆盖收口 | `coverage-review` | 需求到 TP、TP 到 TC 的覆盖审查 | coverage JSON |
| 返工定位 | `bin/apply-coverage-gaps.py` | 将 coverage gap 定位到具体 slice 并重开 work item | work-items JSON |

## 核心原则

- rules 由 `process/rules-pack.json` 独立索引强制语义，后续阶段必须读取适用 rules 正文。
- core knowledge、templates 和 skill 私有参考由 workflow 或 skill 固定读取。
- project/personal knowledge 和 memory 动态来源只通过 `context-pack.json` 暴露给后续阶段。
- `generationContext` 是生成前工作包：脚本准备上下文，AI 只填当前工作单元的语义内容；它不进入最终 deliverables。
- 分析阶段先冻结 SC 再展开 TP；设计阶段按 TP 展开 TC，且不改写分析层级。
- 确定性结构问题交给 Python 脚本；模型评审只处理语义质量。
- coverage-review 发现覆盖缺口后，必须先运行 `bin/apply-coverage-gaps.py`，通过 `coverageGaps[].artifactLocation` 回到对应 TP/TC 切片修复，再重新执行切片 review、脚本合并、最终 review、coverage 和一致性检查；不得直接编辑最终 Markdown 或绕过切片手改主交付件。
