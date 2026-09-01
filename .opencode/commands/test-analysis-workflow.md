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
- Optional output directory id: `--runid <requirement-id>` or `runid=<requirement-id>`.

This command only accepts Markdown inputs. If the user provides `.docx` or `.xlsx`, stop and ask them to run `@file-normalization-agent` or `/normalize-input-documents` first, then pass the normalized Markdown path back to this command.

When `project=<project-key>` is present, pass it through explicitly to `bin/build-rules-pack.py` and `context-source-indexing`. The generated `process/rules-pack.md` must index applicable core/project/user rules. The generated `process/context-pack.md` must record project binding, dynamic project/personal knowledge sources, unscanned project sources, and warnings. Personal dynamic sources use `knowledge/user/**` paths; personal rules are loaded through `process/rules-pack.md`.

Example:

```text
requirements/order-cancel.md design=design/order-cancel.md project=mall-order runid=IR-2026-001
```

Keep `PROJECT_ROOT` fixed to the current repository root. `runid` only selects `outputs/runs/<run-id>/`; without it, use a session timestamp and do not invoke a shell just to prepare the directory. If that directory already contains a formal analysis result, stop and ask for a new `runid`. Write semantic process artifacts as Markdown under `process/`; keep JSON only for `id-registry/work-items` control state and the final analysis result. Generate `process/rules-pack.md` before `process/context-pack.md`, finalize `deliverables/test-analysis-solution.json` once at the stage boundary, render its result Markdown, run the fixed checks, and report the result paths.
