# 输出产物契约

## 目标

`outputs/` 只保存运行产物。每次分析创建一个独立 run 目录，目录内按产物类别固定命名，避免不同模型、语言环境或需求文件名处理方式导致下游无法稳定定位文件。

本项目只有一个默认主交付件：`testcase-title-outline.md`。

## 目录结构

```text
outputs/
└── runs/
    └── <run-id>/
        ├── deliverables/
        │   └── testcase-title-outline.md
        ├── process/
        │   ├── task-list.md
        │   ├── context-pack.md
        │   └── clarification-session.md
        └── reports/
            └── test-analysis-report.md
```

## 产物分类

| 类别 | 路径 | 是否默认生成 | 说明 |
|---|---|---|---|
| 主交付件 | `deliverables/testcase-title-outline.md` | 是 | 唯一主交付物，按“测试场景 -> 测试点 -> 测试用例标题项”组织，不生成完整测试用例 |
| 任务清单 | `process/task-list.md` | 是 | 当前 run 的阶段顺序、状态和证据路径，是流程控制事实源 |
| 过程上下文 | `process/context-pack.md` | 是 | 当前 run 筛选出的 memory、project/personal 补充和项目上下文快照 |
| 待确认治理记录 | `process/clarification-session.md` | 有待确认候选时生成 | 记录候选问题、去重降级结果和最终待确认问题；最终展示以主交付件 `## 5. 待确认信息` 为准 |
| 过程报告 | `reports/test-analysis-report.md` | 可选 | 内部审查、追溯和质量门禁报告 |

## 命名规则

- run 目录名使用 `<YYYYMMDD-HHMMSS>-<需求文件名安全短名>-<短哈希>`。
- run 目录内文件名固定，不再使用需求文件名作为产物文件名前缀。
- 下游完整用例编写只读取 `outputs/runs/<run-id>/deliverables/testcase-title-outline.md`。
- 不生成 `<需求文件名安全短名>.test-points.md`、`<需求文件名安全短名>.testpoint-details.md` 或其他旧格式同义文件。

## 精简原则

- 主交付件必须自包含，不能要求后续使用者读取输入需求、设计方案、`process/`、`reports/` 或 memory。
- `process/task-list.md` 必须在创建 run 目录后立即生成，最终输出前所有必选阶段应为 `done`，可选阶段可为 `skipped` 并说明原因。
- `process/context-pack.md` 必须记录 project/personal 的绑定结果、已扫描来源、命中来源、未采用来源、冲突处理和后续补读建议。
- 如果 context pack 命中了 `*/projects/<project-key>/` 或 `*/user/`，后续完整用例编写需要知道的项目风险、覆盖策略、术语映射、个人关注点或判定依据必须上收到主交付件。
- 过程报告中可以包含方法路由、方法证据、覆盖审查和专家评分，但不得替代主交付件。
- `process/` 只保留运行恢复和追溯必需文件。

## 示例回归

- 示例 fixtures 固定放在 `examples/outputs/runs/<stem>-run/`，目录内部使用本契约的固定文件名。
- `bin/smoke-test-analysis.py` 读取固定 run fixtures 下的 `deliverables/testcase-title-outline.md`。
- `bin/check-artifact-consistency.py <run-dir>` 用于检查固定运行目录、任务清单、主交付件和可选过程报告之间的 `TP-*` / `ITP-*` 一致性。
