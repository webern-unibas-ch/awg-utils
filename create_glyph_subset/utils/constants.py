"""Constants for creating the AWG edition glyph subset of Bravura."""

from pathlib import Path

SOURCE_FONT_NAME = "Bravura 1.380"
DEFAULT_FONT_DIR = Path(__file__).resolve().parent.parent / "fonts" / "bravura-1.380"
DEFAULT_FONT_PATH = DEFAULT_FONT_DIR / "Bravura.woff2"

FAMILY_NAME = "AWG Edition Glyphs"
STYLE_NAME = "Regular"
FULL_NAME = f"{FAMILY_NAME} {STYLE_NAME}"
POSTSCRIPT_NAME = "AWGEditionGlyphs-Regular"
SUBSET_NOTE = f"Subset of {SOURCE_FONT_NAME} for the AWG Online Edition"

FONT_FILENAME = f"{POSTSCRIPT_NAME}.woff2"
MANIFEST_FILENAME = "AWGEditionGlyphs.json"
LICENSE_FILENAME = "OFL.txt"
PREVIEW_FILENAME = "AWGEditionGlyphs-preview.html"
