# FACT 覆盖树结构契约

覆盖证据图的每条既有 `factCoverage[]` 只允许编辑 `coverageTree`、`coverageStatus` 和 `coverageReason`。不得新增、删除、合并或重编号 FACT，也不得使用 `scenarioId`、`testPointTitle`、`coverageType` 等替代字段。

## 通用层级

`coverageTree` 必须是数组。每条覆盖链路固定为叶子场景、测试点和测试用例三级：

```json
[
  {
    "leafScenarioId": "SC-001-001",
    "testPoints": [
      {
        "testPointId": "TP-001",
        "testCases": []
      }
    ]
  }
]
```

- `leafScenarioId` 必须是当前最终方案中真实存在的叶子 `SC-*`。
- `testPointId` 必须是该叶子场景下真实存在的 `TP-*`。
- `testCases` 必须始终是数组；其中的值只能是对应 TP 下真实存在的 `TC-*`。
- 同一 FACT 可关联多个叶子 SC 和多个 TP，但必须按上述层级分组，不得平铺或用标题代替 ID。

## Analysis 覆盖图

分析覆盖只展示 `FACT -> leaf SC -> TP`。当 `coverageStatus=covered` 或 `partial` 时，`testCases` 必须为数组且保持为空：

```json
{
  "coverageTree": [
    {
      "leafScenarioId": "SC-001-001",
      "testPoints": [
        {
          "testPointId": "TP-001",
          "testCases": []
        }
      ]
    }
  ],
  "coverageStatus": "covered",
  "coverageReason": ""
}
```

## Design 覆盖图

设计覆盖展示 `FACT -> leaf SC -> TP -> TC`。当 `coverageStatus=covered` 时，至少有一个真实 `TC-*`：

```json
{
  "coverageTree": [
    {
      "leafScenarioId": "SC-001-001",
      "testPoints": [
        {
          "testPointId": "TP-001",
          "testCases": ["TC-001"]
        }
      ]
    }
  ],
  "coverageStatus": "covered",
  "coverageReason": ""
}
```

## 无覆盖状态

`gap` 和 `not_applicable` 必须使用空树，并填写明确原因：

```json
{
  "coverageTree": [],
  "coverageStatus": "gap",
  "coverageReason": "当前分析方案未形成可追溯的 SC/TP 覆盖链路。"
}
```

`partial` 可以保留真实的部分覆盖链路，但必须在 `coverageReason` 说明未覆盖的约束、路径或可观察结果。
