# 框架与分析术语表

本文件保存测试分析框架内稳定复用的术语。它属于 Knowledge 层，用于统一 skill、template 和 quality gate 对核心概念的理解；具体业务域术语和项目专属含义应放在 `memory/domains/*.md` 或 `memory/project-memory.md`。

## 稳定术语

| 术语 | 含义 | 备注 |
|---|---|---|
| 需求文档 | 输入给 Agent 的 Markdown 产品或业务需求说明 | v1 只支持单文件 |
| 测试点 | 采用 `knowledge/testpoint-standard.md` 中的定义 | 不是测试用例 |
| 需求依据 | 测试点对应的需求标题、段落、表格行或规则摘要 | 用于可追踪性 |
| 方法证据 | 专项测试方法分析后的 `ME-*` 证据摘要 | 用于证明测试理论被实际应用 |
| 记忆上下文包 | 每次分析前从长期 memory 中筛选出的本次上下文摘要 | 写入 `${PROJECT_ROOT}/outputs/runs/<run-id>/process/context-pack.md`，是运行产物 |
| 业务域分片 | 某个业务或项目子域的长期 memory 文件 | 位于 `memory/domains/*.md`，由加载流程自动扫描 |
