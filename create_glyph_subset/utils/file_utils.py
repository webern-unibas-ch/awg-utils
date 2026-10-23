"""Utility functions for file operations like hashing, writing the manifest, copying the license."""

import hashlib
import json
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
    def hash_file(file_path: Path) -> str:
        """Compute the SHA-256 hash of a file from its bytes on disk.

        Args:
            file_path (Path): Path to the file to hash.

        Returns:
            str: The SHA-256 hash as 64 lowercase hex characters.
        """
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    @staticmethod
    def create_manifest(codepoints: list[int], font_sha256: str) -> Dict[str, Any]:
        """Create the manifest describing the glyph subset.

        Args:
            codepoints (list[int]): The codepoints contained in the subset.
            font_sha256 (str): The SHA-256 hash of the written font file.

        Returns:
            Dict[str, Any]: The manifest with font names, file names, font hash, source and
            codepoints.
        """
        return {
            "family": FAMILY_NAME,
            "style": STYLE_NAME,
            "postscriptName": POSTSCRIPT_NAME,
            "file": FONT_FILENAME,
            "sha256": font_sha256,
            "license": LICENSE_FILENAME,
            "source": SOURCE_FONT_NAME,
            "note": SUBSET_NOTE,
            "count": len(codepoints),
            "codepoints": [CodepointUtils.format_codepoint(codepoint) for codepoint in codepoints],
        }

    @staticmethod
    def write_manifest(manifest_path: Path, codepoints: list[int], font_sha256: str) -> None:
        """Write the manifest as JSON with LF line endings.

        Args:
            manifest_path (Path): Path to the output JSON file.
            codepoints (list[int]): The codepoints contained in the subset.
            font_sha256 (str): The SHA-256 hash of the written font file.
        """
        manifest = FileUtils.create_manifest(codepoints, font_sha256)
        content = json.dumps(manifest, ensure_ascii=False, indent=4)
        manifest_path.write_text(f"{content}\n", encoding="utf-8", newline="\n")

    @staticmethod
    def copy_license(license_path: Path, out_dir: Path) -> Path:
        """Copy the license file into the output folder, normalized to LF line endings.

        The text is read and written instead of copied byte for byte, so a source
        checked out with CRLF (e.g. via ``core.autocrlf``) still yields an LF copy.

        Args:
            license_path (Path): Path to the source ``OFL.txt``.
            out_dir (Path): The output folder.

        Returns:
            Path: Path to the copied license file.
        """
        out_path = out_dir / LICENSE_FILENAME
        license_text = license_path.read_text(encoding="utf-8")
        out_path.write_text(license_text, encoding="utf-8", newline="\n")
        return out_path
