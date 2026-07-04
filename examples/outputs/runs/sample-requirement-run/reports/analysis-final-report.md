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

### 需求：examples/requirements/sample-requirement.md

#### 订单取消

| FACT | 输入来源 | 事实内容 | 约束/条件 | 可观察结果 | 覆盖链路 | 覆盖状态 |
|---|---|---|---|---|---|---|
| FACT-001 | 需求 / examples/requirements/sample-requirement.md / 订单取消 | 用户在订单未完成前可以取消订单 | 本人订单且订单未完成 | 取消成功后订单不可继续支付，库存释放并记录取消原因 | SC-001 订单取消业务流程 > SC-001-001 普通用户取消订单 / TP-001 E2E场景测试<br>SC-001 订单取消业务流程 > SC-001-001 普通用户取消订单 / TP-002 本人待支付订单允许取消<br>SC-001 订单取消业务流程 > SC-001-001 普通用户取消订单 / TP-004 已发货订单取消状态限制 | covered |
| FACT-002 | 需求 / examples/requirements/sample-requirement.md / 订单取消 | 普通用户不能取消非本人订单 | 订单归属不匹配 | 取消失败 | SC-001 订单取消业务流程 > SC-001-001 普通用户取消订单 / TP-003 非本人订单取消权限控制 | covered |

#### 重复取消

| FACT | 输入来源 | 事实内容 | 约束/条件 | 可观察结果 | 覆盖链路 | 覆盖状态 |
|---|---|---|---|---|---|---|
| FACT-003 | 需求 / examples/requirements/sample-requirement.md / 重复取消 | 重复取消不能重复释放库存 | 同一订单重复提交取消请求 | 库存不重复释放 | SC-001 订单取消业务流程 > SC-001-002 重复取消与副作用控制 / TP-005 E2E场景测试<br>SC-001 订单取消业务流程 > SC-001-002 重复取消与副作用控制 / TP-006 取消请求幂等与库存副作用 | covered |
