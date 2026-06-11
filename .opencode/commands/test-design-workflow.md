---
description: Generate test design solution from reviewed test analysis solution
agent: build
---

Use the repository skill `test-design-workflow`.

Treat the command arguments below as the skill `$ARGUMENTS`:

```text
$ARGUMENTS
```

Supported argument hints:

- Reviewed analysis solution: `<test-analysis-solution.md>` or `analysis=<path>`.
- Optional requirement document: `--requirement <path>` or `requirement=<path>`.
- Optional design document: `--design <path>`, `design=<path>`, or `设计方案：<path>`.
- Optional project binding: `--project <project-key>`, `project=<project-key>`, or `项目：<project-key>`.
- Optional personal binding: `--personal <personal-key>`, `personal=<personal-key>`, or `个人：<personal-key>`.

When `project=<project-key>` is present, pass it through explicitly to `memory-context-builder`; the generated or reused `process/context-pack.md` must record the project-key, scanned project sources, unused project sources, and project knowledge stage bindings.

Example:

```text
outputs/runs/20260529-120000/deliverables/test-analysis-solution.md requirement=requirements/order-cancel.md design=design/order-cancel.md project=mall-order
```

Keep `PROJECT_ROOT` fixed to the current repository root. Prefer a reviewed `deliverables/test-analysis-solution.md` as input; if only requirement/design documents are provided, first generate the analysis solution, then write the design deliverable at `deliverables/test-design-solution.md`. Run the deterministic checks from `bin/`, and report the design solution path, process report path, check result, and any expected results marked as `待人工分析确认`.
