---
name: test-analysis-solution-generation
description: 基于输入事实模型、测试技术路由参考、专项方法候选和可见动态来源，先生成冻结 SC 场景树，再按叶子 SC 生成 TP 切片并合并为 schema 2.0 测试分析方案。
---

# 测试分析方案生成

本 skill 负责分析生成阶段，但不再一次性生成完整 SC+TP。它先生成 `process/scenario-tree.json` 冻结 SC 树，再按每个叶子 SC 填写 `process/test-point-slices/<SC-ID>.json`，最后由 workflow 调用 `bin/merge-staged-slices.py --scope analysis` 统一合并为 `deliverables/test-analysis-solution.json`。它不输出测试用例、测试数据、步骤或预期结果。

## 何时使用

在 `input-fact-modeling` 和 `testing-method-router` 完成后使用。先用于 SC 树生成，再用于每个叶子 SC 的 TP 切片生成；不要在设计阶段或 TC 写作阶段使用。

## 必读上下文

- `process/input-fact-model.json`
- `process/rules-pack.json`
- `process/context-pack.json`
- 测试技术路由结果与专项方法候选
- `knowledge/test-analysis-solution-standard.md`
- `knowledge/testpoint-standard.md`
- `process/scenario-tree.json`
- `process/test-point-work-items.json`
- `process/test-point-slices/<SC-ID>.json`
- 当前 `process/scenario-tree.json` 或切片 JSON 内的 `generationContext`
- `templates/test-analysis-solution-json-template.json`
- 对本阶段可见的 project/personal 动态来源

## 生成阶段

- [ ] Step 1: 初始化或刷新当前工作单元的 generationContext
- [ ] Step 2: 读取适用依据并锁定当前工作边界
- [ ] Step 3: 生成 SC 场景树
- [ ] Step 4: 校验并冻结 SC 场景树
- [ ] Step 5: 提取叶子 SC 工作项并初始化 TP 切片
- [ ] Step 6: 生成当前叶子 SC 的 TP 集合
- [ ] Step 7: 评审并合并 TP 切片
- [ ] Step 8: 校验合并后的分析 JSON 并保持输出边界

> 阶段索引是静态生成契约；当前 run 的真实状态由 `process/analysis-task-list.json` 和工作项 JSON 维护。

## 易错点

- SC 阶段不得出现 `testPoints[]`；TP 阶段不得改写 SC。
- 不要把单个输入变体、边界点、角色样本、状态样本、错误类型、配置取值、依赖返回、消息顺序或接口参数缺失项拆成独立 TP；这些属于设计阶段 TC 因子。
- 不要为了匹配某个测试技术而生成无输入依据的 TP。
- 切片内 TP 编号只是临时语义位置，最终编号由合并脚本统一处理。

## 各阶段执行要求

### Step 1: 初始化或刷新当前工作单元的 generationContext

1. 每个内部阶段开始前，必须先确认目标 JSON 已由固定脚本写入 `generationContext`；若缺失，先运行 `skills/test-analysis-solution-generation/scripts/init-scenario-tree.py`、`skills/test-analysis-solution-generation/scripts/init-test-point-slice.py` 或 `bin/build-generation-context.py` 生成，不手工拼写。

### Step 2: 读取适用依据并锁定当前工作边界

2. 优先读取 `generationContext.applicableRules[]` 中已内联的本阶段 rules 正文；这些 rules 是强制约束。
3. 按 `generationContext.visibleSources[]` 判断本阶段可见动态来源；只读取与 SC 建模或 TP 生成有关的正文，并在过程产物或 review/coverage 中记录应用状态。
4. 使用 `generationContext.relevantFacts[]` 作为当前工作单元的优先事实候选；如候选不足，可回读 `process/input-fact-model.json` 和输入 Markdown，但不得跳出当前 SC/TP 工作边界。

### Step 3: 生成 SC 场景树

5. SC 阶段只从需求目标、业务流程、角色、状态、接口、数据对象和风险中组织 `SC-*` 场景树，写入 `process/scenario-tree.json`。
6. `process/scenario-tree.json` 的场景最多 3 层，任何 SC 节点都不得包含 `testPoints[]`、测试用例、步骤、测试数据或预期结果。

### Step 4: 校验并冻结 SC 场景树

7. SC review 通过后视为冻结；TP 阶段不得新增、删除、合并或改写 SC ID、标题、层级或字段。

### Step 5: 提取叶子 SC 工作项并初始化 TP 切片

