# 输出产物契约

本项目有两个主交付件：测试分析阶段默认生成 `test-analysis-solution.md`；测试设计阶段在已评审测试分析方案基础上生成 `test-design-solution.md`。

## 运行目录

```text
outputs/
  runs/
    <run-id>/
      deliverables/
        test-analysis-solution.md
        test-design-solution.md
      process/
        task-list.md
        context-pack.md
        clarification-session.md
      reports/
        test-analysis-report.md
```

新建完整 run 时，`run-id` 固定使用 `python bin/generate-run-id.py` 生成，格式为 `<YYYYMMDD-HHMMSS>`。同一轮分析、修正、质量门禁重跑和报告刷新必须复用已创建的 run 目录；测试设计阶段优先复用上游测试分析方案所在 run。

## 固定产物

| 类型 | 路径 | 必须生成 | 说明 |
|---|---|---|---|
| 测试分析主交付件 | `deliverables/test-analysis-solution.md` | 分析阶段是 | 按“测试场景 -> 测试点 -> 测试点明细”组织，不生成测试设计项或完整测试用例 |
| 测试设计主交付件 | `deliverables/test-design-solution.md` | 设计阶段是 | 按“测试场景 -> 测试点 -> 测试点明细 -> 测试设计项”组织，不生成完整测试用例 |
| 任务清单 | `process/task-list.md` | 是 | 当前 run 的流程事实源，记录阶段顺序、状态和证据路径 |
| 上下文包 | `process/context-pack.md` | 是 | 记录适用 rules、Rules 与输入冲突、core/project/personal 来源绑定、命中、未采用来源、项目知识阶段绑定和补读建议 |
| 待确认治理记录 | `process/clarification-session.md` | 有待确认候选时生成 | 记录候选问题、去重降级结果和预期结果兜底清单；不写入主交付件章节 |
| 过程分析报告 | `reports/test-analysis-report.md` | 可选 | 记录方法证据、覆盖审查、独立评审和质量门禁 |

## 测试分析主交付件结构

主交付件只使用中文术语和固定缩写：测试场景 `SC-*`、测试点 `TP-*`、测试点明细 `TP-*-*`，不展开英文全名，不使用其他编号体系。

主交付件必须只面向测试分析方案：

```markdown
# <需求名称> 测试分析方案

## 1. 需求范围

## 2. 测试场景与测试点

### SC-001 <测试场景名称>

#### TP-001 <测试点>

##### TP-001-001 <测试点明细>

- 测试点详情：<说明该分支需要验证什么。>

- 预期结果：<明确预期结果或待人工分析确认>
```

## 测试设计主交付件结构

测试设计方案只使用中文术语和固定缩写：测试场景 `SC-*`、测试点 `TP-*`、测试点明细 `TP-*-*`、测试设计项 `TDI-*`，不展开英文全名，不使用其他编号体系。

```markdown
# <需求名称> 测试设计方案

## 1. 设计输入

## 2. 测试场景与测试设计

### SC-001 <测试场景名称>

#### TP-001 <测试点>

##### TP-001-001 <测试点明细>

- 测试点详情：<来自测试分析方案的测试点详情。>

| 测试设计项 ID | 条件/数据/状态/组合 | 预期结果 |
|---|---|---|
| TDI-001 | <代表性条件、数据、状态或组合> | <明确预期结果或待人工分析确认> |
```

## 预期结果兜底

- `预期结果` 只能写需求或设计方案明确支持的简短判定结果。
- 如果需求和设计方案没有说明错误提示、状态变化、错误码、接口返回内容、消息发送结果或数据记录变化，写 `待人工分析确认`。
- 不得为缺口新增 `## 3. 未明确规则`。
- 不得在主交付件输出独立待确认信息清单。

## 下游消费

- 后续人工评审或 `test-design-agent` 只读取 `outputs/runs/<run-id>/deliverables/test-analysis-solution.md` 即可理解测试场景、测试点和测试点明细。
- 后续完整用例写作或自动化设计只读取 `outputs/runs/<run-id>/deliverables/test-design-solution.md` 即可理解测试场景、测试点明细、代表性设计项和预期结果。
- 过程报告、context pack 和 clarification session 是审查证据，不是主交付件的必读前置。
- 如果 context pack 命中了 `*/projects/<project-key>/` 或 `*/user/`，后续理解测试分析方案需要知道的项目风险、覆盖策略、术语映射、个人关注点或判定依据必须上收到主交付件。
- 如果 context pack 登记了适用 rules，后续生成、评审和覆盖审查必须应用、解释不适用，或记录被当前用户明确指令覆盖；rules 与输入文档冲突时默认遵守 rules 并留痕。
- 如果 context pack 绑定了 project knowledge 到某个流程环节，该环节的过程报告或审查记录必须包含应用状态，覆盖审查需检查绑定文件是否被读取和处理。

## 校验

- `bin/lint-test-analysis-solution.py` 校验主交付件结构和标题。
- `bin/lint-test-design-solution.py` 校验测试设计主交付件结构和标题。
- `bin/check-artifact-consistency.py` 校验 run 目录、任务清单和主交付件基础一致性。
- `bin/smoke-test-analysis.py` 读取固定 run fixtures 下的 `deliverables/test-analysis-solution.md`，用于框架回归和示例 fixture 检查，不属于单次方案 review 阶段。
