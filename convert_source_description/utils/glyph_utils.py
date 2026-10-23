"""Utility functions for reading the glyph names of the AWG edition from awg-app."""

import re
from pathlib import Path

from utils.constants import GLYPH_CLASS, GLYPH_SECTION_CLASSES

# Same patterns as in create_glyph_subset/utils/preview_utils.py (tools stay self-contained)
SECTION_PATTERN = re.compile(r"^\s*/\*\*\s+([A-Z][A-Z ]*?)\s+/\s*$", re.MULTILINE)
ENTRY_PATTERN = re.compile(r"(\w+):\s*\{([^{}]*)\}")
ALT_VALUE_PATTERN = re.compile(r"\balt:\s*(['\"`])(.*?)\1")


############################################
# Public class: GlyphUtils
############################################
class GlyphUtils:
    """A class that contains utility functions for reading the glyphs of the AWG edition."""

    ############################################
    # Public static method: parse_glyphs
    ############################################
    @staticmethod
    def parse_glyphs(content: str) -> dict[str, str]:
        """Parses the glyph names and their CSS classes from ``EDITION_GLYPHS_DATA``.

        The glyph name is the ``alt`` value including its square brackets (e.g. ``[f]``).
        The CSS class is derived from the preceding section comment (e.g. ACCIDENTALS);
        entries in an unknown section or before the first section get the plain class.
        Entries without an ``alt`` value are skipped.

        Args:
            content (str): The TypeScript source text of ``edition-glyphs.data.ts``.

        Returns:
            dict[str, str]: The CSS class for each glyph name, in source order.
        """
        tokens = [(match.start(), match) for match in SECTION_PATTERN.finditer(content)]
        tokens += [(match.start(), match) for match in ENTRY_PATTERN.finditer(content)]

        glyphs: dict[str, str] = {}
        css_class = GLYPH_CLASS
        for _, match in sorted(tokens, key=lambda token: token[0]):
            if match.re is SECTION_PATTERN:
                css_class = GLYPH_SECTION_CLASSES.get(match.group(1), GLYPH_CLASS)
                continue
            alt_match = ALT_VALUE_PATTERN.search(match.group(2))
            if alt_match:
                glyphs[alt_match.group(2)] = css_class
        return glyphs

    ############################################
    # Public static method: read_glyphs
    ############################################
    @staticmethod
    def read_glyphs(path: Path | str) -> dict[str, str]:
        """Reads the glyph names and their CSS classes from ``edition-glyphs.data.ts``.

        Args:
            path (Path | str): Path to ``edition-glyphs.data.ts`` of awg-app.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file contains no glyph entry.

        Returns:
            dict[str, str]: The CSS class for each glyph name, in source order.
        """
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(
                f"Glyph data not found: {path}. Clone awg-app next to awg-utils "
                "or pass the path with --glyphs-data."
            )
        glyphs = GlyphUtils.parse_glyphs(path.read_text(encoding="utf-8"))
        if not glyphs:
            raise ValueError(f"No glyph entries with an alt value found in {path}.")
        return glyphs
