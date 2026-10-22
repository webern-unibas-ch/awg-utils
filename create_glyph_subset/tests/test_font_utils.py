"""Tests for utils/font_utils.py"""

import hashlib

import pytest
from fontTools.ttLib import TTFont

from utils.constants import (
    FAMILY_NAME,
    FONT_FILENAME,
    FULL_NAME,
    POSTSCRIPT_NAME,
    STYLE_NAME,
    SUBSET_NOTE,
)
from utils.font_utils import FontUtils

RENAMED_NAME_IDS = (1, 2, 4, 6, 16, 17)


def get_names(font: TTFont, name_id: int) -> list[str]:
    """Return all strings of a name ID across all platform records."""
    return [record.toUnicode() for record in font["name"].names if record.nameID == name_id]


@pytest.fixture(name="subset_font")
def fixture_subset_font(subset_out_dir) -> TTFont:
    """The font written by the shared full run of create_glyph_subset."""
    return TTFont(subset_out_dir / FONT_FILENAME)


@pytest.fixture(name="renamed_font")
def fixture_renamed_font(source_font_path) -> TTFont:
    """A freshly subset and renamed font, with typographic names 16/17 added beforehand."""
    font = FontUtils.load_font(source_font_path)
    FontUtils.subset_font(font, [0xE260, 0xE262])
    font["name"].setName("Bravura", 16, 3, 1, 0x409)
    font["name"].setName("Regular", 17, 3, 1, 0x409)
    FontUtils.rename_font(font)
    return font


class TestLoadFont:
    """Tests for the load_font function."""

    def test_loads_woff2(self, source_font_path):
        """Test that the source font is loaded as a WOFF2 CFF font."""
        font = FontUtils.load_font(source_font_path)
        assert font.flavor == "woff2"
        assert font.sfntVersion == "OTTO"

    def test_disables_timestamp_recalculation(self, source_font_path):
        """Test that the font keeps its timestamp on save, for reproducible output."""
        assert FontUtils.load_font(source_font_path).recalcTimestamp is False


class TestCheckCodepoints:
    """Tests for the check_codepoints function."""

    def test_passes_for_available_codepoints(self, source_font_path, expected_codepoints):
        """Test that no error is raised when all codepoints are in the font."""
        FontUtils.check_codepoints(FontUtils.load_font(source_font_path), expected_codepoints)

    def test_raises_for_missing_codepoints(self, source_font_path):
        """Test that a ValueError names every codepoint missing in the font."""
        font = FontUtils.load_font(source_font_path)
        with pytest.raises(ValueError, match="U\\+0041, U\\+10FFFF"):
            FontUtils.check_codepoints(font, [0x41, 0xE260, 0x10FFFF])

    def test_raises_for_font_without_unicode_cmap(self, source_font_path):
        """Test that a font without a Unicode cmap reports all codepoints as missing."""
        font = FontUtils.load_font(source_font_path)
        font["cmap"].tables = []
        with pytest.raises(ValueError, match="U\\+E260"):
            FontUtils.check_codepoints(font, [0xE260])


class TestSubsetFont:
    """Tests for the subset_font function."""

    def test_cmap_matches_codepoints(self, subset_font, expected_codepoints):
        """Test that the subset maps exactly the requested codepoints."""
        assert sorted(subset_font.getBestCmap()) == expected_codepoints

    def test_keeps_glyphs_of_codepoints(self, subset_font):
        """Test that the subset keeps the original glyph of a codepoint."""
        assert subset_font.getBestCmap()[0xE264] == "uniE264"

    @pytest.mark.parametrize("name_id", [7, 8, 9, 11, 12, 13, 14])
    def test_keeps_other_name_ids(self, subset_font, name_id):
        """Test that trademark, designer, URL and license entries of the source font are kept."""
        assert get_names(subset_font, name_id)

    def test_subsets_in_place(self, source_font_path):
        """Test that the font object itself is reduced to the requested codepoints."""
        font = FontUtils.load_font(source_font_path)
        FontUtils.subset_font(font, [0xE260])
        assert list(font.getBestCmap()) == [0xE260]