8. 运行固定脚本生成 `process/test-point-work-items.json`，每个叶子 SC 对应一个 TP 切片。

### Step 6: 生成当前叶子 SC 的 TP 集合

9. 每个 `process/test-point-slices/<SC-ID>.json` 只填写当前叶子 SC 的 `scenario.testPoints[]`。
10. 每个叶子场景必须包含一个 `E2E场景测试` 测试点。

### Step 7: 评审并合并 TP 切片

11. `TP-*` 最终由 `skills/test-analysis-solution-generation/scripts/merge-test-point-slice.py` 分配 run 内全局唯一、增量稳定的编号；既有 TP 保留 ID，新 TP 从历史最大值后追加，退役编号不复用。

只有当前 TP 切片通过独立 review 后，才允许固定合并脚本写回主交付件并统一编号；失败时回到当前 SC 的切片修复。

### Step 8: 校验合并后的分析 JSON 并保持输出边界

12. `TP-*` 是验证目标簇，不是具体测试用例标题；它表达规则、路径、状态、权限、接口契约或风险，并应能在设计阶段展开为覆盖该目标的最小充分 TC 集合。
13. 如果多个 TP 候选只在具体取值、缺失字段、角色样本、状态样本、配置取值、依赖返回、消息顺序、错误类型或接口参数变体上不同，而验证的是同一接口、业务规则、权限边界、状态规则或风险目标，应合并为一个 TP，把差异留给 TC。
14. 接口类场景下的非 E2E `TP-*` 应先定位接口、端点、消息、回调或集成点，再表达契约关注点；字段、状态码、错误码、鉴权、幂等、超时、重试和参数缺失是该接口 TP 下的 TC 设计因子，不要默认拆成多个 TP。
15. 不输出 `expectedResult`。具体预期属于设计阶段 TC。
16. 不输出具体数据值、操作步骤、测试脚本、自动化代码或真实生产数据。
17. 如果输入不足，只生成输入可支持的 SC/TP，不编造错误码、提示文案、状态值或阈值；rules 与输入文档冲突时，默认遵守 rules 并在 basisRefs 或 note 中记录覆盖原因。
18. 测试技术和专项方法只作为生成参考，用于启发覆盖维度和风险视角；最终 TP 不必逐项映射方法，也不得为了贴合某个方法而牺牲输入事实支持。

合并后必须运行 `python bin/lint-run-json.py outputs/runs/<run-id>`；失败时只回到当前 JSON 或对应 TP 切片修复，不手工编辑 Markdown。

## JSON 结构

SC 阶段输出：

```text
outputs/runs/<run-id>/process/scenario-tree.json
```

TP 阶段输出：

```text
outputs/runs/<run-id>/process/test-point-slices/<SC-ID>.json
```

最终主输出由 workflow 使用 `bin/merge-staged-slices.py --scope analysis` 合并写入：

```text
outputs/runs/<run-id>/deliverables/test-analysis-solution.json
```

结构要求：

- `artifactType`: `test-analysis-solution`
- `schemaVersion`: `2.0`
- `scope[]`: 需求范围说明
- `scenarios[]`: 场景树
- 叶子场景的 `testPoints[]` 每项包含：
  - `id`
  - `title`
  - `objective`
  - `basisRefs[]`
  - 可选 `note`

## 禁止项

- 不在 `process/scenario-tree.json` 中写 `testPoints[]`。
- 不删除或手工伪造 `generationContext`；上下文缺失或过期时运行固定脚本刷新。
- 不在 TP 切片阶段改写 SC。
- 不写 `TC-*`。
- 不写 schemaVersion 2.0 之外的字段或 `testCases`。
- 不写 `expectedResult`、`preconditions`、`testData`、`steps`。
- 不把测试技术名称直接塞进测试点标题。
- 不把“功能正常”“异常流程”这类空泛词作为测试点主体。
- 不手工写 Markdown；由 `bin/render-run-markdown.py` 渲染。

## 验证闭环

SC 阶段填写后运行 `python skills/test-analysis-solution-generation/scripts/lint-scenario-tree.py outputs/runs/<run-id>/process/scenario-tree.json` 并进入 SC review。TP 切片填写后先做切片 review，再运行 `python bin/merge-staged-slices.py outputs/runs/<run-id> --scope analysis --ids <SC-ID>` 或 `--all`。合并后运行 `python bin/lint-run-json.py outputs/runs/<run-id>`；失败时回到对应 JSON 或切片修复。
