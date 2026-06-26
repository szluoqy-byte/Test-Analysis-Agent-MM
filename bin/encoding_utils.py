#!/usr/bin/env python3
"""Encoding helpers for command-line scripts.

The agent scripts print Chinese diagnostics and often call each other through
subprocesses. Some local shells still expose GBK/CP936 defaults, so CLI entry
points should pin text IO to UTF-8 explicitly.
"""

from __future__ import annotations

import os
import sys
from typing import Any


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def utf8_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def subprocess_text_kwargs() -> dict[str, Any]:
    return {"text": True, "encoding": "utf-8", "errors": "replace"}
