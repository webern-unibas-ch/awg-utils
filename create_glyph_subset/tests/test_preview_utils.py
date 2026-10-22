"""Tests for utils/preview_utils.py"""

import base64

import pytest

from utils.constants import FONT_FILENAME, POSTSCRIPT_NAME, SUBSET_NOTE
from utils.font_utils import FontUtils
from utils.preview_utils import GlyphEntry, GlyphGroup, PreviewUtils


@pytest.fixture(name="glyph_groups")
def fixture_glyph_groups(glyphs_data_path) -> list[GlyphGroup]:
    """The glyph groups parsed from the copy of edition-glyphs.data.ts."""
    return PreviewUtils.parse_glyph_groups(glyphs_data_path.read_text(encoding="utf-8"))


@pytest.fixture(name="subset_font_path")
def fixture_subset_font_path(subset_out_dir):
    """Path to the font written by the shared full run of create_glyph_subset."""
    return subset_out_dir / FONT_FILENAME


@pytest.fixture(name="flat_only_font_path")
def fixture_flat_only_font_path(source_font_path, tmp_path):
    """Path to a renamed subset that contains only the flat sign (U+E260)."""
    font = FontUtils.load_font(source_font_path)
    FontUtils.subset_font(font, [0xE260])
    FontUtils.rename_font(font)
    font_path = tmp_path / FONT_FILENAME
    FontUtils.save_font(font, font_path)
    return font_path


def find_entry(groups: list[GlyphGroup], key: str) -> GlyphEntry:
    """Return the glyph entry with the given key."""
    return next(entry for group in groups for entry in group.entries if entry.key == key)


class TestParseGlyphGroups:
    """Tests for the parse_glyph_groups function."""

    def test_groups_by_section_comments(self, glyph_groups):
        """Test that the entries are grouped by the section comments, in source order."""
        assert [group.title for group in glyph_groups] == [
            "Accidentals",
            "Articulations",
            "Dynamics",
            "Note Values",
            "Playing Techniques",
        ]

    def test_parses_all_entries(self, glyph_groups):
        """Test that all 26 entries are parsed, in source order within a group."""
        assert sum(len(group.entries) for group in glyph_groups) == 26
        assert [entry.key for entry in glyph_groups[0].entries] == [
            "DOUBLE_FLAT",
            "DOUBLE_SHARP",
            "FLAT",
            "NATURAL",
            "SHARP",
        ]

    def test_parses_entry_with_several_escapes(self, glyph_groups):
        """Test that a value with several escapes keeps all glyphs and codepoints in order."""
        entry = find_entry(glyph_groups, "SUBITO_PIANO")
        assert entry.alt == "[sp]"
        assert entry.text == chr(0xE524) + chr(0xE520)
        assert entry.codepoints == [0xE524, 0xE520]

    def test_keeps_literal_characters_in_text(self, glyph_groups):
        """Test that literal characters like the space in NOTE_HALF_DOTTED stay in the text."""
        entry = find_entry(glyph_groups, "NOTE_HALF_DOTTED")
        assert entry.text == chr(0xE1D3) + " " + chr(0xE1E7)
        assert entry.codepoints == [0xE1D3, 0xE1E7]

    def test_collects_entries_before_first_section(self):
        """Test that entries before the first section comment are grouped as Glyphs."""
        groups = PreviewUtils.parse_glyph_groups("FLAT: { alt: '[b]', hex: '\\uE260' },")
        assert [group.title for group in groups] == ["Glyphs"]
        assert groups[0].entries[0].codepoints == [0xE260]

    def test_skips_entries_without_hex_and_empty_sections(self):
        """Test that entries without hex value and sections without entries are left out."""
        content = (
            "    /**            EMPTY             /\n"
            "    OTHER: { alt: '[x]' },\n"
            "    /**            ACCIDENTALS             /\n"
            "    FLAT: { alt: '[b]', hex: '\\uE260' },\n"
        )
        groups = PreviewUtils.parse_glyph_groups(content)
        assert [group.title for group in groups] == ["Accidentals"]
        assert [entry.key for entry in groups[0].entries] == ["FLAT"]

    def test_accepts_double_quotes_and_missing_alt(self):
        """Test that double-quoted values are parsed and a missing alt text is empty."""
        groups = PreviewUtils.parse_glyph_groups('SHARP: { hex: "\\uE262" },')
        assert groups[0].entries[0].alt == ""
        assert groups[0].entries[0].codepoints == [0xE262]


