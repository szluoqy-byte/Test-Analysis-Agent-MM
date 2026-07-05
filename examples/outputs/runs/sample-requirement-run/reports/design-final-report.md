# 测试设计最终报告

## 1. 汇总

| 指标 | 数量 |
|---|---|
| totalFacts | 3 |
| coveredFacts | 3 |
| partialFacts | 0 |
| missingFacts | 0 |
| notApplicableFacts | 0 |

## 2. FACT 覆盖明细

### 需求：examples/requirements/sample-requirement.md

#### 订单取消

| FACT | 输入来源 | 事实内容 | 约束/条件 | 可观察结果 | 覆盖SC | 覆盖TP | 覆盖TC | 覆盖状态 |
|---|---|---|---|---|---|---|---|---|
| FACT-001 | 需求 / examples/requirements/sample-requirement.md / 订单取消 | 用户在订单未完成前可以取消订单 | 本人订单且订单未完成 | 取消成功后订单不可继续支付，库存释放并记录取消原因 | SC-001 订单取消业务流程 > SC-001-001 普通用户取消订单 | TP-001 E2E场景测试<br>TP-002 本人待支付订单允许取消<br>TP-004 已发货订单取消状态限制 | TC-001 普通用户取消本人待支付订单成功闭环<br>TC-002 本人待支付订单取消被允许<br>TC-004 本人已发货订单取消被拒绝 | covered |
| FACT-002 | 需求 / examples/requirements/sample-requirement.md / 订单取消 | 普通用户不能取消非本人订单 | 订单归属不匹配 | 取消失败 | SC-001 订单取消业务流程 > SC-001-001 普通用户取消订单 | TP-003 非本人订单取消权限控制 | TC-003 用户 A 取消用户 B 的订单被拒绝 | covered |

#### 重复取消

| FACT | 输入来源 | 事实内容 | 约束/条件 | 可观察结果 | 覆盖SC | 覆盖TP | 覆盖TC | 覆盖状态 |
|---|---|---|---|---|---|---|---|---|
| FACT-003 | 需求 / examples/requirements/sample-requirement.md / 重复取消 | 重复取消不能重复释放库存 | 同一订单重复提交取消请求 | 库存不重复释放 | SC-001 订单取消业务流程 > SC-001-002 重复取消与副作用控制 | TP-005 E2E场景测试<br>TP-006 取消请求幂等与库存副作用 | TC-005 首次取消成功后重复取消不重复释放库存<br>TC-006 同一订单并发取消只产生一次成功副作用 | covered |
