# 测试分析最终报告

## 1. 汇总

| 指标 | 数量 |
|---|---|
| totalFacts | 3 |
| coveredFacts | 3 |
| partialFacts | 0 |
| missingFacts | 0 |
| notApplicableFacts | 0 |

## 2. FACT 覆盖明细

### 需求：examples/requirements/complex-promotion-requirement.md

#### 限时优惠券领取

| FACT | 输入来源 | 事实内容 | 约束/条件 | 可观察结果 | 覆盖SC | 覆盖TP | 覆盖状态 |
|---|---|---|---|---|---|---|---|
| FACT-001 | 需求 / examples/requirements/complex-promotion-requirement.md / 限时优惠券领取 | 活动时间内、库存充足且未重复领取时允许领取 | 活动开始和结束时间之间；库存充足；同一用户未领取 | 领取成功 | SC-001 优惠券活动与领取 > SC-001-001 普通用户领取优惠券 | TP-001 E2E场景测试 | covered |
| FACT-001 | 需求 / examples/requirements/complex-promotion-requirement.md / 限时优惠券领取 | 活动时间内、库存充足且未重复领取时允许领取 | 活动开始和结束时间之间；库存充足；同一用户未领取 | 领取成功 | SC-001 优惠券活动与领取 > SC-001-001 普通用户领取优惠券 | TP-002 活动时间窗口 | covered |
| FACT-001 | 需求 / examples/requirements/complex-promotion-requirement.md / 限时优惠券领取 | 活动时间内、库存充足且未重复领取时允许领取 | 活动开始和结束时间之间；库存充足；同一用户未领取 | 领取成功 | SC-001 优惠券活动与领取 > SC-001-001 普通用户领取优惠券 | TP-003 库存与单用户领取次数 | covered |

#### 优惠券可用性

| FACT | 输入来源 | 事实内容 | 约束/条件 | 可观察结果 | 覆盖SC | 覆盖TP | 覆盖状态 |
|---|---|---|---|---|---|---|---|
| FACT-002 | 需求 / examples/requirements/complex-promotion-requirement.md / 优惠券可用性 | 商品范围、金额门槛、会员等级和过期状态影响优惠券可用性 | 订单商品、订单金额、会员等级、优惠券有效期 | 优惠券可用或不可用 | SC-002 下单试算与优惠使用 > SC-002-001 订单试算 | TP-004 E2E场景测试 | covered |
| FACT-002 | 需求 / examples/requirements/complex-promotion-requirement.md / 优惠券可用性 | 商品范围、金额门槛、会员等级和过期状态影响优惠券可用性 | 订单商品、订单金额、会员等级、优惠券有效期 | 优惠券可用或不可用 | SC-002 下单试算与优惠使用 > SC-002-001 订单试算 | TP-005 商品范围与最低门槛 | covered |
| FACT-002 | 需求 / examples/requirements/complex-promotion-requirement.md / 优惠券可用性 | 商品范围、金额门槛、会员等级和过期状态影响优惠券可用性 | 订单商品、订单金额、会员等级、优惠券有效期 | 优惠券可用或不可用 | SC-002 下单试算与优惠使用 > SC-002-001 订单试算 | TP-006 会员折扣叠加资格 | covered |

#### 优惠券支付

| FACT | 输入来源 | 事实内容 | 约束/条件 | 可观察结果 | 覆盖SC | 覆盖TP | 覆盖状态 |
|---|---|---|---|---|---|---|---|
| FACT-003 | 需求 / examples/requirements/complex-promotion-requirement.md / 优惠券支付 | 重复支付不能重复扣减优惠券和库存 | 同一订单重复提交支付请求 | 不重复扣减优惠券和库存 | SC-003 订单支付与异步结果 > SC-003-001 优惠券支付闭环 | TP-007 E2E场景测试 | covered |
| FACT-003 | 需求 / examples/requirements/complex-promotion-requirement.md / 优惠券支付 | 重复支付不能重复扣减优惠券和库存 | 同一订单重复提交支付请求 | 不重复扣减优惠券和库存 | SC-003 订单支付与异步结果 > SC-003-001 优惠券支付闭环 | TP-008 已支付订单重复使用限制 | covered |
| FACT-003 | 需求 / examples/requirements/complex-promotion-requirement.md / 优惠券支付 | 重复支付不能重复扣减优惠券和库存 | 同一订单重复提交支付请求 | 不重复扣减优惠券和库存 | SC-003 订单支付与异步结果 > SC-003-001 优惠券支付闭环 | TP-009 支付超时释放优惠券 | covered |
