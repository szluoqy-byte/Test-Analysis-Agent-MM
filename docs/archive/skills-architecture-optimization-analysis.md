# Skills 架构优化说明

当前架构采用 JSON canonical + Markdown render，并以 `SC/TP/TC` 作为主交付模型。

## 分层

| 层 | Skill | 职责 | 输出 |
|---|---|---|---|
| 入口编排 | `test-analysis-workflow` | 创建 run、编排分析链路 | `test-analysis-solution.json` |
| 入口编排 | `test-design-workflow` | 复用或创建 run、编排设计链路 | `test-design-solution.json` |
| 全流程编排 | `test-analysis-design-workflow` | 优先用独立 subagent 执行分析和设计，通过分析 JSON 显式交接；不支持 subagent 时 fallback 为 workflow 串联 | 分析/设计交付件与 final-report |
| 强制规则索引 | `bin/build-rules-pack.py` | 索引 core/project/user rules 元数据；后续阶段按 `ruleSources[]` 读取适用规则正文并形成强约束事实 | `rules-pack.json` |
| 生成前工作包 | `bin/build-generation-context.py` / 初始化脚本 | 按阶段把适用 rules 正文、可见动态来源、事实候选和读入计划写入 `generationContext` | process/review/coverage JSON |
| 输入建模 | `input-fact-modeling` | 抽取需求事实、设计事实和来源应用 | `input-fact-model.json` |
| 上下文索引 | `context-source-indexing` | 索引 project/personal knowledge 动态来源元数据 | `context-pack.json` |
| 方法路由 | `testing-method-router` | 判断适用测试技术 | 方法参考记录 |
| 分析生成 | `test-analysis-solution-generation` | 先生成冻结 SC 树，再按叶子 SC 生成 TP 切片并合并 | `scenario-tree.json` / 分析方案 |
| 设计生成 | `test-design-solution-generation` | 按每个 `TP-*` 生成 TC 切片并合并 | `test-case-slices/` / 设计方案 |
| 分段机械操作 | `bin/list-staged-work-items.py` / `bin/init-staged-slices.py` / `bin/merge-staged-slices.py` / `bin/check-staged-run.py` | 状态查看、批量初始化、批量合并和固定检查，避免临时脚本处理 JSON | work-items / slice / checks |
| 用例写作 | `test-case-writing` | 从 canonical JSON 生成标准 Markdown 或扩展写作风格 | 派生阅读版/导出格式 |
| 独立评审 | review skills | 语义质量评审 | review JSON |
| 覆盖证据图 | `bin/build-fact-coverage-map.py` | 逐 FACT 整理到 SC/TP/TC 的候选覆盖链路，供 coverage-review 审查 | fact-coverage-map JSON/Markdown |
| 覆盖收口 | `coverage-review` | 基于 fact-coverage-map 执行需求到 TP、TP 到 TC 的覆盖门禁 | coverage JSON |
| 最终人审报告 | `final-report-generation` / `bin/build-final-report.py` | 从已审查的 fact-coverage-map 展示 FACT 最终被哪些 SC/TP/TC 覆盖，不触发返工 | final-report JSON/Markdown |
| 返工定位 | `bin/apply-review-findings.py` / `bin/apply-coverage-gaps.py` | 将 review blocking 或 coverage gap 定位到具体 slice 并重开 work item | work-items JSON |

## 核心原则

- rules 由 `process/rules-pack.json` 独立索引强制语义，后续阶段必须读取适用 rules 正文。
- core knowledge、templates 和 skill 私有参考由 workflow 或 skill 固定读取。
- project/personal knowledge 动态来源只通过 `context-pack.json` 暴露给后续阶段。
- `generationContext` 是生成前工作包：脚本准备上下文，AI 只填当前工作单元的语义内容；它不进入最终 deliverables。
- 分析阶段先冻结 SC 再展开 TP；设计阶段按 TP 展开 TC，且不改写分析层级。
- 确定性结构问题交给 Python 脚本；模型评审只处理语义质量。
- review 发现 blocking 或 coverage-review 发现覆盖缺口后，必须先运行 `bin/apply-review-findings.py` 或 `bin/apply-coverage-gaps.py`，通过结构化 location 回到对应 TP/TC 切片修复，再重新执行切片 review、脚本合并、最终 review、fact-coverage-map、coverage 和一致性检查；不得直接编辑最终 Markdown、绕过切片手改主交付件或临时创建脚本处理 JSON。
- final-report 是最终人审件，位于 coverage-review 通过并返工闭环之后；它只从已审查的 fact-coverage-map 展示输入 FACT 与最终 SC/TP/TC 覆盖关系，不输出 `coverageGaps[]`，不参与自动返工链路。
- e2e 全流程推荐 subagent-first：analysis 和 design 放入独立会话以降低上下文互相影响；workflow skill 仍是执行契约，阶段交接只依赖 canonical JSON 和固定报告文件。

