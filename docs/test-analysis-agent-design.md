# Test Analysis Agent 设计文档

## 目标

本 Agent 面向 Markdown 需求文档和可选设计方案文档，输出 `测试分析方案`。它是独立项目，所有运行入口、Agent 门面、知识库、模板、质量门禁和校验脚本都在本仓库内维护，不依赖其他 Agent 项目或外部仓库结构。

主交付件回答 what to test，输出粒度为：

```text
测试场景 -> 测试点 -> 测试点明细
```

`测试点明细` 是测试分析层的规则分支、路径分支、状态分支、权限分支、接口契约分支或风险分支。它不是 `TDI-*` 测试设计项，不表达具体代表性条件、数据、状态或组合。`@test-design-agent` 可在人工评审后的测试分析方案上继续补充 TDI。

## 双 Agent 边界

本仓库维护两个子 Agent：

| Agent | 主问题 | 主输入 | 主输出 |
|---|---|---|---|
| `@test-analysis-agent` | what to test | 需求文档、可选设计方案 | `test-analysis-solution.md`，输出 `SC-* / TP-* / TP-*-*` |
| `@test-design-agent` | how to test | 已评审测试分析方案、可选需求/设计依据 | `test-design-solution.md`，在 `TP-*-*` 下补充 `TDI-*` |

分析 Agent 不输出 `TDI-*`；设计 Agent 不擅自新增分析层级。若设计阶段发现分析方案缺口，应记录过程问题，必要时回到分析 Agent 修正。

## 主交付件

固定路径：

```text
outputs/runs/<run-id>/deliverables/test-analysis-solution.md
```

新建完整分析 run 时，`run-id` 固定使用 `python bin/generate-run-id.py` 生成，格式为 `<YYYYMMDD-HHMMSS>`。

固定术语与缩写：

| 中文术语 | 缩写/ID |
|---|---|
| 测试场景 | `SC-*` |
| 测试点 | `TP-*` |
| 测试点明细 | `TP-*-*` |

主交付件不展开英文全名，不使用 `TDI-*`、`TD-*`、`TC-*`、`TCT-*`、`TI-*`、`ITP-*` 或 `ITDI-*`。

## 输出样例

```markdown
# 订单下发 测试分析方案

## 1. 需求范围

## 2. 测试场景与测试点

### SC-001 订单下发

#### TP-001 验证下发订单 ID 长度规则

##### TP-001-001 下发订单 ID 满足长度要求

- 测试点详情：验证下发订单 ID 符合需求定义的长度规则时，系统能够正常识别并处理订单下发请求。

- 预期结果：下发成功。

##### TP-001-002 下发订单 ID 不满足长度要求

- 测试点详情：验证下发订单 ID 不符合需求定义的长度规则时，系统能够拦截或拒绝订单下发请求。

- 预期结果：下发失败；具体错误处理待人工分析确认。
```

## Agent 协作流程

```mermaid
flowchart TD
  request([用户请求])
  request --> intent{用户目标}
  intent -- 生成测试分析方案 --> analysisAgent[test-analysis-agent]
  intent -- 生成测试设计方案 --> designAgent[test-design-agent]
  analysisAgent --> analysisSkill[analyze-requirement-test-analysis-solution]
  analysisSkill --> analysisOutput[deliverables/test-analysis-solution.md]
  designAgent --> hasAnalysis{是否已有已评审分析方案}
  hasAnalysis -- 否 --> analysisSkill
  hasAnalysis -- 是 --> designSkill[generate-test-design-solution]
  analysisOutput --> designSkill
  designSkill --> designOutput[deliverables/test-design-solution.md]
```

## 测试分析主运行流程

```mermaid
flowchart TD
  start([用户请求])
  start --> agent[test-analysis-agent<br/>识别意图与入口]
  agent --> main[analyze-requirement-test-analysis-solution<br/>创建 run 与任务清单]
  main --> ctx[memory-context-builder<br/>加载适用 rules<br/>生成 context-pack 与项目知识阶段绑定]
  ctx --> req[requirement-testability<br/>结构化需求与可测性分析]
  req --> hasDesign{是否提供设计方案}
  hasDesign -- 是 --> design[design-solution-extraction<br/>提取接口/字段/状态/权限/数据依赖]
  hasDesign -- 否 --> designGap[登记设计缺口候选]
  design --> cpInput[clarification-gate CP-INPUT<br/>收口输入冲突与缺失]
  designGap --> cpInput
  cpInput --> route[testing-method-router<br/>选择测试技术与专项分析 skill]
  route --> methods[专项分析 skills<br/>产出 ME-* 方法证据与测试点候选]
  methods --> cpAnalysis[clarification-gate CP-ANALYSIS<br/>收口会影响覆盖和预期结果的缺口]
  cpAnalysis --> tp[testpoint-generation<br/>生成 SC-* 与 TP-*]
  tp --> analysis[test-analysis-solution-generation<br/>生成 TP-*-* 与预期结果]
  analysis --> review[test-analysis-solution-review<br/>检查粒度、预期结果依据和 TDI 泄漏]
  review --> coverage[coverage-review<br/>覆盖审查与项目知识应用检查]
  coverage --> lint[bin/lint-test-analysis-solution.py<br/>bin/check-artifact-consistency.py]
  lint --> output[deliverables/test-analysis-solution.md]
  output --> finish([完成])
```

