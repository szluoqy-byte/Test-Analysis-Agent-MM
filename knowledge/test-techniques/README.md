# 测试技术库

本目录维护本仓库可复用的测试技术。测试技术不是输出模板，而是支持分析阶段识别测试点，并支持设计阶段生成测试用例。

| 阶段 | 回答问题 | 主要产物 |
|---|---|---|
| Test Analysis | what to test | 覆盖维度建议、场景候选、测试点候选 |
| Test Design | how to test | 测试用例候选条件、测试数据和步骤建议 |

`test-analysis-agent` 只输出 `SC-*` 与 `TP-*`。`test-design-agent` 读取评审后的分析方案，在每个测试点下生成 `TC-*`。

方法示例中的 `testCaseHints[]` 只表示候选条件或数据组合，不是 `test-design-solution.json` 的 canonical 结构。最终测试用例必须由 `test-design-solution-generation` 按 `knowledge/test-design-solution-standard.md` 和 `templates/test-design-solution-json-template.json` 补齐 `level`、`preconditions[]`、`testData[]`、`steps[]`、`expectedResult` 和 `sourceRefs[]`。

## 技术分类

| 分类 | 分析层用途 | 设计层用途 |
|---|---|---|
| 基于规格的测试技术 | 从需求规则、流程、状态、接口、数据范围等规格信息识别测试条件和测试点 | 生成等价类、边界、判定、状态、接口和场景类测试用例 |
| 基于经验的测试技术 | 根据历史缺陷、专家经验和易错点识别补充风险 | 生成风险补充测试用例 |
| 基于风险的测试策略 | 根据业务影响和失败后果识别优先级和风险确认点 | 调整测试用例覆盖深度 |
| 基于质量属性的测试技术 | 从性能、可靠性、恢复性等质量属性识别专项测试点 | 生成质量属性相关测试用例 |

## 使用规则

1. `testing-method-router` 只选择适用技术，不直接生成主交付件。
2. 专项方法参考产出覆盖维度建议和候选测试点。
3. `test-analysis-solution-generation` 将候选归并为场景树和测试点。
4. `test-design-solution-generation` 基于测试点生成测试用例。
5. 缺少判定依据时，不编造错误码、提示文案、状态值或阈值。
