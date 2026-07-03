---
description: Generate test analysis and test design solutions in one end-to-end flow
agent: build
---

Use the repository skill `test-analysis-design-workflow`.

Treat the command arguments below as the skill `$ARGUMENTS`:

```text
$ARGUMENTS
```

Supported argument hints:

- Requirement document: `<requirement.md>` or `requirement=<path>`.
- Optional design document: `--design <path>`, `design=<path>`, or `设计方案：<path>`.
- Optional project binding: `--project <project-key>`, `project=<project-key>`, or `项目：<project-key>`.

This command only accepts normalized Markdown inputs. If the user provides `.docx` or `.xlsx`, stop and ask them to run `@file-normalization-agent` or `/normalize-input-documents` first, then pass the normalized Markdown path back to this command.

The command is a high-level orchestrator. When the runtime supports true independent subagents, prefer an analysis subagent to run `test-analysis-workflow`, wait for that workflow to finish its own lint, render, review, coverage, final-report, and consistency checks, then pass the generated `deliverables/test-analysis-solution.json` explicitly into a design subagent running `test-design-workflow`. Do not duplicate the detailed validation logic from either workflow.

If true subagents are unavailable, fall back to the same-session workflow sequence and say so in the final response. Stage handoff must use canonical JSON files and fixed report paths only, not chat history or natural-language summaries.

Example:

```text
requirements/order-cancel.md design=design/order-cancel.md project=mall-order
```

Keep `PROJECT_ROOT` fixed to the current repository root. Prefer one shared `outputs/runs/<run-id>/` for both phases. Report the final run directory, analysis solution JSON/Markdown, design solution JSON/Markdown, analysis final report JSON/Markdown, and design final report JSON/Markdown.
