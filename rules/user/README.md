# User Rules

本目录用于保存当前使用者的本地强制规则，路径格式为：

```text
rules/user/**/*.md
```

个人 rules 用于表达本地强制约束，例如固定输出约束、个人审核要求或本地环境限制。它们的优先级高于当前输入文档、memory 和 knowledge，但不得覆盖当前用户明确指令、core rules 或 project rules。

规则文件必须声明 frontmatter：`name`、`description`，可选 `stages`。`bin/build-rules-pack.py` 读取 frontmatter 并确认正文非空，写入 `process/rules-pack.json` 的 `ruleSources[]` 索引；后续阶段按 rules-pack 中的阶段可见性读取对应 Markdown 正文并应用。
