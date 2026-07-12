# 文档导航

`docs/` 只保存面向人的架构说明和设计说明，不作为运行时事实源。运行时事实源以 `AGENTS.md`、`agents/`、`skills/`、`knowledge/`、`templates/` 和 `bin/` 为准。

## 当前有效文档

| 文档 | 用途 |
|---|---|
| `agents/file-normalization-agent.md` | 文件归一化 Agent 的能力边界和输出约定 |
| `agents/test-analysis-agent.md` | 测试分析 Agent 的能力边界和分析阶段模型 |
| `agents/test-design-agent.md` | 测试设计 Agent 的能力边界和设计阶段模型 |
| `agents/test-e2e-analysis-design-agent.md` | 端到端分析设计 Agent 的全流程编排说明 |
| `architecture/framework-overview.md` | Agent 包整体架构、关键机制和横切原则 |
| `architecture/test-analysis-design-agent-reference-architecture.md` | 测试分析与测试设计 Agent 的三层架构、贯穿式 Harness，以及 analysis/design 完整实现流程 |
| `architecture/output-artifact-contract.md` | run 目录、主交付件、过程件、review、coverage 和 final-report 的契约 |
| `architecture/knowledge-rules-memory-boundaries.md` | skills、knowledge、rules、memory、templates 和 docs 的边界 |

## 草案和归档

- `drafts/test-eval-agent.md`：未来测试评估 Agent 草案，当前不属于主链路。
- `archive/skills-architecture-optimization-analysis.md`：历史架构优化分析记录，保留用于追溯。

## 维护规则

- 修改 `agents/*.md`、`skills/*/SKILL.md` 或镜像相关配置后，运行 `python bin/sync-opencode-skills.py`。
- 修改框架 wiring、必备文件或 docs 路径后，运行 `python bin/validate-agent-runtime.py` 和 `python bin/smoke-test-analysis.py`。
- docs 中的流程描述应保持高层，不重复 `skills/*-workflow/SKILL.md` 的完整命令清单。
