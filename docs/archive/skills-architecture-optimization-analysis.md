# Skills 架构优化记录

本文记录当前收敛后的职责边界。历史的“所有过程件使用 JSON，再渲染 Markdown”方案已退役。

| 能力 | 当前实现 | 产物 |
|---|---|---|
| 强制规则索引 | `bin/build-rules-pack.py` | `rules-pack.md` |
| 动态上下文索引 | `context-source-indexing` | `context-pack.md` |
| 输入事实建模 | `input-fact-modeling` | `input-fact-model.md` |
| 方法路由 | `testing-method-router` | `testing-method-routing.md` |
| SC/TP 生成 | analysis generation + Markdown 切片 | `scenario-tree.md`、`test-point-slices/*.md` |
| TC 生成 | design generation + Markdown 切片 | `test-case-slices/*.md` |
| 工作项控制 | staged scripts | `*-work-items.json` |
| 结果固化 | `bin/finalize-deliverable.py` | `deliverables/test-*-solution.json/.md` |
| 语义评审与覆盖 | review / coverage skills | `process/reviews/*.md`、`*-fact-coverage-map.md` |
| 最终人审报告 | `final-report-generation` | `reports/*-final-report.md` |

核心收敛原则：

- 过程语义只维护 Markdown，避免 JSON 语法修复和 Markdown 派生的双重成本。
- 控制 JSON 只记录生命周期、状态、内容哈希和稳定编号。
- 结果 JSON 只在阶段边界固化，作为跨阶段和机器消费接口。
- review 或 coverage 缺口通过 `reopen-run-items.py` 回到具体 Markdown 切片返工。
