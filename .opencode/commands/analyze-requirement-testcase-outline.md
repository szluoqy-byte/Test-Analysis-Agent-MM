---
description: Generate testcase title outline from Markdown requirement and optional design documents
agent: build
---

Use the repository skill `analyze-requirement-testcase-outline`.

Treat the command arguments below as the skill `$ARGUMENTS`:

```text
$ARGUMENTS
```

Keep `PROJECT_ROOT` fixed to the current repository root. Write outputs under `outputs/runs/<run-id>/`, generate the main deliverable at `deliverables/testcase-title-outline.md`, run the deterministic checks from `bin/`, and report the outline path, process report path, check result, and unresolved confirmation questions.
