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

- Reviewed analysis solution: `<test-analysis-solution.json>` or `analysis=<path>`; Markdown analysis input is accepted only as a migration fallback.
- Optional requirement document: `--requirement <path>` or `requirement=<path>`.
- Optional design document: `--design <path>`, `design=<path>`, or `设计方案：<path>`.
- Optional project binding: `--project <project-key>`, `project=<project-key>`, or `项目：<project-key>`.
- Optional personal binding: `--personal <personal-key>`, `personal=<personal-key>`, or `个人：<personal-key>`.

This command only accepts JSON canonical, reviewed Markdown analysis, or normalized Markdown evidence inputs. If the user provides `.docx` or `.xlsx`, stop and ask them to run `@file-normalization-agent` or `/normalize-input-documents` first, then pass the normalized Markdown path back to this command.

When `project=<project-key>` is present, pass it through explicitly to `memory-context-builder`; the generated or reused `process/context-pack.json` must record the project-key, scanned project sources, unused project sources, and project knowledge stage bindings.

Example:

```text
outputs/runs/20260529-120000/deliverables/test-analysis-solution.json requirement=requirements/order-cancel.md design=design/order-cancel.md project=mall-order
```

Keep `PROJECT_ROOT` fixed to the current repository root. Prefer a reviewed `deliverables/test-analysis-solution.json` as input; if only requirement/design documents are provided, first generate the analysis solution, then write the design deliverable fact source at `deliverables/test-design-solution.json` and render `deliverables/test-design-solution.md` with `bin/render-run-markdown.py`. Run JSON lint, render drift check, Markdown lint, and consistency checks from `bin/`, and report the JSON and Markdown design solution paths, check result, and any expected results marked as `待人工分析确认`.
