#!/usr/bin/env python3
"""Generate a stable run id for outputs/runs."""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime


RUN_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")
RUN_ID_ENV_VAR = "TEST_ANALYSIS_RUN_ID"


def injected_run_id() -> str | None:
    value = os.environ.get(RUN_ID_ENV_VAR, "").strip()
    if not value:
        return None
    if not RUN_ID_RE.fullmatch(value):
        print(
            f"Invalid run id from {RUN_ID_ENV_VAR}: only letters, numbers, dot, underscore and hyphen are allowed",
            file=sys.stderr,
        )
        return ""
    return value
    return None


def main() -> int:
    injected = injected_run_id()
    if injected == "":
        return 2
    if injected:
        print(injected)
        return 0
    print(datetime.now().strftime("%Y%m%d-%H%M%S"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
