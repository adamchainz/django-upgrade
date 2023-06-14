#!/usr/bin/env python
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    os.environ["CUSTOM_COMPILE_COMMAND"] = "requirements/compile.py"
    os.environ["PIP_REQUIRE_VIRTUALENV"] = "0"
    common_args = [
        "-m",
        "piptools",
        "compile",
        "--generate-hashes",
        "--allow-unsafe",
    ] + sys.argv[1:]
    subprocess.run(
        ["python3.8", *common_args, "-o", "py38.txt"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["python3.9", *common_args, "-o", "py39.txt"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["python3.10", *common_args, "-o", "py310.txt"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["python3.11", *common_args, "-o", "py311.txt"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["python3.12", *common_args, "-o", "py312.txt"],
        check=True,
        capture_output=True,
    )
