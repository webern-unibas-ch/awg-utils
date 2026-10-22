"""Tests for utils/codepoint_utils.py"""

import pytest

from utils.codepoint_utils import CodepointUtils


class TestReadCodepoints:
    """Tests for the read_codepoints function."""

    def test_reads_exact_codepoints_from_data_file(self, glyphs_data_path, expected_codepoints):
        """Test that the codepoints of the data file match the expected sorted list exactly."""
        assert CodepointUtils.read_codepoints(glyphs_data_path) == expected_codepoints

    def test_reads_all_escapes_of_multi_glyph_values(self, glyphs_data_path):
        """Test that values with several escapes (e.g. SUBITO_PIANO) add all codepoints."""
        codepoints = CodepointUtils.read_codepoints(glyphs_data_path)
        assert 0xE524 in codepoints
        assert 0xE1E7 in codepoints

    def test_returns_unique_codepoints(self, glyphs_data_path):
        """Test that codepoints used in several values are listed only once."""
        codepoints = CodepointUtils.read_codepoints(glyphs_data_path)
        assert codepoints.count(0xE520) == 1
        assert codepoints.count(0xE1D3) == 1
        assert len(codepoints) == len(set(codepoints))

    def test_ignores_literal_space(self, glyphs_data_path):
        """Test that the literal space in NOTE_HALF_DOTTED is not added as a codepoint."""
        assert 0x20 not in CodepointUtils.read_codepoints(glyphs_data_path)

    def test_raises_on_missing_file(self, tmp_path):
        """Test that an OSError is raised when the file does not exist."""
        with pytest.raises(OSError):
            CodepointUtils.read_codepoints(tmp_path / "missing.ts")


class TestParseCodepoints:
    """Tests for the parse_codepoints function."""

    def test_parses_single_escape(self):
        """Test that a single escape is parsed to its codepoint."""
        assert CodepointUtils.parse_codepoints("FLAT: { hex: '\\uE260' },") == [0xE260]

    def test_returns_sorted_codepoints(self):
        """Test that the codepoints are sorted regardless of their order in the source."""
        content = "A: { hex: '\\uE650' }, B: { hex: '\\uE260' }, C: { hex: '\\uE4A0' },"
        assert CodepointUtils.parse_codepoints(content) == [0xE260, 0xE4A0, 0xE650]

    def test_parses_lowercase_hex_digits(self):
        """Test that lowercase hex digits are accepted."""
        assert CodepointUtils.parse_codepoints("hex: '\\ue52f'") == [0xE52F]

    def test_parses_double_and_backtick_quotes(self):
        """Test that hex values in double quotes or backticks are parsed as well."""
        content = "A: { hex: \"\\uE260\" }, B: { hex: `\\uE262` }, C: { hex: '\\uE264' },"
        assert CodepointUtils.parse_codepoints(content) == [0xE260, 0xE262, 0xE264]

    def test_ignores_escapes_outside_hex_values(self):
        """Test that escapes in comments or other properties are not collected."""
        content = (
            "/** The glyph \\uE000 in a comment. */\n"
            "SHARP: { alt: '\\uE001', hex: '\\uE262' },\n"
        )
        assert CodepointUtils.parse_codepoints(content) == [0xE262]

    def test_raises_without_hex_values(self):
        """Test that a ValueError is raised when no hex value is found."""
        with pytest.raises(ValueError, match="No \\\\uXXXX escapes"):
            CodepointUtils.parse_codepoints("export const EMPTY = {} as const;")

    def test_raises_without_escapes(self):
        """Test that a ValueError is raised when hex values contain no escape."""
        with pytest.raises(ValueError):
            CodepointUtils.parse_codepoints("SPACE: { hex: ' ' },")


class TestFormatCodepoint:
    """Tests for the format_codepoint function."""

    def test_formats_in_unicode_notation(self):
        """Test that a codepoint is formatted as U+XXXX with uppercase digits."""
        assert CodepointUtils.format_codepoint(0xE52F) == "U+E52F"

    def test_pads_to_four_digits(self):
        """Test that small codepoints are zero-padded to four digits."""
        assert CodepointUtils.format_codepoint(0x20) == "U+0020"
