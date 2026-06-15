# 输出产物契约

本项目有两个主交付件：测试分析阶段默认生成 `test-analysis-solution.json`，并由脚本渲染 `test-analysis-solution.md`；测试设计阶段在已评审测试分析方案基础上生成 `test-design-solution.json`，并由脚本渲染 `test-design-solution.md`。

JSON 是 run 内过程产物、主交付件和 review/coverage 结果的唯一事实源；Markdown 是派生的人类阅读版，不手工维护。若 JSON 与 Markdown 不一致，以 JSON 为准，运行 `python bin/render-run-markdown.py outputs/runs/<run-id>` 重新渲染。

## 运行目录

```text
outputs/
  input-cache/
    <sha256-12>/
      <source-stem>.md
      <source-stem>.conversion.json
  runs/
    <run-id>/
      inputs/
        <sha256-12>-<source-stem>.md
        <sha256-12>-<source-stem>.conversion.json
        input-normalization-manifest.json
      deliverables/
        test-analysis-solution.json
        test-analysis-solution.md
        test-design-solution.json
        test-design-solution.md
      process/
        task-list.json
        task-list.md
        context-pack.json
        context-pack.md
        input-fact-model.json
        input-fact-model.md
        clarification-session.json
        clarification-session.md
      reports/
        test-analysis-solution-review.json
        test-design-solution-review.json
        coverage-review.json
        coverage-review.md
        test-analysis-report.md  # legacy optional only
```

新建完整 run 时，`run-id` 固定使用 `python bin/generate-run-id.py` 生成，格式为 `<YYYYMMDD-HHMMSS>`。同一轮分析、修正、质量门禁重跑和报告刷新必须复用已创建的 run 目录；测试设计阶段优先复用上游测试分析方案所在 run。

当需求文档、系统设计方案或外部分析方案输入为 `.docx` 或 `.xlsx` 时，必须先固定 `<run-id>` 并创建 run 目录，再通过 `normalize-input-documents` 归一化为 Markdown。归一化结果按源文件内容哈希写入 `outputs/input-cache/<sha256-12>/`，源文件内容不变时复用缓存；完整 run 还必须把本次实际使用的 Markdown 和 metadata 绑定到 `outputs/runs/<run-id>/inputs/`。后续测试分析和测试设计流程只读取 run-local Markdown 路径。

DOCX 图片、流程图、架构图、状态图、截图或 EMF/Visio 图形解析后的 Mermaid/结构化事实必须合并回同一个归一化 Markdown，并放在脚本生成的 `DOCX_IMAGE_START` / `DOCX_IMAGE_END` 原文占位位置。不得只维护独立图片补充文件、文末补充章节、process、context-pack 或最终回复。若图片无法可靠定位到原文位置，归一化阶段不能标记为完成。

DOCX 图片理解和 Mermaid 转换必须按原文顺序分批处理：普通图片每批 3-5 张，复杂流程图、架构图、状态图或高密度截图每批 1-2 张。每批完成后必须立即把结果回写到 run-local Markdown 的对应占位块，再进入下一批；不得一次性把全部图片读入模型上下文后再统一整理。

## 固定产物

