---
description: Generate test design solution from reviewed test analysis solution
agent: build
---

Use the repository skill `generate-test-design-solution`.

Treat the command arguments below as the skill `$ARGUMENTS`:

```text
$ARGUMENTS
```

Keep `PROJECT_ROOT` fixed to the current repository root. Prefer a reviewed `deliverables/test-analysis-solution.md` as input; if only requirement/design documents are provided, first generate the analysis solution, then write the design deliverable at `deliverables/test-design-solution.md`. Run the deterministic checks from `bin/`, and report the design solution path, process report path, check result, and any expected results marked as `待人工分析确认`.
