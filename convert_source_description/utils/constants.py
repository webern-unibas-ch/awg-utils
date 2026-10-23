"""Shared string and parsing constants for convert_source_description utilities."""

from pathlib import Path

# awg-app is expected next to awg-utils (both repos in the same folder)
AWG_APP_DIR = Path(__file__).resolve().parents[3] / "awg-app"
DEFAULT_GLYPHS_DATA_PATH = (
    AWG_APP_DIR / "src" / "app" / "views" / "edition-view" / "data" / "edition-glyphs.data.ts"
)
GLYPH_CLASS = "glyph"
GLYPH_SECTION_CLASSES = {
    "ACCIDENTALS": "glyph accid",
    "NOTE VALUES": "glyph note",
}

FOLIO_STR = "Bl."
M_SIGLE = "M "
MX_SIGLE = "M* "
MEASURE_STR = "T."
PAGE_STR = "S."
ROWTABLE_SHEET_ID = "SkRT"
STAR_REPLACEMENT_STR = "x"
SYSTEM_STR = "System"

COLON = ":"
COMMA = ","
FULL_STOP = "."
PARENTHESIS = "("
SEMICOLON = ";"
SLASH = "/"
STAR = "*"
UNDERSCORE = "_"

P_TAG = "p"
STRONG_TAG = "strong"
SUP_TAG = "sup"
