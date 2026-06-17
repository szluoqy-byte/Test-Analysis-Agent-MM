# 接口契约测试技术

接口契约测试技术用于验证系统对 API、消息、回调或第三方交互契约的遵守情况。契约包括请求字段、响应字段、错误码、鉴权、幂等、超时、重试和数据副作用。

## 适用场景

- HTTP API、RPC、消息队列、回调通知。
- 字段必填、类型、枚举、格式、长度、范围校验。
- 鉴权、签名、权限、租户隔离。
- 错误码、错误信息、响应结构。
- 幂等、重复请求、超时、重试、回调补偿。

## 分析落点

当用户任务、需求或设计方案明确要求接口测试/API 契约覆盖时，测试分析方案应先按接口、端点、消息、回调或集成点建立 `TP-*`，让后续 TC 能明确知道目标接口。

示例：

```json
{
  "id": "TP-002",
  "title": "接口：POST /customers/{customer_id}/transactions/",
  "objective": "验证交易创建接口的请求字段、鉴权、响应和副作用契约。",
  "basisRefs": [
    {"source": "design.md", "location": "交易创建接口", "description": "接口字段和响应契约"}
  ],
  "methodRefs": [
    {"method": "interface-contract", "evidenceId": "ME-002"}
  ]
}
```

## 设计派生

接口类 TC 应拆成可观察字段片段，不写完整裸 URL。

```json
{
  "id": "TC-001",
  "title": "合法交易创建请求返回成功并产生交易记录",
  "preconditions": ["用户已认证", "customer_id 存在"],
  "testData": [
    {"name": "接口", "value": "POST /customers/{customer_id}/transactions/", "description": "交易创建接口"},
    {"name": "amount", "value": "100.00", "description": "合法金额"},
    {"name": "reference", "value": "REF_10001", "description": "唯一交易引用"}
  ],
  "steps": [
    {"stepNo": 1, "action": "使用合法请求字段调用交易创建接口", "expected": "接口返回成功响应"},
    {"stepNo": 2, "action": "查询交易记录和订单状态", "expected": "交易记录已创建，订单进入设计规定状态"}
  ],
  "expectedResult": "接口成功创建交易并产生需求或设计支持的副作用。",
  "sourceRefs": [
    {"source": "design.md", "location": "交易创建接口", "description": "成功契约和副作用"}
  ]
}
```
