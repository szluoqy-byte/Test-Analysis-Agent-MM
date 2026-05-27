# 记忆更新建议模板

```markdown
## 建议沉淀的记忆更新

| 层级 | 类型 | 建议写入位置 | 内容 | 依据 | 是否需人工确认 |
|---|---|---|---|---|---|
| project | 项目事实 | memory/project-memory.md |  |  | 是 |
| project | 项目事实 | memory/projects/<project-key>/project-memory.md |  |  | 是 |
| project | 项目专属术语 | memory/domains/<业务域>.md 或 memory/project-memory.md |  |  | 是 |
| project | 项目专属术语 | memory/projects/<project-key>/domains/<业务域>.md 或 memory/projects/<project-key>/project-memory.md |  |  | 是 |
| project | 团队输出偏好 | memory/project-memory.md |  |  | 是 |
| project | 团队输出偏好 | memory/projects/<project-key>/project-memory.md 或 memory/projects/<project-key>/output-preferences.md |  |  | 是 |
| project | 项目历史缺陷 | memory/testing-experience-memory.md |  |  | 是 |
| project | 项目风险模式 | memory/testing-experience-memory.md |  |  | 是 |
| project | 项目反馈教训 | memory/testing-experience-memory.md |  |  | 是 |
| project | 项目历史缺陷 | memory/projects/<project-key>/testing-experience-memory.md |  |  | 是 |
| project | 项目风险模式 | memory/projects/<project-key>/testing-experience-memory.md |  |  | 是 |
| project | 项目反馈教训 | memory/projects/<project-key>/testing-experience-memory.md |  |  | 是 |
| personal | 个人输出偏好 | memory/user/preferences.md |  |  | 是 |
| personal | 个人检查习惯 | memory/user/testing-habits.md |  |  | 是 |
| personal | 个人测试启发 | knowledge/user/<主题>.md |  |  | 是 |
```

## 规则

- 只有当前需求、评审或用户反馈中出现证据时，才建议更新 memory。
- 不自动写入 memory。
- 每条建议保持原子化、可复用、可追踪。
- 如果本次已确定 `project-key`，优先建议写入 `memory/projects/<project-key>/` 下的项目化 memory；无法确定项目归属时，写入建议必须保留为待确认，不要落到任意项目目录。
- project 和 personal 层默认不提交 Git；建议中应标明该更新是团队共享项目配置还是个人本地偏好。
- 项目化 knowledge 的更新建议只适用于经确认的项目测试知识补充，例如项目风险画像、覆盖策略、术语映射、路由说明或 oracle 补充；不得把未确认业务事实写入 `knowledge/projects/<project-key>/`。
- personal 偏好只建议写入 `memory/user/`、`knowledge/user/` 或 `templates/user/`，不得写入 core 层或伪装成项目事实。
- 如果一条内容会影响团队共识或业务事实，必须建议写入 project；如果只影响当前使用者表达、关注点或本地检查，则建议写入 personal。
