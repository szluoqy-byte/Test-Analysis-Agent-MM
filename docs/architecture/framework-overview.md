# 框架总览

本仓库是测试分析与测试设计 Agent 包。用户入口是 Agent，workflow 组织语义工作，固定脚本只负责生命周期、控制状态、稳定编号和结果校验。

## Agent 能力边界

| Agent | 目标 | 主要输入 | 主要结果 |
|---|---|---|---|
| `@file-normalization-agent` | 将 Office / Markdown 整理为输入事实源 | `.docx` / `.xlsx` / `.md` | 归一化 Markdown |
| `@test-analysis-agent` | 回答 what to test | 需求和可选设计 Markdown | 分析结果 JSON/Markdown、分析报告 |
| `@test-design-agent` | 回答 how to test | 已评审分析结果 JSON、需求/设计依据 | 设计结果 JSON/Markdown、设计报告 |
| `@test-e2e-analysis-design-agent` | 编排分析到设计 | 需求和可选设计 Markdown | 两阶段结果和报告 |

## 核心模型

- 测试分析：`SC 场景树 -> TP 测试点`。
- 测试设计：`SC 场景树 -> TP 测试点 -> TC 测试用例`。
- 分析先冻结 `process/scenario-tree.md`，再按叶子 SC 写 TP Markdown 切片。
- 设计继承分析结果 JSON 的 SC/TP，只按 TP 写 TC Markdown 切片。
- 过程语义直接保存在 Markdown；只有阶段结果和控制状态使用 JSON。

## 横切机制

- `rules-pack.md` 索引强制规则，`context-pack.md` 索引 project/personal knowledge。
- 生成时按需读取规则、上下文和 `input-fact-model.md`，不持久化生成上下文副本。
- review 处理语义质量；确定性脚本处理控制状态、编号、结果 schema 和派生 Markdown 一致性。
- coverage-review 直接审阅 Markdown 覆盖证据；final-report 是 Markdown 人审展示。
- run 的真实状态只写入 `process/*-task-list.json` 和 `process/*-work-items.json`。
- `.opencode/` 和 `.testagent/` 是生成镜像，手工源在根目录 `agents/` 和 `skills/`。

## 事实源边界

docs 只做解释。执行顺序以 `skills/*-workflow/SKILL.md` 为准；过程格式以 Markdown 模板为准；结果结构和校验以结果 JSON 模板、`bin/run_artifacts.py` 与相关 lint 为准。
