# 输出产物契约

本项目只有一个默认主交付件：`test-design-solution.md`。

## 运行目录

```text
outputs/
  runs/
    <run-id>/
      deliverables/
        test-design-solution.md
      process/
        task-list.md
        context-pack.md
        clarification-session.md
      reports/
        test-analysis-report.md
```

## 固定产物

| 类型 | 路径 | 必须生成 | 说明 |
|---|---|---|---|
| 主交付件 | `deliverables/test-design-solution.md` | 是 | 唯一主交付物，按“测试场景 -> 测试点 -> 测试设计项”组织，不生成完整测试用例 |
| 任务清单 | `process/task-list.md` | 是 | 当前 run 的流程事实源，记录阶段顺序、状态和证据路径 |
| 上下文包 | `process/context-pack.md` | 是 | 记录 core/project/personal 来源绑定、命中、未采用来源、项目知识阶段绑定和补读建议 |
| 待确认治理记录 | `process/clarification-session.md` | 有待确认候选时生成 | 记录候选问题、去重降级结果和预期结果兜底清单；不写入主交付件章节 |
| 过程分析报告 | `reports/test-analysis-report.md` | 可选 | 记录方法证据、覆盖审查、独立评审和质量门禁 |

## 主交付件结构

主交付件只使用中文术语和固定缩写：测试场景 `SC-*`、测试点 `TP-*`、测试设计项 `TDI-*`，不展开英文全名，不使用其他编号体系。

主交付件必须只面向测试设计方案：

```markdown
# <需求名称> 测试设计方案

## 1. 需求范围

## 2. 测试场景与测试设计

### 场景 SC-001：<测试场景名称>

#### 测试点 TP-001：<测试点>

| 测试设计项 ID | 测试设计项 | 预期结果 |
|---|---|---|
| TDI-001 | <代表性条件、数据、状态或组合> | <明确预期结果或待人工分析确认> |
```

## 预期结果兜底

- `预期结果` 只能写需求或设计方案明确支持的简短判定结果。
- 如果需求和设计方案没有说明错误提示、状态变化、错误码、接口返回内容、消息发送结果或数据记录变化，写 `待人工分析确认`。
- 不得为缺口新增 `## 3. 未明确规则`。
- 不得在主交付件输出独立待确认信息清单。

## 下游消费

- 下游测试设计评审、完整用例写作或自动化设计只读取 `outputs/runs/<run-id>/deliverables/test-design-solution.md` 即可理解测试场景、测试点和设计项。
- 过程报告、context pack 和 clarification session 是审查证据，不是主交付件的必读前置。
- 如果 context pack 命中了 `*/projects/<project-key>/` 或 `*/user/`，后续理解测试设计方案需要知道的项目风险、覆盖策略、术语映射、个人关注点或判定依据必须上收到主交付件。
- 如果 context pack 绑定了 project knowledge 到某个流程环节，该环节的过程报告或审查记录必须包含应用状态，覆盖审查需检查绑定文件是否被读取和处理。

## 校验

- `bin/lint-test-design-solution.py` 校验主交付件结构和表头。
- `bin/check-artifact-consistency.py` 校验 run 目录、任务清单和主交付件基础一致性。
- `bin/smoke-test-analysis.py` 读取固定 run fixtures 下的 `deliverables/test-design-solution.md`。
