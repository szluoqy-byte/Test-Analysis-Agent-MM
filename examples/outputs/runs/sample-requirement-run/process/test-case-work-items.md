# 测试用例生成工作项索引

## 运行目录

examples/outputs/runs/sample-requirement-run

## 分析方案来源

examples/outputs/runs/sample-requirement-run/deliverables/test-analysis-solution.json

## 工作项

| Scenario Path | Leaf Scenario Id | Leaf Scenario Title | Test Point Id | Test Point Title | Objective | Basis Refs | 状态 | Slice Path | Merged At |
|---|---|---|---|---|---|---|---|---|---|
| ID=SC-001；Title=订单取消业务流程；ID=SC-001-001；Title=普通用户取消订单 | SC-001-001 | 普通用户取消订单 | TP-001 | E2E场景测试 | 验证普通用户取消本人待支付订单时，取消请求、订单状态、支付限制、库存释放和取消原因记录能够形成完整业务闭环。 | 来源=examples/requirements/sample-requirement.md；位置=订单取消；说明=用户在订单未完成前可以取消订单，取消后不可继续支付并释放库存。 | done | examples/outputs/runs/sample-requirement-run/process/test-case-slices/TP-001.json | 2026-06-25T20:54:54 |
| ID=SC-001；Title=订单取消业务流程；ID=SC-001-001；Title=普通用户取消订单 | SC-001-001 | 普通用户取消订单 | TP-002 | 本人待支付订单允许取消 | 验证普通用户取消本人名下待支付订单时，系统允许取消并完成状态、库存和取消原因处理。 | 来源=examples/requirements/sample-requirement.md；位置=订单取消规则；说明=待支付本人订单允许取消。 | done | examples/outputs/runs/sample-requirement-run/process/test-case-slices/TP-002.json | 2026-06-25T20:54:54 |
| ID=SC-001；Title=订单取消业务流程；ID=SC-001-001；Title=普通用户取消订单 | SC-001-001 | 普通用户取消订单 | TP-003 | 非本人订单取消权限控制 | 验证普通用户尝试取消非本人订单时，系统能够识别订单归属不匹配并阻止取消。 | 来源=examples/requirements/sample-requirement.md；位置=权限约束；说明=普通用户只能取消自己的订单。 | done | examples/outputs/runs/sample-requirement-run/process/test-case-slices/TP-003.json | 2026-06-25T20:54:54 |
| ID=SC-001；Title=订单取消业务流程；ID=SC-001-001；Title=普通用户取消订单 | SC-001-001 | 普通用户取消订单 | TP-004 | 已发货订单取消状态限制 | 验证普通用户取消本人名下已发货订单时，系统按订单状态限制拒绝取消。 | 来源=examples/requirements/sample-requirement.md；位置=状态约束；说明=已发货订单不允许取消。 | done | examples/outputs/runs/sample-requirement-run/process/test-case-slices/TP-004.json | 2026-06-25T20:54:54 |
| ID=SC-001；Title=订单取消业务流程；ID=SC-001-002；Title=重复取消与副作用控制 | SC-001-002 | 重复取消与副作用控制 | TP-005 | E2E场景测试 | 验证订单首次取消成功后再次出现取消请求时，系统保持订单取消结果并控制库存释放副作用。 | 来源=examples/requirements/sample-requirement.md；位置=重复取消；说明=重复提交取消请求不能重复释放库存。 | done | examples/outputs/runs/sample-requirement-run/process/test-case-slices/TP-005.json | 2026-06-25T20:54:54 |
| ID=SC-001；Title=订单取消业务流程；ID=SC-001-002；Title=重复取消与副作用控制 | SC-001-002 | 重复取消与副作用控制 | TP-006 | 取消请求幂等与库存副作用 | 验证同一订单重复或并发取消时，系统不会产生重复库存释放或重复取消记录等副作用。 | 来源=examples/requirements/sample-requirement.md；位置=副作用控制；说明=库存不能重复释放。 | done | examples/outputs/runs/sample-requirement-run/process/test-case-slices/TP-006.json | 2026-06-25T20:54:54 |
| ID=SC-002；Title=客服协助取消 | SC-002 | 客服协助取消 | TP-007 | E2E场景测试 | 验证客服帮助用户对已支付未发货订单发起取消申请时，业务主流程可被完整追踪。 | 来源=examples/requirements/sample-requirement.md；位置=客服协助取消；说明=客服可以帮助用户对已支付未发货订单发起取消。 | done | examples/outputs/runs/sample-requirement-run/process/test-case-slices/TP-007.json | 2026-06-25T20:54:54 |
| ID=SC-002；Title=客服协助取消 | SC-002 | 客服协助取消 | TP-008 | 客服协助取消范围 | 验证客服协助取消只覆盖已支付未发货订单，不扩大到需求未说明的售后、退款或物流拦截流程。 | 来源=examples/requirements/sample-requirement.md；位置=客服协助取消；说明=已支付但未发货订单允许申请取消，需要客服审核。 | done | examples/outputs/runs/sample-requirement-run/process/test-case-slices/TP-008.json | 2026-06-25T20:54:55 |

## Total Test Points

8
