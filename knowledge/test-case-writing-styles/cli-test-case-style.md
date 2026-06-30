---
name: cli-test-case-style
description: 定义 CLI 测试用例的前置条件、测试数据、步骤和预期写法。
---

# CLI 测试用例写作风格

CLI 用例面向命令行操作者或命令行测试工具执行。步骤必须描述执行环境、命令主体、参数和可观察输出。

本文示例只说明 CLI 字段写法，不构成真实主机、目录、命令、参数或测试数据依据。

## preconditions[]

- 写清执行主机、容器、工作目录、用户权限、环境变量、配置文件、依赖服务和初始数据状态。
- 如果命令依赖上下文，明确使用稳定槽位，例如 `run_id=RUN_001`、`config=staging-mm.yaml`。
- 不把命令执行结果写成前置条件。
- 如果命令名、参数或运行环境没有输入依据，写稳定槽位或待人工确认，不编造真实命令。

## testData[]

- 使用命令参数、环境变量、输入文件或配置项命名，例如 `--transaction-id`、`MM_ENV`、`input_file`。
- `value` 写具体值或稳定槽位；路径使用相对工作目录或明确测试路径，避免生产路径。
- `description` 说明参数含义、边界或异常类型。
- 如果命令通过 stdin 或配置文件输入，分别使用 `stdin`、`config_file`、`input_file` 作为数据项名称。

## steps[].action

CLI action 必须写测试人员或工具可执行的命令动作，优先使用以下格式：

- `在主机「staging-bastion」以用户「tester」进入目录「/opt/mm-tools」`
- `设置环境变量 MM_ENV=staging`
- `执行命令「mmctl payment query --transaction-id TXN_PENDING_001」`
- `通过 stdin 向命令「mmctl batch import」输入文件内容「merchant_import_valid.csv」`
- `使用配置文件「config/staging-mm.yaml」执行命令「mmctl settlement run --date 2026-06-30」`
- `读取文件「logs/payment-result.log」中过滤 transaction_id=TXN_PENDING_001 的日志`

不得只写“执行查询”“系统处理批任务”“脚本生成结果”。如果命令名或参数在输入中没有依据，不编造具体命令；使用稳定槽位并标明待人工确认。

不得生成破坏性命令，例如删除文件、清库、重启生产服务、修改生产配置或终止关键进程；除非输入明确要求在测试环境验证该类命令，并且前置条件明确隔离环境和回滚条件。

如需验证删除、重启、清理、迁移或配置变更类命令，应优先使用 dry-run、测试目录、测试租户、测试命名空间或隔离环境，并在 `preconditions[]` 中写明隔离和回滚条件。

## steps[].expected

- 写退出码、stdout、stderr、输出文件、日志、任务状态或查询记录。
- 如果命令失败是预期，明确 `退出码!=0` 或输入依据支持的错误输出方向。
- 如果输入没有说明具体输出文本，不编造完整输出，只写可支撑的保守预期。
- 普通命令至少写退出码和一个可观察输出；长任务或批处理命令应继续查询任务状态、读取输出文件或读取日志，不能只写“任务完成”。
- 如果命令会产生副作用，expected 应写输出文件、数据库记录、任务状态或日志中的可验证对象。

## expectedResult

- 汇总最终命令执行判定，例如命令返回成功、拒绝非法参数、不产生成功态变更或生成预期文件。
- 不输出自动化脚本或 SQL 修改脚本。

## 示例

```json
{
  "preconditions": ["测试人员可登录主机 staging-bastion", "工作目录 /opt/mm-tools 已部署 mmctl", "交易 TXN_PENDING_001 已存在"],
  "testData": [
    {"name": "--transaction-id", "value": "TXN_PENDING_001", "description": "待查询交易编号"}
  ],
  "steps": [
    {"stepNo": 1, "action": "在主机「staging-bastion」以用户「tester」进入目录「/opt/mm-tools」", "expected": "当前目录切换到 /opt/mm-tools"},
    {"stepNo": 2, "action": "执行命令「mmctl payment query --transaction-id TXN_PENDING_001」", "expected": "退出码=0；stdout 包含 transactionStatus"}
  ],
  "expectedResult": "命令成功返回交易 TXN_PENDING_001 的状态信息。"
}
```

## 反例

- `action`: `系统查询交易状态`
- `action`: `执行查询`
- `action`: `执行脚本`
- `action`: `脚本生成结果`
- `action`: `后台任务处理完成`
- `expected`: `命令正常`
- `expected`: `查看结果正确`
