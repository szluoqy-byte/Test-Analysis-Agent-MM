# 示例需求：限时优惠与订单支付 上下文包

## 本次需求标识

- 需求文档：examples/requirements/complex-promotion-requirement.md
- 运行 ID：complex-promotion-requirement-run
- 关键词：限时优惠、优惠券、支付、库存、权限、兼容

## 项目标识

- project-key：未指定
- 确定依据：示例 fixture 未绑定具体项目
- 未确定原因：示例需求未提供项目参数、frontmatter 或唯一项目目录命中

## 个人配置标识

- personal-key：default
- 确定依据：示例 fixture 使用默认 personal 配置
- 使用路径：memory/user、knowledge/user、templates/user、quality-gates/user
- 默认 personal 说明：示例未命中个人偏好正文

## 命中摘要

| 来源 | 片段 | 命中原因 | 使用方式 |
|---|---|---|---|
| memory/testing-experience-memory.md | 大促交易链路需要重点关注优惠、支付、库存、权限、幂等和版本兼容 | 需求包含优惠券、支付、库存和多角色 | 写入历史经验和风险备注 |

## 已扫描来源

- core：memory/project-memory.md、memory/testing-experience-memory.md
- project：未扫描项目正文，project-key 未唯一确定
- personal：扫描默认 personal 元信息，未命中相关正文

## Project/Personal 使用摘要

| 层级 | 绑定结果 | 命中来源 | 未采用来源 | 冲突处理 | 后续补读建议 |
|---|---|---|---|---|---|
| project | 未绑定 project-key | 无 | 未读取所有项目目录正文，避免跨项目污染 | 无冲突 | 如需项目规则，请提供 project-key |
| personal | default | 无 | 默认 personal 未命中相关正文 | personal 不作为项目事实 | 无需补读 |

## 相关项目事实

- 输出需面向后续完整用例编写环节，主交付件必须自包含。

## 相关领域术语

- 无项目特有术语命中。

## 相关项目知识补充

- 无。

## 相关个人补充

- 无。

## 相关历史缺陷和风险模式

- 大促交易链路需要重点关注优惠、支付、库存、权限、幂等和版本兼容。

## 相关项目测试经验

- 大促优惠需求应组合使用决策表、边界值、状态迁移、接口契约和数据一致性分析。

## 输出偏好

- 主交付件必须自包含。

## 约束和非范围

- 不生成测试用例、操作步骤、具体测试数据或自动化脚本。

## 已检索但未注入的 Memory

- 无。

## 已检索但未注入的 Project/Personal 补充

- project：未绑定 project-key，不读取所有项目目录正文。
- personal：默认 personal 未命中相关正文。

## 大文件来源与后续补读建议

| 来源文件 | 命中原因 | 建议章节/关键词 | 未注入原因 |
|---|---|---|---|
| 无 | 无 | 无 | 示例 fixture 未触发大文件补读 |

## 待确认候选

- 无。
