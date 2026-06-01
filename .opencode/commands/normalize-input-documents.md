---
description: Normalize Office input documents to cached Markdown
agent: build
---

Use the repository skill `normalize-input-documents`.

Treat the command arguments below as the skill `$ARGUMENTS`:

```text
$ARGUMENTS
```

This command only normalizes input documents. Do not create `outputs/runs/<run-id>/`, do not generate `test-analysis-solution.md`, and do not generate `test-design-solution.md`.

Supported argument hints:

- Office input document: `<input.docx>` or `<input.xlsx>`.
- Markdown input document: `<input.md>` or `<input.markdown>`; report that no conversion is needed.
- Multiple inputs are allowed.
- Optional force refresh: `--force`.
- Optional machine-readable output: `--json`.

Run from the repository root:

```text
python bin/normalize-office-input.py <arguments>
```

Use `outputs/input-cache/<sha256-12>/` as the fixed cache location. Report the normalized Markdown path, conversion metadata path, cache reuse status, and conversion warnings.

If conversion metadata reports images or warnings, read `skills/normalize-input-documents/references/docx-image-and-diagram-workflow.md` and, when the active model supports multimodal image understanding, supplement image, diagram, flowchart, architecture, screenshot, EMF, or Visio facts before downstream analysis or design uses the normalized input. Keep supplemental facts in the same cache directory or report that image understanding was not performed because the active model is not multimodal.

When the input is a large or complex Excel knowledge source, read `skills/normalize-input-documents/references/xlsx-to-markdown.md` and `skills/normalize-input-documents/references/xlsx-to-ai-knowledge-base.md` before deciding whether raw table conversion is sufficient.
