# User Rules

本目录用于保存当前使用者的本地强制规则，路径格式为：

```text
rules/user/**/*.md
```

个人 rules 用于表达本地强制约束，例如固定输出约束、个人审核要求或本地环境限制。它们的优先级高于当前输入文档、memory 和 knowledge，但不得覆盖当前用户明确指令、core rules 或 project rules。

动态来源文件必须声明 frontmatter：`name`、`description`，可选 `stages`。`context-source-indexing` 只索引 frontmatter，后续阶段按 `sources[]` 可见性读取正文。