class TestRenderPreview:
    """Tests for the render_preview function."""

    def test_embeds_font_as_data_uri(self, glyph_groups, subset_font_path):
        """Test that the font is embedded as base64 WOFF2 data URI."""
        page = PreviewUtils.render_preview(glyph_groups, subset_font_path)
        font_base64 = base64.b64encode(subset_font_path.read_bytes()).decode("ascii")
        assert f"data:font/woff2;base64,{font_base64}" in page

    def test_renders_one_card_per_entry(self, glyph_groups, subset_font_path):
        """Test that every entry gets a card and none is marked as missing."""
        page = PreviewUtils.render_preview(glyph_groups, subset_font_path)
        assert page.count('<figure class="card') == 26
        assert 'class="card missing"' not in page
        assert '<code class="key">DOUBLE_FLAT</code>' in page
        assert "[bb] · U+E264" in page
        assert "U+E524 + U+E520" in page

    def test_shows_font_names_and_status(self, glyph_groups, subset_font_path):
        """Test that the font names from the name table and the cmap status are shown."""
        page = PreviewUtils.render_preview(glyph_groups, subset_font_path)
        assert "<h1>AWG Edition Glyphs</h1>" in page
        assert POSTSCRIPT_NAME in page
        assert SUBSET_NOTE in page
        assert '<span class="status">26 / 26 in cmap</span>' in page

    def test_uses_dynamics_for_inline_sample(self, glyph_groups, subset_font_path):
        """Test that the inline sample shows the first six dynamics glyphs."""
        page = PreviewUtils.render_preview(glyph_groups, subset_font_path)
        assert page.count('<span class="g">') == 6
        assert f'<span class="g">{chr(0xE522)}</span>' in page

    def test_falls_back_to_all_entries_for_inline_sample(self, subset_font_path):
        """Test that the inline sample uses all entries if there is no Dynamics group."""
        groups = [GlyphGroup("Accidentals", [GlyphEntry("FLAT", "[b]", chr(0xE260), [0xE260])])]
        page = PreviewUtils.render_preview(groups, subset_font_path)
        assert page.count('<span class="g">') == 1

    def test_marks_missing_glyphs(self, glyph_groups, flat_only_font_path):
        """Test that entries with glyphs missing in the font are marked and the status is bad."""
        page = PreviewUtils.render_preview(glyph_groups, flat_only_font_path)
        assert page.count('class="card missing"') == 25
        assert '<span class="status bad">1 / 26 in cmap</span>' in page

    def test_escapes_html(self, subset_font_path):
        """Test that keys, alt texts and titles are HTML-escaped."""
        groups = [GlyphGroup("A & B", [GlyphEntry("FLAT", "<b>", chr(0xE260), [0xE260])])]
        page = PreviewUtils.render_preview(groups, subset_font_path)
        assert "<h2>A &amp; B</h2>" in page
        assert "&lt;b&gt;" in page


class TestWritePreview:
    """Tests for the write_preview function."""

    def test_writes_html_page(self, glyphs_data_path, subset_font_path, tmp_path):
        """Test that the preview is written as a complete HTML page."""
        preview_path = tmp_path / "preview.html"
        PreviewUtils.write_preview(preview_path, glyphs_data_path, subset_font_path)
        page = preview_path.read_text(encoding="utf-8")
        assert page.startswith("<!doctype html>")
        assert page.count('<figure class="card') == 26

    def test_overwrites_existing_preview(self, glyphs_data_path, subset_font_path, tmp_path):
        """Test that an existing preview is replaced, not appended to."""
        preview_path = tmp_path / "preview.html"
        preview_path.write_text("old content", encoding="utf-8")
        PreviewUtils.write_preview(preview_path, glyphs_data_path, subset_font_path)
        assert "old content" not in preview_path.read_text(encoding="utf-8")
