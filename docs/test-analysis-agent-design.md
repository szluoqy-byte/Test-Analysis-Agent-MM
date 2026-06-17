# Test Analysis Agent 设计文档

## 目标

本 Agent 面向已归一化 Markdown 需求文档和可选设计方案文档，输出 `测试分析方案`；如果输入是 `.docx` 或 `.xlsx`，先由 `@file-normalization-agent` 归一化为 Markdown，再把归一化 Markdown 路径交给分析链路。它是独立项目，所有运行入口、Agent 门面、知识库、模板、skill 私有参考和校验脚本都在本仓库内维护，不依赖其他 Agent 项目或外部仓库结构。

主交付件回答 what to test，输出粒度为：

```text
测试场景 -> 测试点 -> 测试点明细
非成功测试点明细 -> 失败类型明细
```

`测试点明细` 是测试分析层的规则分支、路径分支、状态分支、权限分支、接口契约分支或风险分支。只有明确非成功聚合测试点明细强制新增 `TP-*-*-*` 失败类型明细继续拆分失败来源；单一弱结果分支可停留在 `TP-*-*`。它不是 `TDI-*` 测试设计项，不表达具体代表性条件、数据、状态或组合。`@test-design-agent` 可在人工评审后的测试分析方案上继续补充 TDI。

## Agent 边界

本仓库维护三个子 Agent：

| Agent | 主问题 | 主输入 | 主输出 |
|---|---|---|---|
| `@file-normalization-agent` | input readiness | `.docx` / `.xlsx` / `.md` 输入文件 | 归一化 Markdown、conversion metadata、可选 run-local manifest |
| `@test-analysis-agent` | what to test | 已归一化 Markdown 需求文档、可选设计方案 | `test-analysis-solution.json`，输出 `SC-* / TP-* / TP-*-*`，非成功明细可到 `TP-*-*-*` |
| `@test-design-agent` | how to test | 已评审测试分析方案、可选需求/设计依据 | `test-design-solution.json`，在普通 `TP-*-*` 或失败类型 `TP-*-*-*` 下补充 `TDI-*` |

分析 Agent 不输出 `TDI-*`；设计 Agent 不擅自新增分析层级。若设计阶段发现分析方案缺口，应记录过程问题，必要时回到分析 Agent 修正。

## 主交付件

固定路径：

```text
outputs/runs/<run-id>/deliverables/test-analysis-solution.json
```

新建完整分析 run 时，`run-id` 固定使用 `python bin/generate-run-id.py` 生成，格式为 `<YYYYMMDD-HHMMSS>`。

固定术语与缩写：

| 中文术语 | 缩写/ID |
|---|---|
| 测试场景 | `SC-*` |
| 测试点 | `TP-*` |
| 测试点明细 | `TP-*-*` |
| 失败类型明细 | `TP-*-*-*` |

主交付件不展开英文全名，不使用 `TDI-*`、`TD-*`、`TC-*`、`TCT-*`、`TI-*`、`ITP-*` 或 `ITDI-*`。

## 输出样例

```json
{
  "artifactType": "test-analysis-solution",
  "schemaVersion": "1.0",
  "title": "订单下发 测试分析方案",
  "scenarios": [
    {
      "id": "SC-001",
      "title": "订单下发",
      "testPoints": [
        {
          "id": "TP-001",
          "title": "E2E场景测试",
          "details": [
            {
              "id": "TP-001-001",
              "title": "订单下发主流程成功闭环",
              "description": "验证订单下发场景的端到端主流程能够从请求接收到订单处理结果完成闭环。",
              "expectedResult": "订单下发成功。",
              "failureDetails": []
            }
          ]
        }
      ]
    }
  ]
}
```

## Agent 协作流程

```mermaid
flowchart TD
  request([用户请求])
  request --> intent{用户目标}
  intent -- 文件归一化 --> fileAgent[file-normalization-agent]
  fileAgent --> normalized[归一化 Markdown]
  intent -- 生成测试分析方案 --> analysisAgent[test-analysis-agent]
  intent -- 生成测试设计方案 --> designAgent[test-design-agent]
  normalized --> analysisAgent
  normalized --> designAgent
  analysisAgent --> analysisSkill[test-analysis-workflow]
  analysisSkill --> analysisOutput[deliverables/test-analysis-solution.json]
  designAgent --> hasAnalysis{是否已有已评审分析方案}
  hasAnalysis -- 否 --> analysisSkill
  hasAnalysis -- 是 --> designSkill[test-design-workflow]
  analysisOutput --> designSkill
  designSkill --> designOutput[deliverables/test-design-solution.json]
```

## 测试分析主运行流程

