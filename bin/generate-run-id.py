#!/usr/bin/env python3
"""Generate a stable run id for outputs/runs."""

from __future__ import annotations

from datetime import datetime


def main() -> int:
    print(datetime.now().strftime("%Y%m%d-%H%M%S"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
