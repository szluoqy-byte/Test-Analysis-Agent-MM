# Skills 架构优化说明

当前架构采用 JSON canonical + Markdown render，并以 `SC/TP/TC` 作为主交付模型。

## 分层

| 层 | Skill | 职责 | 输出 |
|---|---|---|---|
| 入口编排 | `test-analysis-workflow` | 创建 run、编排分析链路 | `test-analysis-solution.json` |
| 入口编排 | `test-design-workflow` | 复用或创建 run、编排设计链路 | `test-design-solution.json` |
| 强制规则加载 | `bin/build-rules-pack.py` | 加载 core/project/user rules 并形成强约束事实源 | `rules-pack.json` |
| 输入建模 | `input-fact-modeling` | 抽取需求事实、设计事实和来源应用 | `input-fact-model.json` |
| 上下文索引 | `context-source-indexing` | 索引 project/personal knowledge 和 memory 动态来源元数据 | `context-pack.json` |
| 方法路由 | `testing-method-router` | 判断适用测试技术 | 方法参考记录 |
| 分析生成 | `test-analysis-solution-generation` | 生成 `SC-*` 场景树和 `TP-*` 测试点 | 分析方案 |
| 设计生成 | `test-design-solution-generation` | 在每个 `TP-*` 下生成 `TC-*` | 设计方案 |
| 用例写作 | `test-case-writing` | 从 canonical JSON 生成标准 Markdown 或扩展写作风格 | 派生阅读版/导出格式 |
| 独立评审 | review skills | 语义质量评审 | review JSON |
| 覆盖收口 | `coverage-review` | 需求到 TP、TP 到 TC 的覆盖审查 | coverage JSON |

## 核心原则

- rules 由 `process/rules-pack.json` 独立承载强制语义，后续阶段必须读取适用 rules。
- core knowledge、templates 和 skill 私有参考由 workflow 或 skill 固定读取。
- project/personal knowledge 和 memory 动态来源只通过 `context-pack.json` 暴露给后续阶段。
- 分析阶段不输出执行实例；设计阶段不改写分析层级。
- 确定性结构问题交给 Python 脚本；模型评审只处理语义质量。