```mermaid
flowchart TD
  start([用户请求])
  start --> agent[test-analysis-agent<br/>识别意图与入口]
  agent --> office{"是否为 Office 输入"}
  office -- 是 --> fileAgent["file-normalization-agent<br/>先归一化为 Markdown"]
  fileAgent --> restart["把归一化 Markdown 作为输入<br/>重新进入分析 workflow"]
  office -- 否 --> main["test-analysis-workflow<br/>创建 run 与任务清单"]
  restart --> main
  main --> ctx["context-source-indexing<br/>索引动态来源<br/>生成 context-pack"]
  ctx --> facts[input-fact-modeling<br/>建立输入事实模型<br/>事实清单/需求-设计映射/来源应用]
  facts --> route[testing-method-router<br/>选择测试技术与专项方法参考]
  route --> methods[专项方法参考<br/>产出 ME-* 方法证据与测试点候选]
  methods --> analysis[test-analysis-solution-generation<br/>生成 SC-*、TP-* 与 TP-*-*<br/>写入 test-analysis-solution.json]
  analysis --> jsonLint[bin/lint-run-json.py<br/>JSON canonical 校验]
  jsonLint --> render[bin/render-run-markdown.py<br/>渲染派生 Markdown]
  render --> lint[bin/lint-test-analysis-solution.py<br/>派生 Markdown 校验]
  lint --> lintDecision{lint 是否通过}
  lintDecision -- 否 --> fix[修正 JSON 事实源<br/>重新渲染，不手工改 Markdown]
  fix --> jsonLint
  lintDecision -- 是 --> review[test-analysis-solution-review<br/>语义评审<br/>粒度/依据/事实/非用例化]
  review --> coverage[coverage-review<br/>覆盖/追踪/方法/core rules/动态来源]
  coverage --> consistency[bin/check-artifact-consistency.py<br/>最终一致性校验]
  consistency --> output[deliverables/test-analysis-solution.json]
  output --> finish([完成])
```

## Skill 分工

| 层级 | Skill | 职责 |
|---|---|---|
| Agent 门面 | `test-analysis-agent` | 识别用户意图，路由生成、记录、咨询和框架维护任务 |
| 文件归一化入口 | `file-normalization-agent` | 将 `.docx` / `.xlsx` 输入归一化为 Markdown；不进入测试分析主流程 |
| 主入口 | `test-analysis-workflow` | 固定根目录、创建 run、编排全链路、输出主交付件 |
| 上下文 | `context-source-indexing` | 索引 project/personal 动态来源 frontmatter，记录绑定状态和阶段可见性 |
| 输入事实建模 | `input-fact-modeling` | 建立输入事实模型，记录事实清单、需求-设计映射和来源应用说明 |
| 方法路由 | `testing-method-router` | 选择适用测试技术和专项方法参考 |
| 专项方法参考 | `skills/testing-method-router/references/*.md` | 生成方法证据、测试点候选和补读记录 |
| 测试分析方案生成 | `test-analysis-solution-generation` | 生成并写入 `SC-*`、`TP-*`、`TP-*-*` 测试点明细和预期结果；非成功测试点明细继续拆分 `TP-*-*-*` |
| 确定性校验 | `bin/lint-run-json.py`、`bin/render-run-markdown.py --check`、`bin/lint-test-analysis-solution.py` | 先检查 JSON canonical 结构、编号和字段，再检查派生 Markdown 渲染一致性与人读格式；失败时修正 JSON，不手工改 Markdown |
| 独立评审 | `test-analysis-solution-review` | 只检查语义质量：测试点明细粒度、失败类型拆分充分性、预期结果依据、事实溯源和非用例化倾向 |
| 覆盖审查 | `coverage-review` | 检查需求覆盖、方法覆盖、追踪关系、rules 应用、项目知识应用和过程门禁；不重复 lint 已覆盖的结构规则 |

## Knowledge 分工

| 路径 | 作用 |
|---|---|
| `knowledge/test-workflow-boundaries.md` | 定义测试分析、测试设计、测试技术之间的边界 |
| `knowledge/test-analysis-solution-standard.md` | 定义主交付件结构、字段和兜底规则 |
| `knowledge/testpoint-standard.md` | 定义测试点粒度、分类和非用例化约束 |
| `knowledge/test-techniques/` | 测试技术库，支持分析阶段识别覆盖分支，也可供 `@test-design-agent` 复用 |
| `skills/testing-method-router/references/test-method-routing-matrix.md` | 测试技术与专项方法参考路由矩阵 |
| `skills/coverage-review/references/basic-test-types.md` | 基础测试类型参考 |
| `skills/coverage-review/references/coverage-check.md` | coverage-review 私有覆盖门禁参考 |
| `skills/testing-method-router/references/method-evidence-standard.md` | 方法证据 `ME-*` 记录标准 |

## Rules 分工

