---
description: Generate test analysis solution from Markdown requirement and optional design documents
agent: build
---

Use the repository skill `test-analysis-workflow`.

Treat the command arguments below as the skill `$ARGUMENTS`:

```text
$ARGUMENTS
```

Supported argument hints:

- Requirement document: `<requirement.md>` or `requirement=<path>`.
- Optional design document: `--design <path>`, `design=<path>`, or `设计方案：<path>`.
- Optional project binding: `--project <project-key>`, `project=<project-key>`, or `项目：<project-key>`.
- Optional personal binding: `--personal <personal-key>`, `personal=<personal-key>`, or `个人：<personal-key>`.

This command only accepts Markdown inputs. If the user provides `.docx` or `.xlsx`, stop and ask them to run `@file-normalization-agent` or `/normalize-input-documents` first, then pass the normalized Markdown path back to this command.

When `project=<project-key>` is present, pass it through explicitly to `memory-context-builder`; the generated `process/context-pack.json` must record the project-key, scanned project sources, unused project sources, and project knowledge stage bindings.

Example:

```text
requirements/order-cancel.md design=design/order-cancel.md project=mall-order
```

Keep `PROJECT_ROOT` fixed to the current repository root. Write outputs under `outputs/runs/<run-id>/`, generate the main deliverable fact source at `deliverables/test-analysis-solution.json`, render `deliverables/test-analysis-solution.md` with `bin/render-run-markdown.py`, run JSON lint, render drift check, Markdown lint, and consistency checks from `bin/`, and report the JSON and Markdown solution paths, check result, and any expected results marked as `待人工分析确认`.