| 类型 | 路径 | 必须生成 | 说明 |
|---|---|---|---|
| 测试分析主交付件 JSON | `deliverables/test-analysis-solution.json` | 分析阶段是 | 测试分析方案事实源；按 `SC-* -> TP-* -> TP-*-* -> TP-*-*-*` 结构化组织，禁止 `TDI-*` |
| 测试分析主交付件 Markdown | `deliverables/test-analysis-solution.md` | 分析阶段是 | 由 `test-analysis-solution.json` 渲染的人读版，不手工编辑 |
| 测试设计主交付件 JSON | `deliverables/test-design-solution.json` | 设计阶段是 | 测试设计方案事实源；在分析层级下挂载 `TDI-*` 设计项 |
| 测试设计主交付件 Markdown | `deliverables/test-design-solution.md` | 设计阶段是 | 由 `test-design-solution.json` 渲染的人读版，不手工编辑 |
| 任务清单 JSON | `process/task-list.json` | 是 | 当前 run 的流程事实源，记录阶段顺序、状态和证据路径 |
| 任务清单 Markdown | `process/task-list.md` | 是 | 由 `task-list.json` 渲染的人读版 |
| 上下文包 JSON | `process/context-pack.json` | 是 | 记录适用 rules、Rules 与输入冲突、core/project/personal 来源绑定、命中、未采用来源、项目知识阶段绑定和补读建议 |
| 上下文包 Markdown | `process/context-pack.md` | 是 | 由 `context-pack.json` 渲染的人读版 |
| 输入事实模型 JSON | `process/input-fact-model.json` | 分析阶段是 | 记录输入来源、事实、需求-设计映射、待确认事项和来源应用说明 |
| 输入事实模型 Markdown | `process/input-fact-model.md` | 分析阶段是 | 由 `input-fact-model.json` 渲染的人读版 |
| 待确认治理记录 JSON | `process/clarification-session.json` | 是 | 记录候选问题、去重降级结果和预期结果兜底清单；无候选时也必须声明 `无待确认候选` |
| 待确认治理记录 Markdown | `process/clarification-session.md` | 是 | 由 `clarification-session.json` 渲染的人读版；不写入主交付件章节 |
| 分析语义评审 JSON | `reports/test-analysis-solution-review.json` | 分析评审时是 | 记录 LLM 语义评审结论、阻断项、建议和证据引用 |
| 设计语义评审 JSON | `reports/test-design-solution-review.json` | 设计评审时是 | 记录 LLM 语义评审结论、阻断项、建议和证据引用 |
| 覆盖审查 JSON | `reports/coverage-review.json` | 是 | 记录覆盖、追踪、rules/project knowledge 应用和质量门禁结论 |
| 遗留过程分析报告 | `reports/test-analysis-report.md` | 迁移旧 run 时可选 | 兼容性人读证据；新 run 不以该 Markdown 作为机器事实源，优先使用结构化 process/review/coverage JSON |
| 全局归一化输入缓存 | `outputs/input-cache/<sha256-12>/<source-stem>.md` | Office 输入时是 | `.docx` / `.xlsx` 转换后的 Markdown 复用缓存，不属于单次 run 目录，可跨 run 复用 |
| 全局归一化输入 metadata | `outputs/input-cache/<sha256-12>/<source-stem>.conversion.json` | Office 输入时是 | 记录源路径、源大小、mtime、SHA-256、转换时间、输出路径和转换警告 |
| 本次 run 输入 Markdown | `inputs/<sha256-12>-<source-stem>.md` | 完整 run 且有 Office 输入时是 | 从全局缓存绑定到本次 run 的输入事实源，后续流程读取该路径；DOCX 图片/图形补充必须合并在该文件的原文占位位置 |
| 本次 run 输入 metadata | `inputs/<sha256-12>-<source-stem>.conversion.json` | 完整 run 且有 Office 输入时是 | 记录源文件、全局缓存、run-local 路径、转换警告和绑定时间 |
| 本次 run 输入 manifest | `inputs/input-normalization-manifest.json` | 完整 run 且有 Office 输入时是 | 记录本次所有归一化输入的源文件、全局缓存和 run-local 映射 |

## Process 目录边界

`process/` 下固定必需产物以 JSON 为事实源，同时保留同名 Markdown 派生版：

- `task-list.json` / `task-list.md`：阶段顺序、状态和证据路径。
- `context-pack.json` / `context-pack.md`：适用 rules、project/personal 绑定、项目知识阶段绑定和补读建议。
- `input-fact-model.json` / `input-fact-model.md`：输入事实、需求-设计映射和待确认事项。
- `clarification-session.json` / `clarification-session.md`：待确认候选治理、去重降级结果和预期结果兜底清单。

其他过程性材料不是固定必需产物。若某个 skill 需要保存中间证据，优先写入 `reports/` 的结构化 JSON，或在上述 process JSON 中登记摘要和证据路径，避免 `process/` 目录随流程漂移。

## 测试分析主交付件结构

主交付件只使用中文术语和固定缩写：测试场景 `SC-*`、测试点 `TP-*`、测试点明细 `TP-*-*`、失败类型明细 `TP-*-*-*`，不展开英文全名，不使用其他编号体系。

主交付件必须只面向测试分析方案，事实源结构如下：

