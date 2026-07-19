# 框架总览

本仓库是测试分析与测试设计 Agent 包。用户入口是 Agent，workflow 和脚本是 Agent 内部执行机制。

## Agent 能力边界

| Agent | 目标 | 主要输入 | 主要输出 |
|---|---|---|---|
| `@file-normalization-agent` | 把 Office / Markdown 输入整理为下游可读 Markdown 事实源 | `.docx` / `.xlsx` / `.md` | 归一化 Markdown、conversion metadata |
| `@test-analysis-agent` | 回答 what to test | 已归一化需求和可选设计方案 | `test-analysis-solution.json/.md`、分析 final report |
| `@test-design-agent` | 回答 how to test | 已评审测试分析方案、需求/设计依据 | `test-design-solution.json/.md`、设计 final report |
| `@test-e2e-analysis-design-agent` | 编排分析到设计的端到端流程 | 已归一化需求和可选设计方案 | 分析/设计交付件和最终报告 |

## 核心模型

- 测试分析输出 `SC 场景树 -> TP 测试点`。
- 测试设计输出 `SC 场景树 -> TP 测试点 -> TC 测试用例`。
- 分析阶段先冻结 `process/scenario-tree.json`，再按叶子 SC 生成 TP 切片。
- 设计阶段继承分析方案中的 SC/TP，不改写分析层级，只按 TP 生成 TC 切片。
- JSON canonical 是事实源，Markdown 由脚本派生。

## 横切机制

- `rules-pack` 独立索引强制规则；后续阶段按 `ruleSources[]` 读取适用 rules 正文。
- `context-pack` 只索引 project/personal knowledge 动态来源。
- `generationContext` 由固定脚本写入 scenario-tree、slice、review 和 coverage JSON，用于生成前工作包，不进入最终 deliverables。
- review 处理语义质量，deterministic lint 处理结构、编号、字段和 Markdown 一致性。
- 多步骤 skill 用阶段索引描述静态执行契约，并在同编号的 `各阶段执行要求` 中展开；run 的真实状态只写入 `process/*-task-list.json`，由 `bin/lint-skill-step-contract.py` 防止 skill 文档的阶段编号或标题漂移。
- coverage-review 基于 fact-coverage-map 做覆盖门禁；final-report 只从已审查的覆盖证据图生成人审报告，不触发返工。
- `.opencode/` 和 `.testagent/` 是生成镜像，手工源在根目录 `agents/` 和 `skills/`。

## 事实源边界

docs 是解释层，不参与运行。具体执行顺序以 `skills/*-workflow/SKILL.md` 为准；结构和校验以 `templates/`、`bin/run_artifacts.py`、`bin/lint-run-json.py` 和相关脚本为准。
