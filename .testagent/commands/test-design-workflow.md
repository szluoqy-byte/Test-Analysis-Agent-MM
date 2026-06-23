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

This command accepts JSON canonical analysis input plus optional normalized Markdown requirement/design evidence. If the user provides `.docx` or `.xlsx`, stop and ask them to run `@file-normalization-agent` or `/normalize-input-documents` first, then pass the normalized Markdown path back to this command.

When `project=<project-key>` is present, pass it through explicitly to `context-source-indexing`; the generated or reused `process/context-pack.json` must record `projectBinding`, dynamic `sources[]`, unscanned project sources, and warnings. Personal sources are represented only by `rules/user/**`, `knowledge/user/**`, or `memory/user/**` paths in `sources[]`.

Example:

```text
outputs/runs/20260529-120000/deliverables/test-analysis-solution.json requirement=requirements/order-cancel.md design=design/order-cancel.md project=mall-order
```

Keep `PROJECT_ROOT` fixed to the current repository root. Require a reviewed `deliverables/test-analysis-solution.json` as design input; if only requirement/design documents are provided, first generate the analysis solution JSON, then write the design deliverable fact source at `deliverables/test-design-solution.json` and render `deliverables/test-design-solution.md` with `bin/render-run-markdown.py`. Run JSON lint, render drift check, Markdown lint, and consistency checks from `bin/`, and report the JSON and Markdown design solution paths plus check results.
