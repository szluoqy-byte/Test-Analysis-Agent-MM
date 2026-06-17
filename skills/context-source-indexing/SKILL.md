---
name: context-source-indexing
description: 在测试分析或测试设计开始前使用，仅索引 project/personal 扩展来源的元数据，生成 process/context-pack.json；core rules、knowledge、templates 和 skill 私有参考由对应 workflow/skill 固定引用，不进入动态索引。
---

# 上下文来源索引

本 skill 在每次测试分析或测试设计开始时使用。目标不是提前理解所有上下文正文，也不是替后续测试分析阶段做路由，而是为当前 run 建立一个轻量、可追踪的动态来源索引。

`process/context-pack.json` 是当前 run 的上下文来源事实源；`process/context-pack.md` 只由 `bin/render-run-markdown.py` 渲染给人阅读。后续 skill 必须以 JSON 为准。

本 skill 必须调用脚本生成 context pack，不得手工拼写、补写或改写 `process/context-pack.json`：

```bash
python skills/context-source-indexing/scripts/build-context-source-index.py \
  --run-dir outputs/runs/<run-id> \
  --requirement outputs/runs/<run-id>/inputs/requirement.md \
  --requirement-title "<需求标题>" \
  --keyword "<关键词>" \
  --project <project-key>
```

如果没有显式 `project-key`，不要传 `--project`。脚本会基于需求标题、需求路径和 `--keyword` 与现有 project 目录名做轻量推断；只有唯一命中时才绑定并扫描 project 来源。无法唯一命中时可用 `--project-reason` 写明未绑定原因。脚本会默认渲染 `process/context-pack.md`；只需要 JSON 时才使用 `--no-render`。

## 职责边界

- 只索引 `project` 和 `personal` 扩展来源的元数据。
- 不扫描、不摘录、不动态索引 core 层文件：根目录 `rules/*.md`、`knowledge/*.md`、`templates/` 和各 skill 私有参考文件由 workflow 或对应 skill 固定引用。
- 不读取动态来源正文来判断具体测试点、测试设计项、覆盖缺口或专项方法命中。
- 不把来源内容复制到 context pack；context pack 只记录路径、名称、描述、阶段可见性、绑定状态和告警。
- 不把 `applied`、`not_applicable`、`conflict_with_requirement` 等应用状态写入 `sources[]`；应用状态只能写入后续阶段的过程 JSON、review JSON 或 coverage JSON。
- 不把绝对路径写入 `sources[].path`；脚本输出统一使用仓库相对路径。
- 不修改 `rules/`、`knowledge/` 或 `memory/` 下的长期来源文件。

## 输入

- 当前 run 目录：`${PROJECT_ROOT}/outputs/runs/<run-id>/`。
- 已解析的需求文档路径、需求标题或关键词，用于记录本次索引背景。
- 可选 `project-key`：显式提供时优先使用；未提供时，脚本只枚举 project 一级目录名，并用需求标题、路径和关键词做唯一匹配。只有唯一确定时才扫描 project 层路径。
- 可选 `personal-key`：当前默认使用 `default`，扫描 `*/user/**/*.md`。
- 脚本：`skills/context-source-indexing/scripts/build-context-source-index.py`。
- 模板：`templates/context-pack-json-template.json` 和 `templates/context-pack-template.md`，仅作为结构和人读样式参考；实际生成以脚本输出为准。

## 执行方式

1. 从用户参数或上游流程取得 `<run-id>`、需求 Markdown 路径、需求标题、关键词、可选 `project-key` 和可选 `personal-key`。
2. 调用 `skills/context-source-indexing/scripts/build-context-source-index.py` 生成 `process/context-pack.json`。
3. 检查脚本输出的 `warnings[]`。frontmatter 缺失、非法 `stages` 或非法 `project-key` 都保留在 JSON 中，不静默忽略。
4. 不手工编辑 `process/context-pack.md`；如果需要刷新人读版，重新运行脚本或 `python bin/render-run-markdown.py outputs/runs/<run-id>`。

常用命令：

```bash
python skills/context-source-indexing/scripts/build-context-source-index.py \
  --run-dir outputs/runs/<run-id> \
  --requirement <requirement.md> \
  --requirement-title "<需求标题>" \
  --keyword "<关键词1,关键词2>"
```

带项目绑定：

```bash
python skills/context-source-indexing/scripts/build-context-source-index.py \
  --run-dir outputs/runs/<run-id> \
  --requirement <requirement.md> \
  --project <project-key> \
  --personal default
```

## 动态来源范围

当 `project-key` 已唯一确定时，扫描：

- `rules/projects/<project-key>/**/*.md`
- `knowledge/projects/<project-key>/**/*.md`
- `memory/projects/<project-key>/**/*.md`

无唯一 `project-key` 时，不扫描任何 project 目录正文，也不把所有项目目录加载进索引；只在 `projectBinding`、`unscannedProjectSources` 和 `warnings` 中记录未扫描原因。允许枚举 `rules/projects/`、`knowledge/projects/`、`memory/projects/` 的一级目录名用于唯一性判断，但不得读取候选目录下的 Markdown 正文或 frontmatter。

