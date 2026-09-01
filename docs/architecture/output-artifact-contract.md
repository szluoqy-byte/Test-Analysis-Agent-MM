# 输出产物契约

run 产物分为三类：语义过程 Markdown、脚本控制 JSON、阶段结果 JSON。字段细节以 `templates/`、`bin/run_artifacts.py`、`bin/lint-run-json.py` 和工作流为准。

## 核心原则

- 分析、设计和评审过程直接维护 Markdown，不再先写 JSON 再渲染。
- JSON 只用于脚本控制状态和阶段结果传递。
- 分析结果固定为 `SC -> TP`；设计结果固定为 `SC -> TP -> TC`。
- `deliverables/*.md` 是结果 JSON 的人读派生版，不手工维护。

## 运行目录

```text
outputs/runs/<run-id>/
  inputs/
  process/
    id-registry.json
    test-point-work-items.json
    test-case-work-items.json
    rules-pack.md
    context-pack.md
    input-fact-model.md
    testing-method-routing.md
    scenario-tree.md
    test-point-slices/<SC-ID>.md
    test-case-slices/<TP-ID>.md
    analysis-fact-coverage-map.md
    design-fact-coverage-map.md
    reviews/*.md
  deliverables/
    test-analysis-solution.json
    test-analysis-solution.md
    test-design-solution.json
    test-design-solution.md
  reports/
    analysis-final-report.md
    design-final-report.md
```

## 语义过程 Markdown

以下产物由模型直接生成和审阅：

- `rules-pack.md`、`context-pack.md`：规则与动态来源索引。
- `input-fact-model.md`、`testing-method-routing.md`：事实建模和方法分析。
- `scenario-tree.md`：冻结的 SC 场景树。
- `test-point-slices/<SC-ID>.md`：单个叶子 SC 的 TP 草稿。
- `test-case-slices/<TP-ID>.md`：单个 TP 的 TC 草稿。
- `process/reviews/*.md`：切片、整体方案和覆盖评审。
- `*-fact-coverage-map.md`：逐 FACT 覆盖证据。
- `reports/*-final-report.md`：最终人审报告。

过程 Markdown 不维护同名 JSON，不持久化 `generationContext`。返工时修改对应 Markdown 切片并重新评审。

## 控制 JSON

`id-registry.json` 和 `*-work-items.json` 由固定脚本维护。它们只记录稳定编号、分段状态和内容哈希，不承载测试语义，也不生成同名 Markdown。

## 结果 JSON

| 产物 | 用途 |
|---|---|
| `deliverables/test-analysis-solution.json` | 分析阶段向设计阶段传递已固化的 SC/TP 结果 |
| `deliverables/test-design-solution.json` | 对外传递完整 SC/TP/TC 设计结果 |

阶段结束时，模型根据已通过评审的过程 Markdown 写一次 `deliverables/test-*-solution.draft.json`，`bin/finalize-deliverable.py` 负责稳定编号、schema 校验、正式写入、人读 Markdown 渲染和草稿删除。后续机器流程只读取正式结果 JSON。

## Review、Coverage 与返工

- review 结论固定写入 Markdown，首要结论使用 `- 结论：通过`、`需修正`、`失败`、`警告` 或 `不适用`。
- `bin/complete-staged-items.py` 只在切片和对应 review 均存在且结论为“通过”时关闭工作项。
- review 或 coverage 发现缺口时，使用 `bin/reopen-run-items.py` 重开对应 SC/TP，再回到 Markdown 切片修复。
- final report 只展示已审查的覆盖关系，不新增缺口判断，也不触发返工。

## runid 与校验

`runid` 只确定 `outputs/runs/<run-id>/`。未指定时使用当前会话时间戳，目录碰撞时追加顺序后缀。若目标目录已有同阶段正式结果，默认改用新 `runid`；workflow 内 review/coverage 返工通过显式替换重新固化结果并保留稳定编号。

```bash
python bin/lint-run-json.py outputs/runs/<run-id>
python bin/render-run-markdown.py outputs/runs/<run-id> --check
python bin/check-artifact-consistency.py outputs/runs/<run-id>
python bin/check-staged-run.py outputs/runs/<run-id> --scope analysis|design
```
