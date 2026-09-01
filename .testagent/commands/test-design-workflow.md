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

- Reviewed analysis solution: `<test-analysis-solution.json>` or `analysis=<path>`.
- Optional requirement document: `--requirement <path>` or `requirement=<path>`.
- Optional design document: `--design <path>`, `design=<path>`, or `设计方案：<path>`.
- Optional project binding: `--project <project-key>`, `project=<project-key>`, or `项目：<project-key>`.
- Optional output directory id: `--runid <requirement-id>` or `runid=<requirement-id>`.

This command accepts JSON canonical analysis input plus optional normalized Markdown requirement/design evidence. If the user provides `.docx` or `.xlsx`, stop and ask them to run `@file-normalization-agent` or `/normalize-input-documents` first, then pass the normalized Markdown path back to this command.

When `project=<project-key>` is present, pass it through explicitly to `bin/build-rules-pack.py` and `context-source-indexing`. The generated or reused `process/rules-pack.md` must index applicable core/project/user rules. The generated or reused `process/context-pack.md` must record project binding, dynamic project/personal knowledge sources, unscanned project sources, and warnings. Personal dynamic sources use `knowledge/user/**` paths; personal rules are loaded through `process/rules-pack.md`.

Example:

```text
runid=IR-2026-001 requirement=requirements/order-cancel.md design=design/order-cancel.md project=mall-order
```

Keep `PROJECT_ROOT` fixed to the current repository root. `runid` only selects `outputs/runs/<run-id>/`; without it, reuse the explicitly supplied analysis result's run directory when applicable, otherwise use a session timestamp. Do not invoke a shell just to prepare the directory. Require a reviewed `test-analysis-solution.json` as design input; use an explicit analysis path directly instead of copying it. If only requirement/design documents are provided, stop and ask the user to run `@test-analysis-agent` first or use the full flow. If the output directory already contains a formal design result, stop and ask for a new `runid`. Write TC generation, review and coverage as process Markdown, then finalize the design result once at the stage boundary and render its Markdown. Run the fixed checks and report the result paths.
