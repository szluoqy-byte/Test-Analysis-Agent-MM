---
description: Generate test analysis solution from Markdown requirement and optional design documents
agent: build
---

Use the repository skill `analyze-requirement-test-analysis-solution`.

Treat the command arguments below as the skill `$ARGUMENTS`:

```text
$ARGUMENTS
```

Keep `PROJECT_ROOT` fixed to the current repository root. Write outputs under `outputs/runs/<run-id>/`, generate the main deliverable at `deliverables/test-analysis-solution.md`, run the deterministic checks from `bin/`, and report the solution path, process report path, check result, and any expected results marked as `待人工分析确认`.
