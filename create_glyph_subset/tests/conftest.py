"""Pytest configuration for shared test fixtures."""

from pathlib import Path

import pytest

from create_glyph_subset import create_glyph_subset
from utils.constants import DEFAULT_FONT_PATH

DATA_DIR = Path(__file__).resolve().parent / "data"
GLYPHS_DATA_PATH = DATA_DIR / "edition-glyphs.data.ts"

EXPECTED_CODEPOINTS = [
    0xE1D2, 0xE1D3, 0xE1D5, 0xE1D7, 0xE1D9, 0xE1E7,
    0xE260, 0xE261, 0xE262, 0xE263, 0xE264,
    0xE4A0,
    0xE520, 0xE522, 0xE524, 0xE529, 0xE52A, 0xE52B, 0xE52C,
    0xE52D, 0xE52F, 0xE530, 0xE531, 0xE536, 0xE539,
    0xE650,
]


@pytest.fixture(name="glyphs_data_path")
def fixture_glyphs_data_path() -> Path:
    """Path to the copy of awg-app's edition-glyphs.data.ts."""
    return GLYPHS_DATA_PATH


@pytest.fixture(name="expected_codepoints")
def fixture_expected_codepoints() -> list[int]:
    """The 26 unique codepoints of EDITION_GLYPHS_DATA, sorted in ascending order."""
    return list(EXPECTED_CODEPOINTS)


@pytest.fixture(name="source_font_path")
def fixture_source_font_path() -> Path:
    """Path to the committed Bravura 1.380 WOFF2."""
    return DEFAULT_FONT_PATH


@pytest.fixture(name="subset_out_dir", scope="session")
def fixture_subset_out_dir(tmp_path_factory) -> Path:
    """Output folder of one full run of create_glyph_subset, shared across tests.

    The folder is nested and does not exist before the run, so the run also covers its creation.
    """
    out_dir = tmp_path_factory.mktemp("subset") / "nested" / "out"
    create_glyph_subset(GLYPHS_DATA_PATH, DEFAULT_FONT_PATH, out_dir)
    return out_dir
