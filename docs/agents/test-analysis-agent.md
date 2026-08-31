# Test Analysis Agent

`@test-analysis-agent` 基于归一化需求 Markdown 和可选设计 Markdown 回答“测什么”，输出 `SC -> TP`，不生成测试用例、步骤、测试数据或预期结果。

## 输入与结果

| 类型 | 路径或内容 |
|---|---|
| 输入 | 需求 Markdown、可选设计 Markdown、可选 `project-key` / `runid` |
| 阶段结果 | `deliverables/test-analysis-solution.json` |
| 人读结果 | `deliverables/test-analysis-solution.md` |
| 人审报告 | `reports/analysis-final-report.md` |

## 流程

1. `manage-run.py prepare --flow analysis` 准备或恢复持久 run。
2. 生成 `rules-pack.md`、`context-pack.md`、`input-fact-model.md` 和 `testing-method-routing.md`。
3. 生成并评审 `scenario-tree.md`，冻结最多 3 层的 SC 树。
4. 从叶子 SC 建立 `test-point-work-items.json`，逐项填写 `test-point-slices/<SC-ID>.md`。
5. 每个切片通过 `test-point-reviews/<SC-ID>.md` 后，由 `complete-staged-items.py` 关闭工作项。
6. 基于已通过的过程 Markdown 写一次分析结果草稿，由 `finalize-deliverable.py --scope analysis` 分配稳定 TP ID、校验并固化结果 JSON。
7. 完成整体评审、FACT 覆盖图、coverage review 和最终 Markdown 报告。
8. 运行 staged check 后 finalize run。

## 关键过程件

| 产物 | 职责 |
|---|---|
| `process/scenario-tree.md` | 已评审冻结的 SC 层级 |
| `process/test-point-work-items.json` | 叶子 SC 的控制状态和内容哈希 |
| `process/test-point-slices/<SC-ID>.md` | 当前 SC 下的 TP 语义草稿 |
| `process/reviews/test-point-reviews/<SC-ID>.md` | 当前 TP 切片的语义评审 |
| `process/analysis-fact-coverage-map.md` | FACT 到 SC/TP 的覆盖证据 |
| `process/reviews/analysis-coverage-review.md` | 覆盖门禁和返工定位 |

过程件直接使用 Markdown，不生成同名 JSON，也不持久化 `generationContext`。控制 JSON 只由固定脚本维护。

## 生成约束

- 只有叶子 SC 挂载 TP；每个叶子 SC 必须包含 `E2E场景测试`。
- TP 是验证目标簇，不把单个输入变体、边界值、角色、状态或错误类型拆成独立 TP。
- 接口或集成覆盖先按端点、消息、回调或集成点组织 TP。
- 不编造业务事实、错误码、阈值、提示或状态变化。

## 返工与校验

- SC review 阻断时只修 `scenario-tree.md`。
- TP 或 coverage 阻断时使用 `reopen-run-items.py` 重开对应 SC 工作项，修复切片并重新评审。
- 不绕过过程 Markdown 直接手改正式结果 JSON。

```bash
python bin/check-staged-run.py outputs/runs/<run-id> --scope analysis
```
