# 输出产物契约

本文件说明 run 目录内主要产物的职责边界。字段细节以 `templates/`、`bin/run_artifacts.py`、`bin/lint-run-json.py` 和渲染脚本为准。

## 主交付件

| 产物 | 职责 |
|---|---|
| `deliverables/test-analysis-solution.json` | 测试分析方案，schema `2.0`，结构为 `SC -> TP` |
| `deliverables/test-analysis-solution.md` | 分析方案人读版，由 JSON 渲染 |
| `deliverables/test-design-solution.json` | 测试设计方案，schema `2.0`，结构为 `SC -> TP -> TC` |
| `deliverables/test-design-solution.md` | 设计方案人读版，由 JSON 渲染 |

JSON 是唯一事实源；Markdown 不手工维护。二者不一致时，以 JSON 为准并重新运行 `bin/render-run-markdown.py`。

## 运行目录

```text
outputs/runs/<run-id>/
  inputs/
  deliverables/
  process/
    analysis-task-list.json/.md
    design-task-list.json/.md
    rules-pack.json/.md
    context-pack.json/.md
    input-fact-model.json/.md
    scenario-tree.json/.md
    test-point-work-items.json/.md
    test-point-slices/
    test-case-work-items.json/.md
    test-case-slices/
    analysis-fact-coverage-map.json/.md
    design-fact-coverage-map.json/.md
    reviews/
  reports/
    analysis-final-report.json/.md
    design-final-report.json/.md
```

`process/reviews/` 保存过程评审和 coverage-review 产物；`reports/` 只保存最终人审报告。

## 过程件

- `process/scenario-tree.json`：冻结 SC 场景树，不包含 `testPoints[]`。
- `process/test-point-slices/<SC-ID>.json`：单个叶子 SC 的 TP 切片。
- `process/test-case-slices/<TP-ID>.json`：单个 TP 的 TC 切片。
- `process/analysis-fact-coverage-map.json` / `process/design-fact-coverage-map.json`：coverage-review 使用的 FACT 覆盖证据图。
- `generationContext`：由固定脚本生成的阶段工作包，只服务当前产物生成或评审，不合并进 deliverables。

## Review、Coverage 和 Final Report

- review 产物位于 `process/reviews/`，用于语义评审和返工定位。
- coverage-review 基于 fact-coverage-map 审查需求事实到 SC/TP/TC 的覆盖关系。
- coverage gap 必须通过 `coverageGaps[].artifactLocation` 定位回 slice，再用固定脚本重开工作项。
- final-report 位于 `reports/`，从已审查的 fact-coverage-map 生成，只供人工审阅，不输出 `coverageGaps[]`，不触发自动返工。

## Markdown 渲染

- 测试分析 Markdown 保留 SC/TP 层级。
- 测试设计 Markdown 面向脑图导入优化，避免超过 Markdown 标题层级上限。
- review、coverage、final-report Markdown 均由 JSON 派生。

## 校验入口

- `python bin/lint-run-json.py outputs/runs/<run-id>`
- `python bin/render-run-markdown.py outputs/runs/<run-id> --check`
- `python bin/check-artifact-consistency.py outputs/runs/<run-id>`
- `python bin/check-staged-run.py outputs/runs/<run-id> --scope analysis|design`
- `python bin/smoke-test-analysis.py`
