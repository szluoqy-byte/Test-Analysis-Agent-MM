# ISTQB 方法论对齐分析

## 1. 分析目的

本文审视当前 `knowledge/test-techniques/` 是否与 ISTQB 测试技术分类一致，并识别哪些技术是标准方法直接映射、哪些是工程扩展、哪些未来可以合并。

本次只做分析，不执行技术库裁剪。

## 2. 参考基线

参考 ISTQB Certified Tester Foundation Level v4.0.1 Syllabus：

- 官方页面：https://www.istqb.org/certifications/certified-tester-foundation-level-ctfl-v4-0/
- Syllabus 下载页：https://www.istqb.org/sdm_downloads/istqb-certified-tester-foundation-level-syllabus-v4-0/

CTFL v4.0.1 将测试技术分为三类：

| ISTQB 分类 | 说明 | CTFL v4.0.1 常见技术 |
|---|---|---|
| Black-box / Specification-based | 基于规格或外部行为设计测试 | 等价类划分、边界值分析、判定表测试、状态转换测试 |
| White-box / Structure-based | 基于内部结构和代码路径设计测试 | 语句测试、分支测试 |
| Experience-based | 基于测试人员经验和历史知识设计测试 | 错误推测、探索式测试、检查清单测试 |

本 Agent 面向需求和设计方案生成测试分析方案，不读取代码结构。因此当前测试技术库以黑盒/规格技术和经验技术为主，不覆盖 white-box 技术是合理的。

## 3. 当前技术对齐结果

| 当前技术文件 | ISTQB 对齐 | 判断 | 说明 |
|---|---|---|---|
| `specification-based/equivalence-boundary.md` | 等价类划分、边界值分析 | 直接匹配 | 当前把 EP 和 BVA 合并在一个技术文件中，符合测试设计项生成的使用方式 |
| `specification-based/decision-table.md` | 判定表测试 | 直接匹配 | 多条件共同决定动作或结果时，是 ISTQB 规格类技术的标准映射 |
| `specification-based/state-transition.md` | 状态转换测试 | 直接匹配 | 生命周期、审批流、终态、非法迁移与 ISTQB 状态转换技术一致 |
| `experience-based/error-guessing-checklist.md` | 错误推测、检查清单测试 | 直接匹配 | 已合入缺陷模式库，承担经验型补充覆盖 |
| `specification-based/cause-effect.md` | 判定逻辑建模，接近判定表前置建模 | 部分匹配 | CTFL v4.0.1 常见技术列表不把因果图作为主技术列出；更像判定表的建模前置 |
| `specification-based/decision-point.md` | 单点判定，接近判定表/等价类 | 部分匹配 | 是工程化拆分粒度，不是独立 ISTQB 核心技术 |
| `specification-based/scenario-usecase-userstory.md` | 场景/用例思路，偏业务流程测试 | 广义匹配 | 更像需求表达和业务流程覆盖方法，适合保留为场景与测试点生成技术 |
| `risk-based/risk-based-testing.md` | 风险驱动测试策略 | 策略匹配，不是单一测试设计技术 | ISTQB 体系重视风险驱动，但它更偏测试策略、优先级和深度控制 |
| `specification-based/data-combination.md` | 组合测试、pairwise、正交思路 | 工程扩展 | CTFL v4.0.1 常见黑盒技术不把组合测试列为核心项；但工程上很实用 |
| `specification-based/interface-contract.md` | API/契约测试 | 工程扩展 | 不是 CTFL 核心测试技术，更像面向接口和集成场景的领域技术 |
| `specification-based/processing-cycle.md` | 周期/批处理/时间窗口建模 | 工程扩展 | 可被状态转换、场景流和可靠性覆盖，当前是业务域便利技术 |
| `quality-attribute-based/performance-efficiency.md` | 性能效率质量属性测试 | 质量属性扩展 | 属于非功能/质量属性关注，不是 CTFL 黑盒测试技术本体 |
| `quality-attribute-based/reliability-recoverability.md` | 可靠性、恢复性质量属性测试 | 质量属性扩展 | 与异常、恢复、重试、容错有关，可与风险和场景流共同使用 |

## 4. 未来可合并候选

以下只是后续优化建议，本次不操作。

| 合并方向 | 可合并技术 | 原因 | 建议时机 |
|---|---|---|---|
| 规则判定技术 | `decision-point.md`、`decision-table.md`、`cause-effect.md` | 三者都处理条件、判定、动作和结果；ISTQB 直接核心是判定表 | 当维护者希望减少规格类技术文件数量时 |
| 状态周期技术 | `state-transition.md`、`processing-cycle.md` | 周期、批处理、重试周期常可建模为状态、事件和时间窗口 | 当状态/周期章节重复增多时 |
| 质量属性技术 | `performance-efficiency.md`、`reliability-recoverability.md` | 都是非功能质量属性设计；可共享指标、负载、故障和恢复表达 | 当非功能技术继续增加时 |
| 场景流扩展 | `scenario-usecase-userstory.md` 与部分 `processing-cycle.md` | 批处理、定时任务、端到端业务流都依赖场景入口、触发和结束状态 | 当场景技术需要覆盖系统触发类流程时 |

## 5. 不建议合并的内容

| 技术文件 | 原因 |
|---|---|
| `equivalence-boundary.md` | ISTQB 直接核心技术，且测试设计项派生粒度稳定 |
| `state-transition.md` | ISTQB 直接核心技术，生命周期测试高频且独立 |
| `interface-contract.md` | 虽非 ISTQB CTFL 核心技术，但本 Agent 明确需要基于设计方案补接口、字段、错误码和幂等 |
| `data-combination.md` | 虽是工程扩展，但配置、渠道、版本、角色组合在测试分析方案中高频出现 |
| `risk-based-testing.md` | 不是单一测试设计技术，但负责深度和风险补充，是测试分析方案不可缺的策略层 |
| `error-guessing-checklist.md` | ISTQB 经验类技术直接匹配，且已承载通用缺陷模式 |

## 6. 当前结论

当前测试技术库不是纯 ISTQB 技术清单，而是“ISTQB 基础技术 + 工程化测试设计技术”的组合。这个方向与 Agent 目标一致。

短期建议：

- 保持当前技术文件数量不变。
- 已直接匹配 ISTQB 的技术继续作为核心技术。
- 工程扩展技术继续保留，但在 README 中明确它们是测试分析方案扩展，不是 ISTQB CTFL 核心技术。
- 下一轮如要减文件，优先合并 `decision-point / decision-table / cause-effect`，其次再考虑 `state-transition / processing-cycle`。