## Skill 编写契约

本项目的 `SKILL.md` 兼容 Agent Skills 的目录和 frontmatter 约定：

- skill 目录至少包含 `SKILL.md`，可选 `scripts/`、`references/` 和其他资源目录。
- frontmatter 必须包含 `name` 和 `description`；`name` 与目录名一致，`description` 同时说明“做什么”和“何时使用”。
- `SKILL.md` 保持核心流程和高价值易错点，详细标准、矩阵、参考资料或脚本放到 `references/`、`scripts/`，并在正文说明何时读取或调用。
- 每个 skill 正文至少提供：何时使用、输入、执行步骤、输出、验证闭环、约束/易错点，便于 agent 激活后按步骤推进和自检。
- 多步骤 workflow、生成、coverage、final-report 和写作类 skill 使用阶段索引，按连续的 `- [ ] Step N: ...` 列出静态执行契约，并在同编号、同标题的 `各阶段执行要求` 中展开关键脚本、编辑对象和验证门禁；真实 run 状态只写入 `process/*-task-list.json`。
- 脆弱链路把脚本准备、AI 语义填写、review/coverage 和合并收口放入对应阶段要求，由 `bin/lint-skill-step-contract.py` 校验阶段索引和详细展开一致，避免维护独立流程副本。
- 非显而易见的失败模式必须写入 `易错点`，例如“不要自动运行分析”“不要把方法路由写成交付字段”“不要在 final-report 阶段新增 missing 判断”。
- 命令从仓库根目录执行，因此命令示例使用仓库相对路径；skill 私有资源说明优先使用 `references/...`、`scripts/...` 的相对写法。

`bin/validate-agent-runtime.py` 会校验 skill frontmatter、行数、正文结构、必需文件和 runtime wiring；`bin/lint-skill-step-contract.py` 负责校验关键多步骤 skill 的阶段索引和同编号详细展开。修改 skill 后必须运行 `python bin/sync-opencode-skills.py` 同步 `.opencode` 和 `.testagent` 镜像。

## Best Practices 对照决策

| 官方实践 | 当前处理 |
|---|---|
| Start from real expertise | 保留项目内真实 SC/TP/TC、JSON canonical、rules/context-pack、切片返工等专有流程，不改成泛化测试理论 |
| Refine with real execution | 保留 smoke fixture、runtime 校验和示例 run 校验，作为 skill 文案回归依据 |
| Spending context wisely | `SKILL.md` 控制在 500 行以内；长参考保留在 `references/`、`knowledge/` 或脚本中按需读取 |
| Match specificity to fragility | 对 schema、切片、review、coverage、final-report 等脆弱链路使用明确脚本和顺序；对测试方法参考保留灵活性 |
| Provide defaults, not menus | workflow 使用固定默认脚本和固定产物路径，备选路径只作为异常分支说明 |
| Favor procedures over declarations | 核心 skill 使用 checklist、执行步骤和验证闭环，而不是只声明产物应该正确 |
| Gotchas sections | 高风险点保留在 `约束`、`禁止项`、`防卡住规则` 中；不为低风险 skill 额外堆叠重复 gotchas |
| Templates for output format | 继续使用 `templates/*.json` 与 Markdown render 脚本；不把长模板塞入 `SKILL.md` |
| Checklists for multi-step workflows | 入口 workflow、归一化、生成、coverage、final-report 和写作类 skill 使用可校验的阶段索引；运行状态由 task-list JSON 维护 |
| Validation loops | 每个关键 skill 保留验证闭环；coverage/review 返工回到 slice，不直接改最终 Markdown |
| Plan-validate-execute | SC 树、TP 切片、TC 切片、fact-coverage-map 和 final-report 都先由脚本生成结构，再由 AI 填语义，再由脚本校验 |
| Bundling reusable scripts | 重复 JSON 初始化、合并、渲染、lint、覆盖图和报告生成继续使用 `bin/` 或 skill 私有 `scripts/` 固定脚本 |
