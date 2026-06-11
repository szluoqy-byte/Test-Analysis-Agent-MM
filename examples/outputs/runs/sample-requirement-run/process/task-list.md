# 测试分析方案任务清单

## 运行标识

- 需求文档：examples/requirements/sample-requirement.md
- 设计方案文档：未提供
- run-id：sample-requirement-run
- PROJECT_ROOT：示例 fixture
- 生成时间：示例固定产物

## 任务列表

| 序号 | 阶段 | 负责 skill | 必须产物/检查点 | 状态 | 证据/路径 |
|---|---|---|---|---|---|
| 1 | 固定 PROJECT_ROOT 与运行目录 | analyze-requirement-test-analysis-solution | outputs/runs/sample-requirement-run/ | done | outputs/runs/sample-requirement-run/ |
| 2 | 构建上下文包 | memory-context-builder | process/context-pack.md、项目知识阶段绑定 | done | process/context-pack.md |
| 3 | 需求可测性分析 | requirement-testability | 结构化需求模型、需求待确认候选 | done | reports/test-analysis-report.md |
| 4 | 设计方案提取 | design-solution-extraction | 设计方案事实摘要、接口/状态/字段/数据依赖清单 | skipped | 未提供设计方案 |
| 5 | 待确认治理 | clarification-gate | CP-INPUT、CP-ANALYSIS、CP-REVIEW、process/clarification-session.md | done | process/clarification-session.md |
| 6 | 测试技术路由 | testing-method-router | 分析维度覆盖表、测试技术路由表、project knowledge 应用记录 | done | reports/test-analysis-report.md |
| 7 | 专项分析 | selected method references | ME-* 方法证据、测试点候选、技术缺口候选 | done | reports/test-analysis-report.md |
| 8 | 按源补读 | selected method references | 按需补读记录、来源说明 | skipped | 示例未触发补读 |
| 10 | 测试分析方案生成 | test-analysis-solution-generation | deliverables/test-analysis-solution.md、project knowledge 应用记录 | done | deliverables/test-analysis-solution.md |
| 11 | 确定性校验 | bin | lint-test-analysis-solution.py 结构校验结果；失败不进入评审 | done | bin/lint-test-analysis-solution.py |
| 12 | 独立评审 | test-analysis-solution-review | 语义覆盖、测试点明细粒度、预期结果依据、事实溯源和非用例化语义 | done | reports/test-analysis-report.md |
| 13 | 覆盖审查 | coverage-review | 需求/方法/rules/project knowledge 应用检查、阻断项；专家评分仅深度评估时执行 | done | reports/test-analysis-report.md |
| 14 | 输出收口 | analyze-requirement-test-analysis-solution | 主交付件路径、过程报告路径、check-artifact-consistency.py 结果 | done | deliverables/test-analysis-solution.md |
