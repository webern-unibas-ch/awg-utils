"""Utility functions for file operations like writing the manifest and copying the license."""

import json
import shutil
from pathlib import Path
from typing import Any, Dict

from utils.codepoint_utils import CodepointUtils
from utils.constants import (
    FAMILY_NAME,
    FONT_FILENAME,
    LICENSE_FILENAME,
    POSTSCRIPT_NAME,
    SOURCE_FONT_NAME,
    STYLE_NAME,
    SUBSET_NOTE,
)


class FileUtils:
    """A class that contains utility functions for file operations like writing or copying."""

    @staticmethod
    def create_manifest(codepoints: list[int]) -> Dict[str, Any]:
        """Create the manifest describing the glyph subset.

        Args:
            codepoints (list[int]): The codepoints contained in the subset.

        Returns:
            Dict[str, Any]: The manifest with font names, file names, source and codepoints.
        """
        return {
            "family": FAMILY_NAME,
            "style": STYLE_NAME,
            "postscriptName": POSTSCRIPT_NAME,
            "file": FONT_FILENAME,
            "license": LICENSE_FILENAME,
            "source": SOURCE_FONT_NAME,
            "note": SUBSET_NOTE,
            "count": len(codepoints),
            "codepoints": [CodepointUtils.format_codepoint(codepoint) for codepoint in codepoints],
        }

    @staticmethod
    def write_manifest(manifest_path: Path, codepoints: list[int]) -> None:
        """Write the manifest as JSON.

        Args:
            manifest_path (Path): Path to the output JSON file.
            codepoints (list[int]): The codepoints contained in the subset.
        """
        content = json.dumps(FileUtils.create_manifest(codepoints), ensure_ascii=False, indent=4)
        manifest_path.write_text(f"{content}\n", encoding="utf-8")

    @staticmethod
    def copy_license(license_path: Path, out_dir: Path) -> Path:
        """Copy the license file into the output folder.

        Args:
            license_path (Path): Path to the source ``OFL.txt``.
            out_dir (Path): The output folder.

        Returns:
            Path: Path to the copied license file.
        """
        return Path(shutil.copyfile(license_path, out_dir / LICENSE_FILENAME))
