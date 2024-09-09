#!/usr/bin/env python
from __future__ import annotations

import os
import subprocess
import sys
from functools import partial
from pathlib import Path

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    common_args = [
        "uv",
        "pip",
        "compile",
        "--quiet",
        "--generate-hashes",
        "requirements.in",
        *sys.argv[1:],
    ]
    run = partial(subprocess.run, check=True)
    run([*common_args, "--python", "3.8", "--output-file", "py38.txt"])
    run([*common_args, "--python", "3.9", "--output-file", "py39.txt"])
    run([*common_args, "--python", "3.10", "--output-file", "py310.txt"])
    run([*common_args, "--python", "3.11", "--output-file", "py311.txt"])
    run([*common_args, "--python", "3.12", "--output-file", "py312.txt"])
    run([*common_args, "--python", "3.13", "--output-file", "py313.txt"])
