"""Utility functions for reading glyph codepoints from the AWG edition glyphs data file."""

import re
from pathlib import Path

HEX_VALUE_PATTERN = re.compile(r"\bhex:\s*(['\"`])(.*?)\1")
UNICODE_ESCAPE_PATTERN = re.compile(r"\\u([0-9A-Fa-f]{4})")


class CodepointUtils:
    """A class that contains utility functions for reading and formatting glyph codepoints."""

    @staticmethod
    def read_codepoints(file_path: Path) -> list[int]:
        """Read the glyph codepoints from an ``edition-glyphs.data.ts`` file.

        Args:
            file_path (Path): Path to the TypeScript file containing ``EDITION_GLYPHS_DATA``.

        Returns:
            list[int]: The unique codepoints of all ``hex`` values, sorted in ascending order.
        """
        return CodepointUtils.parse_codepoints(file_path.read_text(encoding="utf-8"))

    @staticmethod
    def parse_codepoints(content: str) -> list[int]:
        """Parse the glyph codepoints from the ``hex`` values of a TypeScript source.

        Only ``\\uXXXX`` escapes inside ``hex`` string values (single, double or backtick
        quotes) are collected, so a value
        like ``'\\uE524\\uE520'`` yields two codepoints. Literal characters (e.g. the
        space in ``'\\uE1D3 \\uE1E7'``) and escapes outside ``hex`` values are ignored.

        Args:
            content (str): The TypeScript source text.

        Returns:
            list[int]: The unique codepoints, sorted in ascending order.

        Raises:
            ValueError: If no ``\\uXXXX`` escape is found in any ``hex`` value.
        """
        codepoints = {
            int(escape, 16)
            for hex_match in HEX_VALUE_PATTERN.finditer(content)
            for escape in UNICODE_ESCAPE_PATTERN.findall(hex_match.group(2))
        }
        if not codepoints:
            raise ValueError("No \\uXXXX escapes found in any hex value.")
        return sorted(codepoints)

    @staticmethod
    def format_codepoint(codepoint: int) -> str:
        """Format a codepoint in Unicode notation.

        Args:
            codepoint (int): The codepoint to format.

        Returns:
            str: The codepoint as ``U+XXXX`` (e.g. ``U+E264``).
        """
        return f"U+{codepoint:04X}"
