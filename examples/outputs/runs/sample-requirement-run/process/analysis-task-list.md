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
| 1 | 固定 PROJECT_ROOT 与运行目录 | test-analysis-workflow | outputs/runs/sample-requirement-run/ | done | outputs/runs/sample-requirement-run/ |
| 2 | 强制规则加载 | bin/build-rules-pack.py | process/rules-pack.json、core/project/user rules 强制规则索引 | done | process/rules-pack.json |
| 3 | 上下文来源索引 | context-source-indexing | process/context-pack.json、动态 project/personal knowledge/memory 来源索引 | done | process/context-pack.json |
| 4 | 输入事实建模 | input-fact-modeling | process/input-fact-model.json、事实清单、需求-设计映射 | done | process/input-fact-model.json |
| 5 | 测试技术路由 | testing-method-router | 分析维度覆盖表、测试技术路由表、动态来源应用记录 | done | process/input-fact-model.json；process/rules-pack.json；process/context-pack.json |
| 6 | 专项分析 | testing-method-router | 覆盖维度建议、测试点候选、补读记录 | done | deliverables/test-analysis-solution.json |
| 7 | 按源补读 | testing-method-router | 按需补读记录、来源说明 | skipped | 示例未触发补读 |
| 8 | 测试分析方案生成 | test-analysis-solution-generation | process/scenario-tree.json、process/test-point-work-items.json、process/test-point-slices/{SC-ID}.json、deliverables/test-analysis-solution.json | done | deliverables/test-analysis-solution.json |
| 9 | 确定性校验 | bin | lint-run-json.py、render-run-markdown.py、lint-test-analysis-solution.py 结果；失败不进入评审 | done | bin/lint-run-json.py；bin/render-run-markdown.py；bin/lint-test-analysis-solution.py |
| 10 | 独立评审 | test-analysis-solution-review | 语义覆盖、测试点粒度、依据质量、事实溯源和分析边界 | done | process/reviews/test-analysis-solution-review.json |
| 11 | 覆盖审查 | coverage-review | 需求/方法/rules-pack/动态来源应用检查、阻断项；专家评分仅深度评估时执行 | done | process/reviews/analysis-coverage-review.json |
| 12 | 最终报告生成 | final-report-generation | reports/analysis-final-report.json、reports/analysis-final-report.md | done | reports/analysis-final-report.json、reports/analysis-final-report.md |
| 13 | 输出收口 | test-analysis-workflow | 主交付件 JSON/Markdown 路径、review/coverage/final-report JSON 路径、check-staged-run.py 结果 | done | bin/check-staged-run.py --scope analysis |