personal 层扫描：

- `rules/user/**/*.md`
- `knowledge/user/**/*.md`
- `memory/user/**/*.md`

扫描时跳过 `README.md` 的正文。README 只作为目录说明，不进入 `sources[]`。

## 元数据格式

每个动态来源 Markdown 文件必须在文件头提供最小 frontmatter：

```yaml
---
name: payment-risk-profile
description: 支付项目风险画像，补充支付状态、幂等、补偿和对账类覆盖关注点。
stages:
  - input-fact-modeling
  - testing-method-router
  - coverage-review
---
```

字段规则：

- `name`：必填，短名称，用于人读识别和 review 引用。
- `description`：必填，说明该来源提供什么补充价值。
- `stages`：可选。缺省或空数组表示对所有阶段可见，渲染为 `["*"]`；显式配置时只对列出的阶段可见。

`sources[]` 不写 `sourceType`、`layer`、`projectKey`、`stages` 或 `applied`。这些信息由路径和后续阶段应用记录推断：`rules/projects/<project-key>/...` 是 project rules，`knowledge/user/...` 是 personal knowledge。`project-key` 的绑定只写在顶层 `projectBinding`；阶段可见性只写为 `availableStages` 和 `availability`。

推荐阶段值：

- `input-fact-modeling`
- `clarification-gate`
- `testing-method-router`
- `test-analysis-solution-generation`
- `test-analysis-solution-review`
- `test-design-solution-generation`
- `test-design-solution-review`
- `coverage-review`

## 输出结构

脚本创建或刷新 `${PROJECT_ROOT}/outputs/runs/<run-id>/process/context-pack.json`：

```json
{
  "artifactType": "context-pack",
  "schemaVersion": "1.0",
  "title": "上下文来源索引",
  "requirement": {
    "path": "outputs/runs/<run-id>/inputs/requirement.md",
    "title": "",
    "keywords": []
  },
  "projectBinding": {
    "status": "unresolved",
    "projectKey": "",
    "reason": "未提供 project-key，且无法从输入唯一识别"
  },
  "personalBinding": {
    "status": "default",
    "personalKey": "default",
    "reason": "使用默认 personal 扩展路径"
  },
  "sources": [
    {
      "path": "knowledge/projects/payment/risk-profile.md",
      "name": "payment-risk-profile",
      "description": "支付项目风险画像，补充支付状态、幂等、补偿和对账类覆盖关注点。",
      "availableStages": ["testing-method-router", "coverage-review"],
      "availability": "restricted"
    }
  ],
  "unscannedProjectSources": [
    {
      "path": "knowledge/projects/",
      "reason": "project-key 未唯一确定"
    }
  ],
  "warnings": []
}
```

脚本保证：

- 即使没有 project/personal 命中，也必须生成 `process/context-pack.json` 和派生 `process/context-pack.md`。
- `sources` 可以为空；空列表表示本次没有动态 project/personal 来源可用。
- `sources[]` 只允许来自 `rules/projects/<project-key>/`、`knowledge/projects/<project-key>/`、`memory/projects/<project-key>/`、`rules/user/`、`knowledge/user/` 或 `memory/user/`。core rules、core knowledge、templates 和 skill 私有参考不进入 `sources[]`。
- `availableStages` 缺省时统一写 `["*"]`，`availability` 写 `all`；显式阶段列表时写 `restricted`。
- frontmatter 缺失或不合法的动态来源不得静默注入，必须在 `warnings[]` 中记录文件路径和问题，且不写入 `sources[]`。
- 如果 `project-key` 未唯一确定，`projectBinding.status` 写 `unresolved`，并在 `unscannedProjectSources[]` 记录 project 根路径未扫描原因。
- 如果未传 `--project`，但需求标题、路径或 keywords 唯一命中某个 project 目录名，`projectBinding.status` 写 `resolved`，`reason` 写明由关键词/路径推断；如果命中多个目录，保持 `unresolved` 并在 `warnings[]` 列出候选。

## 后续消费原则

后续 skill 根据当前阶段过滤 `sources[]`：

- `availableStages` 包含当前阶段，或包含 `"*"`，才允许读取对应来源正文。
- 被读取的动态来源必须在本阶段的过程 JSON、review JSON 或 coverage JSON 中记录应用状态。
- 应用状态只能使用 `applied`、`not_applicable`、`insufficient_evidence`、`conflict_with_requirement` 或 `deferred_to_review`。
- 如果动态来源与当前用户明确指令、core rules 或输入文档冲突，不在 context pack 中裁决；由读取该来源的阶段记录冲突和处理依据。

core rules、core knowledge 和 skill 私有参考不依赖 `context-pack.json` 才能生效。它们由 workflow 和 skill 明确读取，属于默认能力边界。