`rules/` 保存强制规则，优先级低于当前用户明确指令，但高于需求文档、设计方案、已评审测试分析方案、memory 和 knowledge。

| 路径 | 作用 |
|---|---|
| `rules/*.md` | 全局强制规则 |
| `rules/projects/<project-key>/**/*.md` | 项目级强制规则，确定 `project-key` 后读取 |
| `rules/user/**/*.md` | 个人本地强制规则，不得覆盖 core/project rules |

core rules 由 workflow 或对应 skill 固定读取；与输入冲突时默认遵守 rules，并在结构化过程记录或 review/coverage JSON 中留痕。

## 动态来源应用

project/personal 动态来源只来自 `rules/projects/<project-key>/`、`rules/user/`、`knowledge/projects/<project-key>/`、`knowledge/user/`、`memory/projects/<project-key>/` 和 `memory/user/`。文件名没有硬性要求，但必须声明 `name`、`description`，可选 `stages`。context pack 阶段只索引 frontmatter，不读取正文，不提前判断具体测试点或测试点明细命中。

- 项目风险画像、覆盖策略、术语映射、测试 oracle、测试设计因子库或业务测试设计模式库可通过 `stages` 对对应阶段可见。
- 项目/个人 checklist 通常配置为 `coverage-review` 可见，统一查漏。
- 覆盖门禁本身维护在 `skills/coverage-review/references/coverage-check.md`，不再维护独立顶层质量门禁目录；project/personal 附加要求应按语义进入 rules、knowledge 或 memory。
- 阶段读取动态来源后必须输出应用状态。
- 应用状态只能使用 `applied`、`not_applicable`、`insufficient_evidence`、`conflict_with_requirement` 或 `deferred_to_review`。

## 校验与审查门禁

确定性结构、编号、字段、JSON canonical 结构、Markdown 渲染一致性和固定章节问题以 `bin/lint-run-json.py`、`bin/render-run-markdown.py --check`、`bin/lint-test-analysis-solution.py` 和 `bin/check-artifact-consistency.py` 为事实源；模型型 review 不重复逐项检查，只消费脚本结果并继续做语义和覆盖判断。覆盖审查使用 `skills/coverage-review/references/coverage-check.md` 和 coverage-review 私有 references，不读取独立顶层质量门禁目录。

- 主输出必须按 `测试场景 -> 测试点 -> 测试点明细` 组织。
- 每个测试场景必须包含 `E2E场景测试` 测试点。
- `E2E场景测试` 是独立同级测试点，只维护 1 个端到端主流程成功闭环测试点明细；其他业务规则、异常处理、接口契约、权限、状态、回滚或补偿分支必须拆为同级 `TP-*`。
- 当需求、设计方案或用户任务明确要求接口测试/API 契约覆盖时，接口测试或集成覆盖场景下的非 E2E `TP-*` 必须先按接口、端点、消息、回调或集成点组织；字段、状态码、错误码、鉴权、幂等、超时和重试作为该接口 `TP-*` 下的明细或失败类型，不作为无法定位目标接口的泛化 `TP-*`。
- 每个测试点至少有一个测试点明细。
- 明确非成功聚合测试点明细必须新增 `TP-*-*-*` 失败类型明细；是否新增第四层由 `TP-*-*` 决定，不由 `TP-*` 决定。“未找到返回空结果”“列表为空”“count=0”等单一弱结果分支不强制新增第四层。
- 每个普通测试点明细必须包含 `测试点详情` 和 `预期结果`；非成功测试点明细由第四层失败类型明细承载 `测试点详情` 和 `预期结果`。
- 主输出不得出现 `TDI-*`、`测试设计项` 或测试设计项表格。
- 主输出不得出现旧版主交付件字段；字段禁用清单以 `bin/lint-test-analysis-solution.py` 为准。
- 主输出不得使用 Markdown 加粗语法，例如 `**文本**` 或 `__文本__`。
- 主输出不得包含完整测试用例字段、操作步骤、脚本或执行数据。
- 依据不足的预期结果只写输入可支撑的保守判定，不补写未说明具体值。
- 适用 rules 必须被执行、解释不适用，或记录被当前用户明确指令覆盖。

## 校验命令

```bash
python bin/sync-opencode-skills.py --check
python bin/validate-agent-runtime.py
python bin/lint-run-json.py outputs/runs/<run-id>
python bin/render-run-markdown.py outputs/runs/<run-id> --check
python bin/lint-test-analysis-solution.py outputs/runs/<run-id>/deliverables/test-analysis-solution.md
python bin/check-artifact-consistency.py outputs/runs/<run-id>
```

`python bin/smoke-test-analysis.py` 只用于框架回归或示例 fixture 变更后的 smoke 检查，不属于单次测试分析方案 review 阶段。
