# 测试分析与测试设计 Agent 参考架构

## 1. 目标

本架构把复杂性限制在必要边界：模型直接维护易读的语义过程 Markdown，固定脚本维护控制状态和稳定编号，JSON 只作为阶段结果传递格式。

```text
输入 Markdown
  -> 过程 Markdown（FACT / 方法 / SC / TP / TC / review / coverage）
  -> 阶段结果 JSON（analysis / design）
  -> 结果人读 Markdown
```

这样避免过程阶段反复修正 JSON 语法和字段，再把 JSON 转回 Markdown 的开销。

## 2. 分层

| 层 | 职责 | 事实源 |
|---|---|---|
| Agent 门面 | 识别意图、校验入口条件、路由 workflow | `agents/*.md` |
| Workflow | 组织阶段、门禁、返工和结果交接 | `skills/*-workflow/SKILL.md` |
| 语义 Skill | 事实建模、方法路由、生成、review、coverage、报告 | `skills/*/SKILL.md`、`knowledge/` |
| Harness | run 生命周期、控制状态、稳定编号、schema 校验 | `bin/` |
| Artifact | 持久化过程和结果 | `outputs/runs/<run-id>/` |

根目录 `agents/` 和 `skills/` 是手工事实源；`.opencode/`、`.testagent/` 是同步镜像。

## 3. 产物边界

### 3.1 语义过程 Markdown

- 规则和上下文：`rules-pack.md`、`context-pack.md`
- 输入分析：`input-fact-model.md`、`testing-method-routing.md`
- 分析过程：`scenario-tree.md`、`test-point-slices/*.md`
- 设计过程：`test-case-slices/*.md`
- 质量闭环：`process/reviews/*.md`、`*-fact-coverage-map.md`
- 人审报告：`reports/*-final-report.md`

这些文件直接生成、直接评审、直接返工，不维护同名 JSON，不持久化 `generationContext`。

### 3.2 控制 JSON

- `run-manifest.json` / `run-plan.json`：生命周期、输入与依赖指纹。
- `id-registry.json`：稳定 TP/TC 编号。
- `analysis-task-list.json` / `design-task-list.json`：阶段状态。
- `test-point-work-items.json` / `test-case-work-items.json`：分段状态和内容哈希。

控制 JSON 由脚本维护，不承载测试语义。

### 3.3 阶段结果 JSON

- `deliverables/test-analysis-solution.json`：`SC -> TP`
- `deliverables/test-design-solution.json`：`SC -> TP -> TC`

结果 JSON 是跨阶段和机器消费接口。对应 `.md` 由脚本确定性渲染。

## 4. 测试分析流程

```text
prepare run
  -> rules/context Markdown
  -> FACT Markdown
  -> testing method routing Markdown
  -> scenario-tree.md + review
  -> SC work items
  -> TP Markdown slices + reviews
  -> complete work items
  -> analysis result draft JSON
  -> stable ID + schema validation + deliverable
  -> final review
  -> FACT coverage Markdown + coverage review
  -> analysis final report Markdown
  -> check + finalize
```

关键门禁：

- SC 树最多 3 层，只有叶子 SC 挂 TP。
- 每个叶子 SC 包含 `E2E场景测试`。
- TP 表达验证目标簇，不把 TC 设计因子上移为 TP。
- 正式 JSON 只在所有 TP 切片通过后固化。

## 5. 测试设计流程

```text
prepare/bind analysis result
  -> load Markdown context
  -> TP work items
  -> TC Markdown slices + reviews
  -> complete work items
  -> design result draft JSON
  -> stable ID + schema validation + deliverable
  -> final review
  -> FACT coverage Markdown + coverage review
  -> design final report Markdown
  -> check + finalize
```

关键门禁：

- 设计阶段继承分析结果中的 SC/TP，不改写上游结构。
- 每个 TP 先做测试因子分析，再形成最小充分 TC 集合。
- 每个 TC 具有具体数据、可执行步骤、步骤预期和最终预期。
- 正式 JSON 只在所有 TC 切片通过后固化。

## 6. 返工闭环

review 或 coverage 发现问题时：

1. 通过缺口表定位 `SC-ID` 或 `TP-ID`。
2. 运行 `bin/reopen-run-items.py` 重开对应工作项。
3. 修改对应 Markdown 切片。
4. 重新完成切片 review 和工作项关闭。
5. 重新固化结果 JSON，并重复整体 review、coverage 和一致性检查。

不得直接编辑派生结果 Markdown，也不得绕过过程切片手改正式结果 JSON。

## 7. 增量与 Revision

`manage-run.py` 负责 `create/resume/reuse/extend/rebuild`、锁和输入指纹。输入或上游内容变化时，workflow 做语义影响分析，`reopen-run-items.py` 重开受影响工作项；无法确定影响范围时保守重开全部。

`extend/rebuild` 前快照当前 JSON、Markdown 和 inputs 到 `revisions/rNNNN/`，当前交付路径保持稳定。

## 8. 确定性边界

固定脚本负责：

- run 锁、revision、指纹和状态。
- Markdown 切片骨架及工作项状态。
- TP/TC 稳定编号。
- 结果 JSON schema、结果 Markdown 渲染与一致性。

模型负责：

- 业务事实理解和方法选择。
- SC、TP、TC 语义生成。
- review、coverage 判断和人审报告。

这种边界保留了结构可靠性，同时不要求模型在每个中间步骤承担 JSON 机械格式成本。
