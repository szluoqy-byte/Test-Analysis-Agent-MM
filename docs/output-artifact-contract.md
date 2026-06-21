# 输出产物契约

本项目有两个主交付件：

- `deliverables/test-analysis-solution.json`：测试分析方案，schema `2.0`，结构为 `SC 场景树 -> TP 测试点`。
- `deliverables/test-design-solution.json`：测试设计方案，schema `2.0`，结构为 `SC 场景树 -> TP 测试点 -> TC 测试用例`。

JSON 是 run 内过程产物、主交付件和 review/coverage 结果的唯一事实源；Markdown 是派生的人类阅读版，不手工维护。若 JSON 与 Markdown 不一致，以 JSON 为准，运行 `python bin/render-run-markdown.py outputs/runs/<run-id>` 重新渲染。

派生 Markdown 必须保留 JSON 层级。测试分析 Markdown 保留章节层级：`SC-001` 渲染为 `###`，`SC-001-001` 渲染为 `####`，`SC-001-001-001` 渲染为 `#####`；叶子 SC 下的 `TP-*` 比父级 SC 低一层。测试设计 Markdown 面向脑图导入优化，不额外增加“测试场景与测试设计”章节层级：`SC-001` 渲染为 `##`，`SC-001-001` 渲染为 `###`，常规叶子 SC 下 `TP-*` 渲染为 `####`，`TC-*` 渲染为 `#####`；如 3 层 SC 导致 TP 已是 `#####`，TC 使用 TP 下的列表节点兜底，避免 6 级标题在 emmx/脑图解析中截断。

## 运行目录

```text
outputs/
  input-cache/
  runs/
    <run-id>/
      inputs/
      deliverables/
        test-analysis-solution.json
        test-analysis-solution.md
        test-design-solution.json
        test-design-solution.md
      process/
        task-list.json
        task-list.md
        context-pack.json
        context-pack.md
        input-fact-model.json
        input-fact-model.md
      reports/
        test-analysis-solution-review.json
        test-analysis-solution-review.md
        test-design-solution-review.json
        test-design-solution-review.md
        coverage-review.json
        coverage-review.md
```

Office 输入必须先通过 `@file-normalization-agent` 归一化为 Markdown。测试分析和测试设计 workflow 本身只消费已归一化 Markdown 或 JSON canonical 输入。

## 测试分析主交付件

```json
{
  "artifactType": "test-analysis-solution",
  "schemaVersion": "2.0",
  "title": "<需求名称> 测试分析方案",
  "scope": [
    {"field": "需求名称", "content": "<需求名称>"}
  ],
  "scenarios": [
    {
      "id": "SC-001",
      "title": "<一级场景>",
      "fields": [{"field": "场景目标", "content": "<目标>"}],
      "children": [
        {
          "id": "SC-001-001",
          "title": "<叶子场景>",
          "fields": [{"field": "场景目标", "content": "<目标>"}],
          "testPoints": [
            {
              "id": "TP-001",
              "title": "E2E场景测试",
              "objective": "<验证目标>",
              "basisRefs": [{"source": "<来源>", "location": "<位置>", "description": "<依据>"}]
            }
          ]
        }
      ]
    }
  ]
}
```

规则：

- `SC-*` 最多 3 层。
- 非叶子场景只包含 `children[]`，叶子场景包含 `testPoints[]`。
- `TP-*` 全局连续编号。
- 每个叶子场景必须包含 `E2E场景测试`。
- 分析方案不包含测试用例、测试数据、步骤或预期结果。

## 测试设计主交付件

```json
{
  "artifactType": "test-design-solution",
  "schemaVersion": "2.0",
  "title": "<需求名称> 测试设计方案",
  "inputs": [
    {"field": "测试分析方案来源", "content": "deliverables/test-analysis-solution.json"}
  ],
  "scenarios": [
    {
      "id": "SC-001",
      "title": "<一级场景>",
      "children": [
        {
          "id": "SC-001-001",
          "title": "<叶子场景>",
          "testPoints": [
            {
              "id": "TP-001",
              "title": "E2E场景测试",
              "objective": "<继承分析方案>",
              "basisRefs": [],
              "testCases": [
                {
                  "id": "TC-001",
                  "title": "<测试用例标题>",
                  "level": "Level 1",
                  "preconditions": ["<前置条件>"],
                  "testData": [
                    {"name": "<字段>", "value": "<值>", "description": "<说明>"}
                  ],
                  "steps": [
                    {"stepNo": 1, "action": "<操作>", "expected": "<步骤预期>"}
                  ],
                  "expectedResult": "<最终预期>",
                  "sourceRefs": [{"source": "<来源>", "location": "<位置>", "description": "<依据>"}]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

规则：

- 设计方案完整继承分析方案中的 `SC-*` 和 `TP-*`。
- 每个 `TP-*` 下至少有 1 个 `TC-*`。
- `TC-*` 全局连续编号。
- `level` 使用 `Level 0` 到 `Level 4`。
- `testData[]` 使用 `{name, value, description}`。
- `steps[]` 使用 `{stepNo, action, expected}`。
- 接口类用例不写完整裸 URL。
- 新 run 只支持 schemaVersion 2.0，不提供历史结构自动迁移分支。

## 校验

- `bin/lint-run-json.py outputs/runs/<run-id>` 校验 JSON canonical 的结构、编号、层级、字段和固定产物完整性。
- `bin/render-run-markdown.py outputs/runs/<run-id> --check` 校验 Markdown 是否完全由 JSON 渲染得到。
- `bin/lint-test-analysis-solution.py` 校验渲染后的测试分析 Markdown。
- `bin/lint-test-design-solution.py` 校验渲染后的测试设计 Markdown。
- `bin/check-artifact-consistency.py` 校验 run 目录、任务清单和主交付件基础一致性。
- `bin/smoke-test-analysis.py` 用于框架回归和示例 fixture 检查。
