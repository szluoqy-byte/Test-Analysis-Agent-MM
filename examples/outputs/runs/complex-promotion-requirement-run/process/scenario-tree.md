# 示例需求：限时优惠与订单支付 冻结 SC 场景树

## 运行目录

examples/outputs/runs/complex-promotion-requirement-run

## 分析方案来源

examples/outputs/runs/complex-promotion-requirement-run/deliverables/test-analysis-solution.json

## 范围

| Field | Content |
|---|---|
| 需求 ID | 复杂示例需求 |
| 需求名称 | 限时优惠与订单支付 |
| 需求来源 | examples/requirements/complex-promotion-requirement.md |
| 设计方案来源 | 未提供 |
| 需求摘要 | 大促期间支持限时优惠券抵扣订单金额，支付成功后锁定优惠券状态并扣减库存。 |
| 本次覆盖范围 | 优惠券领取、试算、支付提交、支付回调、超时释放、重复支付和版本兼容。 |
| 本次不覆盖内容 | 真实支付渠道清结算、运营后台完整配置流程和客服后台 UI。 |

## 场景树

| ID | Title | Fields | Children |
|---|---|---|---|
| SC-001 | 优惠券活动与领取 | Field=场景目标；Content=覆盖优惠券活动有效期、库存、用户领取次数和适用商品范围。 | ID=SC-001-001；Title=普通用户领取优惠券；Fields=Field=场景目标；Content=验证普通用户只能领取自己可用范围内且库存充足的优惠券。；Field=场景入口/触发方式；Content=用户在 App 领取限时优惠券。；Field=执行用户/角色；Content=普通用户。；Field=业务与设计约束；Content=活动有开始和结束时间；库存为 0 不能领取；每个用户同一活动最多领取 1 张。 |
| SC-002 | 下单试算与优惠使用 | Field=场景目标；Content=覆盖优惠券在订单试算和支付前的可用性判断。 | ID=SC-002-001；Title=订单试算；Fields=Field=场景目标；Content=验证试算接口返回优惠金额、应付金额和不可用原因。；Field=场景入口/触发方式；Content=前端调用试算接口。；Field=执行用户/角色；Content=普通用户。；Field=业务与设计约束；Content=优惠券仅适用于配置商品分类；订单金额必须大于等于最低使用门槛；VIP 可叠加会员折扣。 |
| SC-003 | 订单支付与异步结果 | Field=场景目标；Content=覆盖支付提交、异步回调、超时释放和重复支付副作用。 | ID=SC-003-001；Title=优惠券支付闭环；Fields=Field=场景目标；Content=验证待支付订单使用优惠券支付后的状态、优惠券、库存和日志处理。；Field=场景入口/触发方式；Content=前端调用支付接口，支付系统异步回调。；Field=执行用户/角色；Content=普通用户、支付系统。；Field=业务与设计约束；Content=待支付订单可以使用优惠券支付；已支付订单不能再次使用优惠券；支付成功后更新订单状态、优惠券状态、库存数量和操作日志。 |
| SC-004 | 版本兼容展示 | Field=场景目标；Content=覆盖 App 版本对新优惠券规则展示的影响。 |  |
