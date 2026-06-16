# 示例需求：限时优惠与订单支付 上下文来源索引

## 本次需求

| 字段 | 值 |
|---|---|
| path | examples/requirements/complex-promotion-requirement.md |
| title | 限时优惠与订单支付 |
| keywords | 限时优惠、优惠券、支付、库存、权限、兼容 |

## 绑定结果

| 绑定 | 状态 | 标识 | 说明 |
|---|---|---|---|
| projectBinding | unresolved |  | 示例 fixture 未绑定具体项目，且需求未提供可唯一识别的 project-key |
| personalBinding | default | default | 示例 fixture 使用默认 personal 扩展路径，未命中动态来源文件 |

## 动态来源索引

无动态 project/personal 来源。

## 未扫描项目来源

| 路径 | 原因 |
|---|---|
| rules/projects/ | project-key 未唯一确定 |
| knowledge/projects/ | project-key 未唯一确定 |
| memory/projects/ | project-key 未唯一确定 |
| quality-gates/projects/ | project-key 未唯一确定 |

## 告警

无告警。
