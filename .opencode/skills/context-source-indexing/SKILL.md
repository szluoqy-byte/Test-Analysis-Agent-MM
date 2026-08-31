---
name: context-source-indexing
description: 为测试分析或设计 run 扫描已绑定 project/personal Markdown 来源的 frontmatter，直接生成 Markdown 上下文来源索引。
---

# 上下文来源索引 Skill

## 何时使用

在 run 已准备、project-key 已显式指定或可唯一推断时使用。未唯一确定 project-key 时不得读取所有项目目录正文。

## 输入

- requirement 路径、标题、关键词和可选 project-key。
- `knowledge/projects/<project-key>/**/*.md` 与 `knowledge/user/**/*.md` frontmatter。

## 执行

运行：

```text
python skills/context-source-indexing/scripts/build-context-source-index.py --run-dir outputs/runs/<run-id> ...
```

脚本直接写入 `process/context-pack.md`，只索引 `name`、`description`、`stages` 和路径，不生成 JSON，不摘录正文。

## 输出

- `process/context-pack.md`。

## 验证闭环

确认 Markdown 包含需求、project 绑定、动态来源、未扫描来源和告警章节；后续阶段只读取可用阶段包含当前阶段或 `*` 的来源。

## 约束

- 不扫描 rules；rules 由 `process/rules-pack.md` 独立索引。
- 不扫描 core knowledge。
- 不直接编辑 `.opencode/` 或 `.testagent/` 镜像。
