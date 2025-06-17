#!/usr/bin/env python3
"""
Django timezone.utc to datetime.timezone.utc fixer
Replaces django.utils.timezone.utc with datetime.timezone.utc
"""

from __future__ import annotations

import ast
import re


class DjangoTimezoneUtcFixer:
    """
    Fixes django.utils.timezone.utc usage by:
    1. Adding 'from datetime import timezone as dt_timezone' import
    2. Replacing 'timezone.utc' with 'dt_timezone.utc'

    This version preserves original formatting, comments, and whitespace.
    """

    def __init__(self, source_lines: list[str]):
        self.source_lines = source_lines
        self.has_django_timezone_import = False
        self.has_datetime_import = False
        self.datetime_import_line: int | None = None
        self.uses_timezone_utc = False
        self.changes_made = False

    def analyze_imports(self) -> None:
        """Analyze the source to understand current imports"""
        try:
            tree = ast.parse("\n".join(self.source_lines))

            # Only look at top-level nodes to avoid nested imports
            for node in tree.body:
                if isinstance(node, ast.ImportFrom):
                    if node.module == "django.utils" and any(
                        alias.name == "timezone" for alias in node.names
                    ):
                        self.has_django_timezone_import = True
                    elif node.module == "datetime":
                        self.has_datetime_import = True
                        # Find the actual line that contains the datetime import
                        for i, line in enumerate(self.source_lines):
                            if "from datetime import" in line:
                                self.datetime_import_line = i
                                break
                        # Make sure we don't already have timezone imported
                        for alias in node.names:
                            if alias.name == "timezone":
                                return  # Already has timezone imported, nothing to do

            # Now look for timezone.utc usage
            for node in ast.walk(tree):  # type: ignore[assignment]
                if (
                    isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Name)
                    and node.value.id == "timezone"
                    and node.attr == "utc"
                ):
                    self.uses_timezone_utc = True

        except SyntaxError:
            pass

    def fix_imports(self) -> None:
        """Fix the datetime import to include timezone as dt_timezone"""
        if not (self.uses_timezone_utc and self.has_django_timezone_import):
            return

        if self.has_datetime_import and self.datetime_import_line is not None:
            # Update existing datetime import
            line = self.source_lines[self.datetime_import_line]

            # Check if timezone is already imported
            if "timezone" not in line:
                # Preserve original line ending
                original_ending = ""
                clean_line = line.rstrip()
                if line != clean_line:
                    original_ending = line[len(clean_line) :]

                # Add timezone import to existing datetime import
                if clean_line.strip().endswith(")"):
                    # Multi-line import like: from datetime import (date, datetime)
                    clean_line = clean_line.rstrip().rstrip(")")
                    if not clean_line.endswith(","):
                        clean_line += ","
                    clean_line += " timezone as dt_timezone)"
                else:
                    # Single line import like: from datetime import date, datetime
                    if not clean_line.endswith(","):
                        clean_line += ","
                    clean_line += " timezone as dt_timezone"

                # Restore original line ending
                line = clean_line + original_ending

                self.source_lines[self.datetime_import_line] = line
                self.changes_made = True
        else:
            # Add new datetime import with timezone alias
            # Find the best position to insert (after existing imports)
            insert_pos = 0
            for i, line in enumerate(self.source_lines):
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("from "):
                    insert_pos = i + 1
                elif stripped.startswith("#") or stripped == "":
                    continue
                elif stripped.startswith('"""') or stripped.startswith("'''"):
                    # Skip docstrings - find end
                    quote = stripped[:3]
                    if stripped.count(quote) >= 2:
                        insert_pos = i + 1
                    else:
                        # Multi-line docstring
                        for j in range(i + 1, len(self.source_lines)):
                            if quote in self.source_lines[j]:
                                insert_pos = j + 1
                                break
                else:
                    break

            self.source_lines.insert(
                insert_pos, "from datetime import timezone as dt_timezone\n"
            )
            self.changes_made = True

    def fix_timezone_utc_usage(self) -> None:
        """Replace timezone.utc with dt_timezone.utc"""
        if not self.uses_timezone_utc:
            return

        # Use regex to replace timezone.utc with dt_timezone.utc
        # This preserves all formatting and context
        timezone_utc_pattern = r"\btimezone\.utc\b"

        for i, line in enumerate(self.source_lines):
            if re.search(timezone_utc_pattern, line):
                new_line = re.sub(timezone_utc_pattern, "dt_timezone.utc", line)
                if new_line != line:
                    self.source_lines[i] = new_line
                    self.changes_made = True


def fix_django_timezone_utc(source_code: str) -> tuple[str, bool]:
    """
    Fix django timezone.utc usage in the given source code.
    Returns (fixed_code, changes_made)
    """
    try:
        # Split into lines, preserving line endings
        lines = source_code.splitlines(keepends=True)

        fixer = DjangoTimezoneUtcFixer(lines)
        fixer.analyze_imports()
        fixer.fix_imports()
        fixer.fix_timezone_utc_usage()

        if fixer.changes_made:
            # Join lines back together
            fixed_code = "".join(fixer.source_lines)
            return fixed_code, True
        else:
            return source_code, False

    except Exception as e:
        print(f"Error processing source: {e}")
        return source_code, False