class TestAddSubsetNote:
    """Tests for the add_subset_note function."""

    def test_inserts_note_after_first_paragraph(self):
        """Test that the note is inserted between the copyright statement and the license text."""
        result = FontUtils.add_subset_note("Copyright X.\n\nLicense text.\n\nMore.")
        assert result == f"Copyright X.\n\n{SUBSET_NOTE}.\n\nLicense text.\n\nMore."

    def test_appends_note_to_single_paragraph(self):
        """Test that the note is appended when the copyright has a single paragraph."""
        assert FontUtils.add_subset_note("Copyright X.") == f"Copyright X. {SUBSET_NOTE}."


class TestRenameFont:
    """Tests for the rename_font function."""

    @pytest.mark.parametrize(
        "name_id, expected",
        [
            (1, FAMILY_NAME),
            (2, STYLE_NAME),
            (4, FULL_NAME),
            (6, POSTSCRIPT_NAME),
            (10, SUBSET_NOTE),
        ],
    )
    def test_sets_names(self, subset_font, name_id, expected):
        """Test that family, style, full, PostScript name and description are set everywhere."""
        names = get_names(subset_font, name_id)
        assert names
        assert all(name == expected for name in names)

    def test_sets_unique_id_with_version(self, subset_font):
        """Test that the unique ID combines the source version and the PostScript name."""
        assert get_names(subset_font, 3) == [f"Version 1.38;{POSTSCRIPT_NAME}"]

    def test_sets_unique_id_without_version(self, source_font_path):
        """Test that the unique ID falls back to the PostScript name if there is no version."""
        font = FontUtils.load_font(source_font_path)
        font["name"].removeNames(nameID=5)
        FontUtils.rename_font(font)
        assert set(get_names(font, 3)) == {POSTSCRIPT_NAME}

    def test_keeps_version(self, subset_font):
        """Test that the version string of the source font is kept."""
        assert get_names(subset_font, 5) == ["Version 1.38"]

    def test_removes_reserved_font_name(self, subset_font):
        """Test that "Bravura" is not used in any primary font name."""
        for name_id in RENAMED_NAME_IDS:
            assert not any("Bravura" in name for name in get_names(subset_font, name_id))

    def test_keeps_copyright_and_adds_note(self, subset_font):
        """Test that the Steinberg copyright is kept and extended by the subset note."""
        copyrights = get_names(subset_font, 0)
        assert copyrights
        for copyright_text in copyrights:
            assert copyright_text.startswith("Copyright")
            assert "Steinberg Media Technologies GmbH" in copyright_text
            assert f"{SUBSET_NOTE}." in copyright_text
            assert "SIL OPEN FONT LICENSE" in copyright_text

    def test_removes_typographic_names(self, renamed_font):
        """Test that the typographic family and subfamily names 16/17 are removed."""
        assert not get_names(renamed_font, 16)
        assert not get_names(renamed_font, 17)

    def test_renames_cff(self, subset_font):
        """Test that the font names in the CFF table are renamed."""
        cff = subset_font["CFF "].cff
        top_dict = cff.topDictIndex[0]
        assert cff.fontNames == [POSTSCRIPT_NAME]
        assert top_dict.FamilyName == FAMILY_NAME
        assert top_dict.FullName == FULL_NAME

    def test_skips_cff_for_fonts_without_cff(self, renamed_font):
        """Test that fonts without a CFF table are renamed in the name table only."""
        del renamed_font["CFF "]
        FontUtils.rename_font(renamed_font)
        assert get_names(renamed_font, 6) == [POSTSCRIPT_NAME]


class TestSaveFont:
    """Tests for the save_font function."""

    def test_saves_woff2(self, subset_font):
        """Test that the saved font is a WOFF2."""
        assert subset_font.flavor == "woff2"

    def test_is_much_smaller_than_source(self, subset_out_dir, source_font_path):
        """Test that the subset is a small fraction of the source font."""
        subset_size = (subset_out_dir / FONT_FILENAME).stat().st_size
        assert subset_size < source_font_path.stat().st_size / 10

    def test_output_is_reproducible(self, source_font_path, tmp_path):
        """Test that two runs produce byte-identical files."""
        hashes = []
        for run in ("a", "b"):
            font = FontUtils.load_font(source_font_path)
            FontUtils.subset_font(font, [0xE260, 0xE262])
            FontUtils.rename_font(font)
            out_path = tmp_path / f"{run}.woff2"
            FontUtils.save_font(font, out_path)
            hashes.append(hashlib.sha256(out_path.read_bytes()).hexdigest())
        assert hashes[0] == hashes[1]