## Skill 分工

| 层级 | Skill | 职责 |
|---|---|---|
| Agent 门面 | `test-analysis-agent` | 识别用户意图，路由生成、记录、咨询和框架维护任务 |
| 主入口 | `analyze-requirement-test-analysis-solution` | 固定根目录、创建 run、编排全链路、输出主交付件 |
| 上下文 | `memory-context-builder` | 发现适用 rules、core/project/personal 上下文和项目知识阶段绑定 |
| 需求分析 | `requirement-testability` | 结构化需求模型、识别可测性缺口 |
| 设计提取 | `design-solution-extraction` | 提取接口、字段、状态、权限、数据依赖和设计缺口 |
| 缺口治理 | `clarification-gate` | 合并过程缺口，不向主交付件写独立待确认章节 |
| 方法路由 | `testing-method-router` | 选择适用测试技术和专项分析 skill |
| 专项分析 | 各专项 `*-analysis` skill | 生成方法证据、测试点候选和技术缺口 |
| 测试点生成 | `testpoint-generation` | 生成 `SC-*` 和 `TP-*` |
| 测试分析方案生成 | `test-analysis-solution-generation` | 生成 `TP-*-*` 测试点明细和预期结果 |
| 独立评审 | `test-analysis-solution-review` | 检查测试点明细粒度、预期结果依据、旧字段和 TDI 泄漏 |
| 覆盖审查 | `coverage-review` | 检查需求覆盖、方法覆盖、项目知识应用和质量门禁 |

## Knowledge 分工

| 路径 | 作用 |
|---|---|
| `knowledge/test-analysis-methodology.md` | 定义测试分析、测试设计、测试技术之间的边界 |
| `knowledge/test-analysis-solution-standard.md` | 定义主交付件结构、字段和兜底规则 |
| `knowledge/testpoint-standard.md` | 定义测试点粒度、分类和非用例化约束 |
| `knowledge/test-techniques/` | 测试技术库，支持分析阶段识别覆盖分支，也可供 `@test-design-agent` 复用 |
| `knowledge/test-method-routing-matrix.md` | 测试技术与专项 skill 路由参考 |
| `knowledge/basic-test-types.md` | 基础测试类型参考 |
| `knowledge/method-evidence-standard.md` | 方法证据 `ME-*` 记录标准 |

## Rules 分工

`rules/` 保存强制规则，优先级低于当前用户明确指令，但高于需求文档、设计方案、已评审测试分析方案、memory 和 knowledge。

| 路径 | 作用 |
|---|---|
| `rules/*.md` | 全局强制规则 |
| `rules/projects/<project-key>/**/*.md` | 项目级强制规则，确定 `project-key` 后读取 |
| `rules/user/**/*.md` | 个人本地强制规则，不得覆盖 core/project rules |

适用 rules 必须进入 `process/context-pack.md` 的“适用强制规则”表；与输入冲突时默认遵守 rules，并在“Rules 与输入冲突记录”中留痕。

## Project Knowledge 应用

`knowledge/projects/<project-key>/` 下的文件名没有硬性要求。context pack 阶段只判断文件用途和强制应用环节，不提前判断具体测试点或测试点明细命中。

- 测试设计因子库、业务测试设计模式库可绑定到 `testing-method-router`、`testpoint-generation`、`test-analysis-solution-generation` 和 `test-design-solution-generation`。
- 测试设计 checklist 可绑定到 `test-analysis-solution-review`、`test-design-solution-review` 和 `coverage-review`。
- 被绑定到某阶段的 project knowledge，该阶段必须读取相关章节并输出应用状态。
- 应用状态只能使用 `applied`、`not_applicable`、`insufficient_evidence`、`conflict_with_requirement` 或 `deferred_to_review`。

## 质量门禁

- 主输出必须按 `测试场景 -> 测试点 -> 测试点明细` 组织。
- 每个测试点至少有一个测试点明细。
- 每个测试点明细必须包含 `测试点详情` 和 `预期结果`。
- 主输出不得出现 `TDI-*`、`测试设计项` 或测试设计项表格。
- 主输出不得出现旧版主交付件字段；字段禁用清单以 `bin/lint-test-analysis-solution.py` 为准。
- 主输出不得包含完整测试用例字段、操作步骤、脚本或执行数据。
- 依据不足的预期结果必须写 `待人工分析确认`。
- 适用 rules 必须被执行、解释不适用，或记录被当前用户明确指令覆盖。

## 校验命令

```bash
python bin/sync-opencode-skills.py --check
python bin/validate-agent-runtime.py
python bin/lint-test-analysis-solution.py outputs/runs/<run-id>/deliverables/test-analysis-solution.md
python bin/check-artifact-consistency.py outputs/runs/<run-id>
```

`python bin/smoke-test-analysis.py` 只用于框架回归或示例 fixture 变更后的 smoke 检查，不属于单次测试分析方案 review 阶段。