```json
{
  "artifactType": "test-analysis-solution",
  "schemaVersion": "1.0",
  "title": "<需求名称> 测试分析方案",
  "scope": [
    {"field": "需求名称", "content": "<需求名称>"}
  ],
  "scenarios": [
    {
      "id": "SC-001",
      "title": "<测试场景名称>",
      "fields": [
        {"field": "场景目标", "content": "<场景目标>"}
      ],
      "testPoints": [
        {
          "id": "TP-001",
          "title": "E2E场景测试",
          "details": [
            {
              "id": "TP-001-001",
              "title": "<端到端主流程测试点明细>",
              "description": "<说明该场景端到端业务主流程需要验证什么。>",
              "expectedResult": "<业务主流程按预期完整闭环或待人工分析确认>",
              "failureDetails": []
            }
          ]
        },
        {
          "id": "TP-002",
          "title": "<测试点>",
          "details": [
            {
              "id": "TP-002-001",
              "title": "<测试点明细>",
              "description": "<说明该分支需要验证什么。>",
              "expectedResult": "<明确预期结果或待人工分析确认>",
              "failureDetails": []
            },
            {
              "id": "TP-002-002",
              "title": "<非成功测试点明细>",
              "failureDetails": [
                {
                  "id": "TP-002-002-001",
                  "title": "<失败类型明细>",
                  "description": "<说明该失败类型需要验证什么。>",
                  "expectedResult": "<明确预期结果或待人工分析确认>"
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

每个测试场景下必须包含一个 `E2E场景测试` 测试点。`E2E场景测试` 是独立同级测试点，只维护 1 个端到端主流程成功闭环测试点明细；其他业务规则、异常处理、接口契约、权限、状态、回滚或补偿分支必须拆为同级 `TP-*`。当需求、设计方案或用户任务明确要求接口测试/API 契约覆盖时，接口测试或集成覆盖场景的非 E2E `TP-*` 必须先按接口、端点、消息、回调或集成点组织，再拆契约维度；通用接口规则必须在 `TP-*` 标题中说明适用范围。只有 `TP-*-*` 是明确非成功聚合测试点明细时才强制新增 `TP-*-*-*` 第四层；“未找到返回空结果”“列表为空”“count=0”等单一弱结果分支可停留在 `TP-*-*`。`TP-*` 本身仍表示测试点主题。

## 测试设计主交付件结构

测试设计方案只使用中文术语和固定缩写：测试场景 `SC-*`、测试点 `TP-*`、测试点明细 `TP-*-*`、失败类型明细 `TP-*-*-*`、测试设计项 `TDI-*`，不展开英文全名，不使用其他编号体系。

```json
{
  "artifactType": "test-design-solution",
  "schemaVersion": "1.0",
  "title": "<需求名称> 测试设计方案",
  "inputs": [
    {"field": "测试分析方案来源", "content": "deliverables/test-analysis-solution.json"}
  ],
  "scenarios": [
    {
      "id": "SC-001",
      "title": "<测试场景名称>",
      "fields": [
        {"field": "场景目标", "content": "<继承测试分析方案>"}
      ],
      "testPoints": [
        {
          "id": "TP-001",
          "title": "E2E场景测试",
          "details": [
            {
              "id": "TP-001-001",
              "title": "<端到端主流程测试点明细>",
              "description": "<来自测试分析方案的端到端主流程测试点详情。>",
              "expectedResult": "<来自测试分析方案的预期结果，依据不足时为待人工分析确认>",
              "failureDetails": [],
              "designItems": [
                {
                  "id": "TDI-001",
                  "content": "<覆盖端到端主流程的代表性条件、数据、状态或组合>"
                }
              ]
            }
          ]
        },
        {
          "id": "TP-002",
          "title": "<测试点>",
          "details": [
            {
              "id": "TP-002-001",
              "title": "<测试点明细>",
              "description": "<来自测试分析方案的测试点详情。>",
              "expectedResult": "<来自测试分析方案的预期结果，依据不足时为待人工分析确认>",
              "failureDetails": [],
              "designItems": [
                {
                  "id": "TDI-002",
                  "content": "<代表性条件、数据、状态或组合>"
                }
              ]
            },
            {
              "id": "TP-002-002",
              "title": "<非成功测试点明细>",
              "failureDetails": [
                {
                  "id": "TP-002-002-001",
                  "title": "<失败类型明细>",
                  "description": "<来自测试分析方案的失败类型明细。>",
                  "expectedResult": "<来自测试分析方案的预期结果，依据不足时为待人工分析确认>",
                  "designItems": [
                    {
                      "id": "TDI-003",
                      "content": "<覆盖该失败类型的代表性条件、数据、状态或组合>"
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

测试设计方案必须继承测试分析方案的分析层级，不新增、删除、合并或改写 `SC-*`、`TP-*`、`TP-*-*` 或 `TP-*-*-*`。`E2E场景测试` 仍是独立同级测试点，只维护端到端主流程成功闭环设计项；其他规则、异常、接口、权限、状态、回滚或补偿设计项保留在同级 `TP-*` 下。当分析方案包含接口测试或集成覆盖场景时，设计方案必须继承按接口、端点、消息、回调、集成点或通用接口范围组织的 `TP-*`，让每个 `TDI-*` 能追溯到具体接口或通用接口范围。已有 `TP-*-*-*` 失败类型明细时，`designItems[]` 挂第四层；单一弱结果分支停留在 `TP-*-*` 时，`designItems[]` 直接挂该明细，不机械新增第四层。普通测试点明细或失败类型明细层保留 `expectedResult`；`TDI-*` 必须写入 `designItems[]`，只写代表性条件、具体数据值、数据槽位、状态、接口返回或组合，不重复写 `expectedResult`，不得使用测试设计项表格。接口类 `TDI-*` 不输出完整裸 URL，必须拆成 `接口=METHOD /path`、`参数名=参数值`、`响应状态=...` 等同一行字段片段。`TDI-*` 不写结果或动作表达；同类条件在不同场景、渠道、操作或接口下复用时必须补充差异维度；接口契约叶子节点应基于已明确字段约束覆盖代表性有效、无效、边界、枚举、必填、鉴权、幂等、超时或异常返回组合；补偿类叶子节点应写成可观察分支条件。

## 预期结果兜底

- `预期结果` 只能写需求、设计方案或上游测试分析方案明确支持的简短判定结果。
- 如果需求和设计方案没有说明错误提示、状态变化、错误码、接口返回内容、消息发送结果或数据记录变化，写 `待人工分析确认`。
- 不得为缺口新增 `## 3. 未明确规则`。
- 不得在主交付件输出独立待确认信息清单。
- 不得在主交付件使用 Markdown 加粗语法，例如 `**文本**` 或 `__文本__`。

## 下游消费

- 后续机器流程和 review skill 优先读取 `outputs/runs/<run-id>/deliverables/test-analysis-solution.json`；人工评审读取同名 `.md` 派生版。
- 后续完整用例写作或自动化设计优先读取 `outputs/runs/<run-id>/deliverables/test-design-solution.json`；人工评审读取同名 `.md` 派生版。
- 结构化过程记录、context pack 和 clarification session 是审查证据，不是主交付件的必读前置。
- 如果 context pack 命中了 `*/projects/<project-key>/` 或 `*/user/`，后续理解测试分析方案需要知道的项目风险、覆盖策略、术语映射、个人关注点或判定依据必须上收到主交付件。
- 如果 context pack 登记了适用 rules，后续生成、评审和覆盖审查必须应用、解释不适用，或记录被当前用户明确指令覆盖；rules 与输入文档冲突时默认遵守 rules 并留痕。
- 如果 context pack 绑定了 project knowledge 到某个流程环节，该环节的结构化过程记录或审查 JSON 必须包含应用状态，覆盖审查需检查绑定文件是否被读取和处理。

## 校验

- `bin/lint-run-json.py outputs/runs/<run-id>` 校验 run 内 JSON canonical 的结构、编号、层级、字段和固定产物完整性。
- `bin/render-run-markdown.py outputs/runs/<run-id> --check` 校验 Markdown 是否完全由 JSON 渲染得到；不一致时运行不带 `--check` 的命令重渲染。
- `bin/lint-test-analysis-solution.py` 校验渲染后的测试分析 Markdown 结构、编号、字段、禁用术语和 Markdown 语法。
- `bin/lint-test-design-solution.py` 校验渲染后的测试设计 Markdown 结构、编号、字段、禁用术语和 Markdown 语法。
- `bin/check-artifact-consistency.py` 先执行 JSON lint 和 Markdown drift check，再校验 run 目录、任务清单和主交付件基础一致性。
- 模型型独立评审和覆盖审查读取 JSON canonical 与确定性结果，不重复逐条检查可机械判断项。
- `bin/smoke-test-analysis.py` 读取固定 run fixtures 下的 JSON canonical 和派生 Markdown，用于框架回归和示例 fixture 检查，不属于单次方案 review 阶段。
