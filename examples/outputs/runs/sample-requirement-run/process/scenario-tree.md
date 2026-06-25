# 示例需求：订单取消 冻结 SC 场景树

## 运行目录

examples/outputs/runs/sample-requirement-run

## 分析方案来源

examples/outputs/runs/sample-requirement-run/deliverables/test-analysis-solution.json

## 范围

| Field | Content |
|---|---|
| 需求 ID | 示例需求 |
| 需求名称 | 订单取消 |
| 需求来源 | examples/requirements/sample-requirement.md |
| 设计方案来源 | 未提供 |
| 需求摘要 | 用户在订单未完成前可以取消订单；取消后订单不可继续支付，系统释放库存并记录取消原因。 |
| 本次覆盖范围 | 普通用户取消本人订单、权限控制、订单状态限制、重复取消、客服协助取消和取消副作用。 |
| 本次不覆盖内容 | 退款、售后、物流拦截和客服审核后台详细流程。 |

## 场景树

| ID | Title | Fields | Children |
|---|---|---|---|
| SC-001 | 订单取消业务流程 | Field=场景目标；Content=覆盖订单取消的用户入口、权限、状态和副作用控制。 | ID=SC-001-001；Title=普通用户取消订单；Fields=Field=场景目标；Content=验证普通用户在不同归属和订单状态下的取消规则。；Field=场景入口/触发方式；Content=前端调用订单取消接口。；Field=执行用户/角色；Content=普通用户。；Field=业务与设计约束；Content=普通用户只能取消自己的订单；待支付订单允许取消；已发货订单不允许取消。；ID=SC-001-002；Title=重复取消与副作用控制；Fields=Field=场景目标；Content=验证重复取消不会造成重复释放库存或重复副作用。；Field=场景入口/触发方式；Content=同一订单重复提交取消请求。；Field=执行用户/角色；Content=普通用户。；Field=业务与设计约束；Content=用户重复提交取消请求时，系统不能重复释放库存。 |
| SC-002 | 客服协助取消 | Field=场景目标；Content=覆盖客服协助用户取消订单的业务入口。 |  |
