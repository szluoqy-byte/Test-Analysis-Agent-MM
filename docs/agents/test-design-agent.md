# Test Design Agent

`@test-design-agent` 基于已评审分析结果 JSON 设计可执行测试用例，输出 `SC -> TP -> TC`。它继承既有 SC/TP，不负责重新执行测试分析。

## 输入与结果

| 类型 | 路径或内容 |
|---|---|
| 必需输入 | `deliverables/test-analysis-solution.json` |
| 补充输入 | 需求 Markdown、可选设计 Markdown、rules/context Markdown |
| 阶段结果 | `deliverables/test-design-solution.json` |
| 人读结果 | `deliverables/test-design-solution.md` |
| 人审报告 | `reports/design-final-report.md` |

## 流程

1. `manage-run.py prepare --flow design` 绑定分析结果并检查上游变化。
2. 加载或补齐 `rules-pack.md`、`context-pack.md` 和 `input-fact-model.md`。
3. 从分析结果提取 `test-case-work-items.json`。
4. 逐 TP 填写 `test-case-slices/<TP-ID>.md`，每个切片只生成当前 TP 的 TC。
5. 切片 review 通过后用 `complete-staged-items.py` 关闭工作项。
6. 基于已通过的过程 Markdown 写一次设计结果草稿，由 `finalize-deliverable.py --scope design` 分配稳定 TC ID、校验并固化结果 JSON。
7. 完成整体评审、FACT 覆盖图、coverage review、最终 Markdown 报告和 run 校验。

## 关键过程件

| 产物 | 职责 |
|---|---|
| `process/test-case-work-items.json` | TP 工作项的控制状态和内容哈希 |
| `process/test-case-slices/<TP-ID>.md` | 单个 TP 下的 TC 语义草稿 |
| `process/reviews/test-case-reviews/<TP-ID>.md` | 当前 TC 切片的语义评审 |
| `process/design-fact-coverage-map.md` | FACT 到 SC/TP/TC 的覆盖证据 |
| `process/reviews/design-coverage-review.md` | 覆盖门禁和返工定位 |

过程件直接使用 Markdown，不生成同名 JSON，也不持久化生成上下文副本。正式设计 JSON 只在阶段边界固化一次。

## 用例约束

- 每个 TP 先识别必选因子、候选因子和必要补充因子，再形成最小充分 TC 集合。
- TC 必须包含 `level`、前置条件、结构化测试数据、步骤级动作/预期、最终预期和来源引用。
- GUI、API、CLI 遵守各自写作风格；接口测试不写完整裸 URL。
- 设计阶段不得新增、删除、合并或改写分析结果中的 SC/TP。
- 不编造接口契约、状态、角色、阈值、错误码或提示。

## 返工与校验

- 切片或 coverage 阻断时使用 `reopen-run-items.py` 重开对应 TP 工作项，修复 Markdown 切片并重新评审。
- 不绕过过程 Markdown 直接手改正式结果 JSON。

```bash
python bin/check-staged-run.py outputs/runs/<run-id> --scope design
```
