---
name: api-test-case-style
description: 定义 API 测试用例的前置条件、测试数据、步骤和预期写法。
---

# API 测试用例写作风格

API 用例面向接口调用方或接口测试工具执行。步骤必须描述可发起的请求、可读取的响应和可查询的副作用。

本文示例只说明 API 字段写法，不构成真实接口、消息主题、字段、错误码或测试数据依据。

## preconditions[]

- 写清测试环境、鉴权条件、调用方身份、必要配置、依赖服务状态和初始数据状态。
- 如果需要前置业务数据，使用稳定数据槽位，例如 `customer_id=AGT_CUSTOMER_001`、`transaction_id=TXN_PENDING_001`。
- 不把接口响应或系统处理结果写成前置条件。
- 如果接口方法、路径、主题、回调地址或字段名没有输入依据，写稳定槽位或待人工确认，不编造契约细节。

## testData[]

- 使用接口字段或稳定数据槽位命名，例如 `Header.Authorization`、`Body.amount`、`Query.msisdn`。
- `value` 写具体值或稳定槽位；枚举、边界、无效值必须明确。
- `description` 说明字段含义、等价类、边界或异常类型。

## steps[].action

API action 必须写外部调用方或测试工具可执行的请求或取数动作，优先使用字段片段：

- `调用接口=POST /api/v1/payments；Header.Authorization=有效Token；Body.amount=1000.00；Body.msisdn=22670000001`
- `调用接口=GET /api/v1/payments/{transactionId}；Path.transactionId=TXN_PENDING_001`
- `发送消息 topic=payment-request；key=TXN_PENDING_001；payload.amount=1000.00`
- `模拟回调接口=POST /api/v1/payment-callback；Body.transactionId=TXN_PENDING_001；Body.status=SUCCESS`
- `查询数据库表=payment_order；条件 transaction_id=TXN_PENDING_001`
- `拉取消息主题=payment-result；过滤 transaction_id=TXN_PENDING_001`

HTTP API 字段片段优先按 `接口`、`Header`、`Path`、`Query`、`Body` 顺序书写。不得写完整裸 URL，例如 `GET https://host/path?x=1`。不得把 `检查响应体字段`、`系统返回错误码`、`服务端写入记录` 写成 action。

接口稳定性类用例也必须写成可执行输入：

- 幂等：`调用接口=POST /api/v1/payments；Header.Idempotency-Key=IDEMP_001；Body...`，再用相同幂等键重复调用。
- 超时：`在测试桩配置中设置依赖服务 payment-core 返回超时` 后调用目标接口。
- 重试：`在测试桩配置中设置第一次依赖调用超时、第二次调用成功` 后调用目标接口。
- 回调乱序：按指定顺序发送回调消息或请求，例如先发送 `status=SUCCESS` 再发送 `status=PENDING`。

## steps[].expected

- 写响应状态、响应体字段、错误码、错误提示、幂等结果、数据记录、消息事件或外部依赖结果。
- 如果需要验证数据库、消息或日志，action 写查询/读取/拉取动作，expected 写具体字段或状态。
- 如果输入没有说明具体错误码或提示文案，不编造具体值，只写保守预期。
- 成功类用例不得只写 `响应状态=HTTP 200`；还应写输入依据支持的关键响应字段或数据副作用。
- 失败类用例不得只写 `响应状态=HTTP 4xx/5xx`；还应写请求被拒绝、无成功态数据变更、错误方向或状态保持不变等可判定结果。

## expectedResult

- 汇总最终契约或业务判定，例如请求成功创建交易、请求被拒绝且无成功态数据变更、重复请求保持幂等。
- 保持与需求、设计、规则或分析方案依据一致。

## 示例

```json
{
  "preconditions": ["调用方已获得有效 Token", "客户 AGT_CUSTOMER_001 状态为 Active"],
  "testData": [
    {"name": "Body.amount", "value": "1000.00", "description": "有效支付金额"},
    {"name": "Body.msisdn", "value": "22670000001", "description": "有效客户号码"}
  ],
  "steps": [
    {"stepNo": 1, "action": "调用接口=POST /api/v1/payments；Header.Authorization=有效Token；Body.amount=1000.00；Body.msisdn=22670000001", "expected": "响应状态=HTTP 200；响应体 transactionStatus=SUCCESS"},
    {"stepNo": 2, "action": "调用接口=GET /api/v1/payments/{transactionId}；Path.transactionId=上一步返回的 transactionId", "expected": "响应状态=HTTP 200；响应体 transactionStatus=SUCCESS"}
  ],
  "expectedResult": "支付请求处理成功，交易状态可通过查询接口确认。"
}
```

## 反例

- `action`: `GET https://host/api/v1/payments?amount=1000`
- `action`: `调用支付接口`
- `action`: `检查响应体字段`
- `action`: `系统返回交易成功`
- `action`: `数据库更新成功`
- `expected`: `接口正常`
- `expected`: `接口返回正确`
