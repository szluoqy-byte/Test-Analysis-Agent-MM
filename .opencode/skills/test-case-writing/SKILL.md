---
name: test-case-writing
description: 在测试设计方案 JSON 已生成后使用，负责将 canonical 测试用例设计转换为标准 Markdown 或后续扩展的不同写作风格/交付格式；不改变测试覆盖事实。
---

# 测试用例写作

本 skill 是测试设计链路的表达适配层。它只回答“测试用例如何写出来给人或平台消费”，不回答“应该设计哪些测试用例”。

## 何时使用

在 `deliverables/test-design-solution.json` 已生成并通过确定性校验后使用。不要在 TC 生成前使用，也不要用它修改测试覆盖事实。

## 职责边界

- 读取 `deliverables/test-design-solution.json` 作为唯一事实源。
- 默认生成标准人读版 `deliverables/test-design-solution.md`。
- 支持后续扩展不同写作风格，例如简洁评审版、详细执行版、接口测试版、平台导入版或自动化候选版。
- 不新增、删除、合并或改写 `SC-*`、`TP-*`、`TC-*`。
- 不改变 `level`、`testData[]`、`steps[]`、`expectedResult`、`sourceRefs[]` 的事实含义。
- 不把写作结果反向覆盖 canonical JSON。

## 输入

- 当前 run 目录：`outputs/runs/<run-id>/`。
- 主事实源：`outputs/runs/<run-id>/deliverables/test-design-solution.json`。
- `process/rules-pack.json` 中对 `test-case-writing` 可见的 core/project/user rules 索引及对应 Markdown 正文。
- 可选：`process/context-pack.json` 中对 `test-case-writing` 可见的 project/personal 写作偏好、平台字段映射、命名风格或导入约束。
- 模板：`templates/test-design-solution-template.md` 作为标准 Markdown 阅读版样式参考。
- 公共写作标准：`knowledge/test-case-writing-standard.md`，用于理解 canonical JSON 中所有 TC 字段的通用写法。
- 共享写作风格：`knowledge/test-case-writing-styles/`，用于理解 canonical JSON 中 GUI、API、CLI 用例字段的表达约束。
- 脚本：`bin/render-run-markdown.py` 作为默认确定性写作器。

## 默认标准 Markdown 写作

标准 Markdown 必须由脚本生成：

```bash
python bin/render-run-markdown.py outputs/runs/<run-id>
python bin/render-run-markdown.py outputs/runs/<run-id> --check
python bin/lint-test-design-solution.py outputs/runs/<run-id>/deliverables/test-design-solution.md
```

不得手工编辑 `deliverables/test-design-solution.md`。如果 Markdown 与 JSON 不一致，以 JSON 为准，重新渲染 Markdown。

## 执行步骤

1. 读取 `deliverables/test-design-solution.json`、适用 rules 和可见动态来源。
2. 默认调用 `bin/render-run-markdown.py` 生成或检查标准 Markdown。
3. 运行 Markdown lint；失败时回到 canonical JSON 或渲染脚本修复。
4. 若扩展其他写作风格，先确认该风格不会改变覆盖事实，再输出派生文件。

## 风格扩展规则

新增写作风格时，应优先新增脚本、模板或 writer profile，而不是修改 `test-design-solution-generation`：

- `standard-markdown`：默认人读版，输出 `deliverables/test-design-solution.md`。
- `review-brief`：更短的评审版，只保留关键步骤、核心数据和最终预期。
- `execution-detail`：详细执行版，强调前置条件、操作步骤和观察点。
- `interface-case`：接口测试版，突出接口、参数、响应、鉴权、幂等和异常返回字段。
- `platform-import`：测试管理平台导入版，可输出 CSV/XLSX/JSONL 等平台字段格式。
- `automation-candidate`：自动化候选版，只输出可自动化评估的字段映射和稳定断言候选，不生成脚本。

风格写作可以重排字段、改写标题、调整自然语言详略，但必须保持以下约束：

- `id` 不变。
- 覆盖关系不变。
- 测试数据事实不变。
- 步骤语义不变。
- 所有 TC 字段表达不得背离 `knowledge/test-case-writing-standard.md` 的公共写作规范。
- GUI、API、CLI 字段表达不得背离 `knowledge/test-case-writing-styles/` 中对应执行形态的约束。
- 最终预期不新增无依据业务事实。
- 写作表达必须先筛选 `process/rules-pack.json` 的 `ruleSources[]`，读取对 `test-case-writing` 可见的规则正文并遵守；rules 与个人偏好或动态来源冲突时，以 rules 为准。
- 来源引用不丢失；如目标格式不支持完整来源引用，必须在配套说明或 sidecar 文件中保留。

## 输出

- 默认输出 `deliverables/test-design-solution.md`。
- 未来扩展风格可以输出独立派生文件或 sidecar，但必须声明它是 JSON 的派生表达。
- 所有输出都不得成为后续机器流程的事实源。

## 动态来源应用

如果 `process/context-pack.json` 中存在对 `test-case-writing` 可见的 project/personal 来源，只能读取与写作表达、平台字段映射或风格偏好相关的正文。读取后必须在 review、coverage 或写作产物说明中记录应用状态。

personal 偏好只影响表达风格，不得改变测试覆盖事实。project 写作约束只影响字段映射、命名口径或导入格式，不得覆盖 schemaVersion 2.0 的 canonical 字段。

## 禁止项

- 不生成或修改 `deliverables/test-design-solution.json` 中的测试用例事实。
- 不把 Markdown 当作后续流程事实源。
- 不在写作阶段补造接口、字段、状态、错误码、错误提示、阈值或业务结果。
- 不生成自动化脚本。
- 不绕过 `bin/render-run-markdown.py --check` 和 `bin/lint-test-design-solution.py`。

## 验证闭环

默认 Markdown 写作完成后运行 `python bin/render-run-markdown.py outputs/runs/<run-id> --check` 和 `python bin/lint-test-design-solution.py outputs/runs/<run-id>/deliverables/test-design-solution.md`。失败时只修改 canonical JSON 或渲染脚本，再重新生成 Markdown。
