# 测试设计方案任务清单

## 运行标识

- 需求文档：examples/requirements/sample-requirement.md
- 设计方案文档：未提供
- run-id：sample-requirement-run
- PROJECT_ROOT：示例 fixture
- 生成时间：示例固定产物

## 任务列表

| 序号 | 阶段 | 负责 skill | 必须产物/检查点 | 状态 | 证据/路径 |
|---|---|---|---|---|---|
| 1 | 固定 PROJECT_ROOT 与运行目录 | test-design-workflow | outputs/runs/sample-requirement-run/ | done | outputs/runs/sample-requirement-run/ |
| 2 | 测试分析方案校验 | test-design-workflow | deliverables/test-analysis-solution.json | done | deliverables/test-analysis-solution.json |
| 3 | 强制规则加载 | bin/build-rules-pack.py | process/rules-pack.json、core/project/user rules 强制规则包 | done | process/rules-pack.json |
| 4 | 上下文来源索引 | context-source-indexing | process/context-pack.json | done | process/context-pack.json |
| 5 | 设计依据补读 | test-design-workflow | 归一化需求与测试分析方案 | done | examples/requirements/sample-requirement.md |
| 6 | 测试设计方案生成 | test-design-solution-generation | deliverables/test-design-solution.json | done | deliverables/test-design-solution.json |
| 7 | 确定性校验 | lint-run-json/render-run-markdown/lint-test-design-solution | JSON 与 Markdown 校验 | done | bin/smoke-test-analysis.py |
| 8 | 独立评审 | test-design-solution-review | reports/test-design-solution-review.json | done | bin/smoke-test-analysis.py |
| 9 | 覆盖审查 | coverage-review | reports/design-coverage-review.json | done | bin/check-artifact-consistency.py |
| 10 | 输出收口 | test-design-workflow | check-artifact-consistency | done | bin/check-artifact-consistency.py |
