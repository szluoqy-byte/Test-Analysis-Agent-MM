#!/usr/bin/env python3
"""Generate a stable run id for outputs/runs."""

from __future__ import annotations

from datetime import datetime

from encoding_utils import configure_stdio


def main() -> int:
    configure_stdio()
    print(datetime.now().strftime("%Y%m%d-%H%M%S"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
