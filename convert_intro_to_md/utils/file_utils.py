"""Utility functions for file operations."""

import json
import sys
from pathlib import Path
from typing import Any, Dict


def read_json(file_path: Path) -> Dict[str, Any]:
    """Read and parse a JSON file, exiting with an error message on failure."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


def write_md(file_path: Path, content: str) -> None:
    """Write Markdown content to a file, creating parent directories as needed."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
