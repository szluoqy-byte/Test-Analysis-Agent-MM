# 测试用例标题大纲任务清单

## 运行标识

- 需求文档：examples/requirements/sample-requirement.md
- 设计方案文档：未提供
- run-id：sample-requirement-run
- PROJECT_ROOT：examples fixture
- 生成时间：fixture

## 任务列表

| 序号 | 阶段 | 负责 skill | 必须产物/检查点 | 状态 | 证据/路径 |
|---|---|---|---|---|---|
| 1 | 固定 PROJECT_ROOT 与运行目录 | analyze-requirement-testcase-outline | outputs/runs/sample-requirement-run/ | done | examples/outputs/runs/sample-requirement-run/ |
| 2 | 构建上下文包 | memory-context-builder | process/context-pack.md | done | process/context-pack.md |
| 3 | 需求可测性分析 | requirement-testability | 结构化需求模型、需求待确认候选 | done | reports/test-analysis-report.md |
| 4 | 设计方案提取 | analyze-requirement-testcase-outline | 设计方案事实摘要、接口/状态/字段/数据依赖清单 | skipped | 示例 fixture 未提供独立设计方案 |
| 5 | 待确认治理 | clarification-gate | CP-INPUT、CP-ANALYSIS、CP-REVIEW | done | deliverables/testcase-title-outline.md#5-待确认信息 |
| 6 | 测试技术路由 | testing-method-router | 分析维度覆盖表、测试技术路由表 | done | reports/test-analysis-report.md |
| 7 | 专项分析 | selected method skills | ME-* 方法证据、测试点候选、技术缺口候选 | done | reports/test-analysis-report.md |
| 8 | 按源补读 | selected method skills | 按需补读记录、来源说明 | skipped | 示例 fixture 未触发 project/user 按源补读 |
| 9 | 场景化测试点生成 | testpoint-generation | 场景、测试点、接口测试点 | done | deliverables/testcase-title-outline.md |
| 10 | 测试用例标题大纲生成 | testcase-title-outline-generation | deliverables/testcase-title-outline.md | done | deliverables/testcase-title-outline.md |
| 11 | 覆盖审查 | coverage-review | 门禁结果、专家评分、阻断项 | done | reports/test-analysis-report.md |
| 12 | 确定性校验 | coverage-review / bin | lint、consistency、semantic 检查结果 | done | bin/smoke-test-analysis.py |
| 13 | 输出收口 | analyze-requirement-testcase-outline | 主交付件路径、过程报告路径、最终待确认信息 | done | deliverables/testcase-title-outline.md |
