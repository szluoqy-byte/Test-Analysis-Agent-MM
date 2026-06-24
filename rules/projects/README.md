# Project Rules

本目录用于保存项目级强制规则，路径格式为：

```text
rules/projects/<project-key>/**/*.md
```

未唯一确定 `project-key` 时，不得读取所有项目目录正文，避免跨项目规则污染。

项目级 rules 的优先级高于当前输入文档、memory 和 knowledge；如果与输入文档冲突，默认遵守 rules，并在过程产物中记录覆盖原因。项目级 rules 不得覆盖当前用户明确指令，也不得违反 core rules。

项目规则文件必须声明 frontmatter：

```yaml
---
name: payment-project-rules
description: 支付项目强制规则补充。
stages:
  - test-analysis-solution-generation
  - coverage-review
---
```

`stages` 可选；未配置时默认所有阶段可用。`bin/build-rules-pack.py` 读取 frontmatter 并确认正文非空，写入 `process/rules-pack.json` 的 `ruleSources[]` 索引；后续阶段按 rules-pack 中的阶段可见性读取对应 Markdown 正文并应用。
