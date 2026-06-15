---
name: test-analysis-solution-review
description: 在测试分析方案 JSON 通过确定性 lint 且 Markdown 已渲染后使用，作为产物级语义评审环节，检查测试点明细粒度、预期结果依据、事实溯源、失败类型拆分充分性、项目评审清单和非完整用例化倾向；不重复执行 Python 脚本可确定性检查的结构、编号、字段和 Markdown 语法规则。
---

# 测试分析方案语义评审

本 skill 是 `test-analysis-agent` 的产物级语义评审环节。它只处理 Python 脚本无法稳定判断的质量问题；结构、编号、禁用字段、固定章节、JSON schema、Markdown 加粗、`TDI-*` 泄漏、E2E 是否存在、第四层格式等确定性问题，以 `bin/lint-run-json.py`、`bin/render-run-markdown.py --check`、`bin/lint-test-analysis-solution.py` 和 `bin/check-artifact-consistency.py` 的结果为准。

如果确定性 lint 未通过，本 skill 不进入语义评审，只引用脚本失败项给出修正方向。

## 输入

- `outputs/runs/<run-id>/deliverables/test-analysis-solution.json`，必要时参考派生 `test-analysis-solution.md`。
- `bin/lint-run-json.py`、`bin/render-run-markdown.py --check` 和 `bin/lint-test-analysis-solution.py` 的执行结果。
- 需求文档和可选设计方案文档摘要。
- `process/context-pack.json`。
- `process/clarification-session.json`。
- 方法证据、测试技术路由和测试分析方案生成结果。
- `process/context-pack.json` 中绑定到 `test-analysis-solution-review` 的评审类 project knowledge；默认 checklist 类项目知识优先由 `coverage-review` 统一处理，避免重复读取。
- `knowledge/test-workflow-boundaries.md`。
- `knowledge/test-analysis-solution-standard.md`。

## 不再重复检查

以下内容由确定性脚本负责，本 skill 不逐项复查：

- 主标题、必需章节和禁止章节。
- `SC-*`、`TP-*`、`TP-*-*`、`TP-*-*-*` 的格式与连续编号。
- 每个场景是否存在 `E2E场景测试`。
- 每个测试点是否存在测试点明细。
- 明确非成功聚合测试点明细是否存在第四层，普通明细是否误挂第四层。
- `TDI-*`、`TD-*`、`TC-*` 等禁用编号和旧字段泄漏。
- Markdown 加粗、完整测试用例字段、表格承载分析明细等格式问题。

## 评审维度

| 维度 | 通过标准 |
|---|---|
| 需求语义覆盖 | 关键需求规则、主路径、失败路径、权限/状态/接口/数据风险没有明显漏分析 |
| 分析粒度 | 测试点明细表达规则分支、路径分支、状态分支、权限分支、接口契约分支或风险分支，不下钻成具体代表性数据或测试设计项 |
| 失败类型充分性 | 明确非成功聚合测试点明细下的失败类型能按业务逻辑、系统交互、外部依赖、异常返回、数据校验、权限控制、状态限制、接口契约或数据一致性等来源充分拆分；单一弱结果分支不机械要求第四层 |
| 预期结果依据 | 预期结果能追溯到需求、设计方案、适用 rules 或明确业务不变量；依据不足时写 `待人工分析确认` |
| 事实完整性 | 不编造需求或设计方案没有说明的状态、错误码、错误提示、接口字段、数据库字段、角色或阈值 |
| 非用例化语义 | 虽然脚本已过滤明显步骤字段，但评审仍需识别隐性的执行流程、脚本化表达或完整用例倾向 |
| 自包含性 | 后续人工评审和 `test-design-agent` 不需要回读结构化过程记录即可理解测试场景、测试点和测试点明细 |
| 项目评审知识 | 若 context pack 明确绑定本阶段 project knowledge，必须读取相关章节并记录应用状态 |

## 评审步骤

1. 确认 `bin/lint-run-json.py`、`bin/render-run-markdown.py --check` 和 `bin/lint-test-analysis-solution.py` 已通过；若未通过，输出 `需修正`，只列脚本失败项和修正方向，不继续做语义评审。
2. 读取 `process/context-pack.json` 的“项目知识阶段绑定”。如果存在绑定到 `test-analysis-solution-review` 的 project knowledge，按来源文件、相关章节、关键词或标题读取，不全量复制大文件。
3. 对照输入事实模型和方法证据，检查是否存在关键需求规则、主路径、失败路径、权限、状态、接口契约、数据一致性或高风险区域漏分析。
4. 检查测试点明细是否停留在测试分析层：能支撑后续测试设计，但不直接列代表性条件、具体边界值、数据组合或执行数据清单。
5. 检查明确非成功聚合测试点明细下的失败类型拆分是否充分；如果多个失败来源被混在一个失败类型明细中，要求拆分或记录依据不足。对“未找到返回空结果”“列表为空”“count=0”等单一弱结果分支，不因缺少第四层判为失败。
6. 检查每个叶子分析节点的 `预期结果` 是否有可追溯依据；无法溯源的具体错误码、状态变化、提示文案、接口字段或阈值必须改为 `待人工分析确认`。
7. 检查是否存在隐性的完整用例化表达，例如按执行顺序描述操作、把断言写成步骤、把方法产物清单直接放进主交付件。
8. 按本阶段绑定的 project review knowledge 检查项目级漏覆盖；无法直接判断的检查项记录为 `insufficient_evidence`，不得编造成已确认缺陷。
9. 记录本阶段 project knowledge 应用状态，输出语义评审结论和逐项修正建议。

## 输出

评审输出写入 `reports/test-analysis-solution-review.json`，使用以下结构；如需人读版，由 `bin/render-run-markdown.py` 渲染：

| 评审项 | 结果 | 证据 | 修正建议 |
|---|---|---|---|
| 确定性 lint 前置 | 通过/失败 |  |  |
| 需求语义覆盖 | 通过/警告/失败 |  |  |
| 分析粒度 | 通过/警告/失败 |  |  |
| 失败类型充分性 | 通过/警告/失败 |  |  |
| 预期结果依据 | 通过/警告/失败 |  |  |
| 事实完整性 | 通过/警告/失败 |  |  |
| 非用例化语义 | 通过/警告/失败 |  |  |
| 自包含性 | 通过/警告/失败 |  |  |
| 项目评审知识 | 通过/警告/失败/不适用 |  |  |

如本阶段绑定了 project knowledge，追加应用记录：

| 来源文件 | 当前阶段 | 应用状态 | 应用位置 | 说明 |
|---|---|---|---|---|

结论必须明确为：

- `通过`：可以进入覆盖审查。
- `需修正`：必须先修正主交付件或过程证据再进入覆盖审查。

## 约束

- 不重复执行或改写确定性脚本已经覆盖的结构规则。
- 不编造需求或设计方案事实。
- 不把过程缺口写回主交付件的独立章节。
- 不用 `待确认`、`TBD`、`见设计方案` 替代 `待人工分析确认`。
- 不引入 `TDI-*` 或测试设计项。
- 绑定到本阶段的 project knowledge 必须读取并留痕；如果未应用，必须使用 `not_applicable`、`insufficient_evidence` 或 `conflict_with_requirement` 解释。
