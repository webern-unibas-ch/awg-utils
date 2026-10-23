"""Tests for glyph_utils.py"""

import pytest

from tests.test_fixtures import GLYPHS_DATA_PATH
from utils.glyph_utils import GlyphUtils


class TestParseGlyphs:
    """Tests for the parse_glyphs function."""

    def test_classes_follow_sections(self, glyphs):
        """Test that each section of the glyph data maps to its CSS class."""
        assert glyphs["[#]"] == "glyph accid"
        assert glyphs["[bb]"] == "glyph accid"
        assert glyphs["[>]"] == "glyph"
        assert glyphs["[mp]"] == "glyph"
        assert glyphs["[Halbe Note]"] == "glyph note"
        assert glyphs["[Punktierte Halbe Note]"] == "glyph note"
        assert glyphs["[ped]"] == "glyph"

    def test_unknown_section_gets_plain_class(self):
        """Test that entries of an unknown section get the plain glyph class."""
        content = """
            /**            ORNAMENTS             /
            TRILL: {
                alt: '[tr]',
                hex: '\\uE566',
            },
        """
        assert GlyphUtils.parse_glyphs(content) == {"[tr]": "glyph"}

    def test_entry_before_first_section_gets_plain_class(self):
        """Test that entries before the first section comment get the plain glyph class."""
        content = """
            FORTE: { alt: '[f]', hex: '\\uE522' },
            /**            ACCIDENTALS             /
            FLAT: { alt: '[b]', hex: '\\uE260' },
        """
        assert GlyphUtils.parse_glyphs(content) == {"[f]": "glyph", "[b]": "glyph accid"}

    def test_section_after_other_section_resets_class(self):
        """Test that a following section replaces the class of the previous one."""
        content = """
            /**            NOTE VALUES             /
            NOTE_EIGHTH: { alt: '[Achtelnote]', hex: '\\uE1D7' },
            /**         PLAYING TECHNIQUES         /
            PEDAL: { alt: '[ped]', hex: '\\uE650' },
        """
        assert GlyphUtils.parse_glyphs(content) == {
            "[Achtelnote]": "glyph note",
            "[ped]": "glyph",
        }

    def test_double_quoted_alt_values(self):
        """Test that alt values in double quotes are parsed as well."""
        content = 'FORTE: { alt: "[f]", hex: "\\uE522" },'
        assert GlyphUtils.parse_glyphs(content) == {"[f]": "glyph"}

    def test_entry_without_alt_is_skipped(self):
        """Test that entries without an alt value are skipped."""
        content = """
            FORTE: { hex: '\\uE522' },
            PIANO: { alt: '[p]', hex: '\\uE520' },
        """
        assert GlyphUtils.parse_glyphs(content) == {"[p]": "glyph"}

    def test_empty_content(self):
        """Test that empty content returns an empty dict."""
        assert not GlyphUtils.parse_glyphs("")


class TestReadGlyphs:
    """Tests for the read_glyphs function."""

    def test_reads_all_entries_in_source_order(self):
        """Test that all entries of the glyph data are read in source order."""
        glyphs = GlyphUtils.read_glyphs(GLYPHS_DATA_PATH)

        assert list(glyphs) == [
            "[bb]",
            "[x]",
            "[b]",
            "[a]",
            "[#]",
            "[>]",
            "[f]",
            "[ff]",
            "[fff]",
            "[mp]",
            "[Achtelnote]",
            "[Halbe Note]",
            "[Punktierte Halbe Note]",
            "[Viertelnote]",
            "[Sechzehntelnote]",
            "[Ganze Note]",
            "[ped]",
        ]

    def test_accepts_str_path(self):
        """Test that the path may also be given as a string."""
        assert GlyphUtils.read_glyphs(str(GLYPHS_DATA_PATH)) == GlyphUtils.read_glyphs(
            GLYPHS_DATA_PATH
        )

    def test_missing_file_raises_error(self, tmp_path):
        """Test that a missing file raises a FileNotFoundError with a hint."""
        with pytest.raises(FileNotFoundError, match="--glyphs-data"):
            GlyphUtils.read_glyphs(tmp_path / "missing.data.ts")

    def test_file_without_entries_raises_error(self, tmp_path):
        """Test that a file without glyph entries raises a ValueError."""
        path = tmp_path / "empty.data.ts"
        path.write_text("export const EDITION_GLYPHS_DATA = {} as const;\n", encoding="utf-8")

        with pytest.raises(ValueError, match="No glyph entries"):
            GlyphUtils.read_glyphs(path)
