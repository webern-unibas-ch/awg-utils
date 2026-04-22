# pylint: disable=protected-access
"""Tests for sources_utils.py"""

from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup

from utils.index_utils import IndexUtils
from utils.sources_utils import SourcesUtils
from utils.stripping_utils import StrippingUtils


@pytest.fixture(name="helper")
def fixture_helper():
    """Return an instance of SourcesUtils."""
    return SourcesUtils()


class TestCreateSourceList:
    """Tests for the create_source_list public method."""

    def _make_soup(self, *siglums: str) -> BeautifulSoup:
        """Build a minimal soup with one block of fixed paragraphs per siglum."""
        html = ""
        for siglum in siglums:
            html += (
                f"<p><strong>{siglum}</strong></p>"
                "<p>Typenbeschreibung</p>"
                "<p>CH-Basel, Paul Sacher Stiftung</p>"
                "<p>gut erhalten</p>"
            )
        return BeautifulSoup(html, "html.parser")

    def test_returns_empty_sources_when_no_siglum_found(self, helper):
        """Test that sources is empty when no siglum paragraphs are present."""
        soup = BeautifulSoup("<p>no siglum here</p>", "html.parser")
        with patch.object(IndexUtils, "find_siglum_indices", return_value=[]):
            result = helper.create_source_list(soup)
        assert result == {"sources": []}

    def test_appends_single_source_description(self, helper):
        """Test that a single source is appended when one siglum is found."""
        soup = self._make_soup("A")
        sentinel = {"id": "source_A"}
        with patch.object(helper, "_process_source_description", return_value=sentinel):
            result = helper.create_source_list(soup)
        assert result["sources"] == [sentinel]

    def test_appends_multiple_source_descriptions_in_order(self, helper):
        """Test that multiple sources are appended in document order."""
        soup = self._make_soup("A", "B")
        sentinels = [{"id": "source_A"}, {"id": "source_B"}]
        with patch.object(
            helper,
            "_process_source_description",
            side_effect=sentinels,
        ):
            result = helper.create_source_list(soup)
        assert result["sources"] == sentinels

    def test_does_not_append_duplicate_source(self, helper, capsys):
        """Test that a duplicate source_id is not appended a second time."""
        soup = self._make_soup("A", "A")
        duplicate = {"id": "source_A"}
        with patch.object(
            helper,
            "_process_source_description",
            side_effect=[duplicate, duplicate],
        ):
            result = helper.create_source_list(soup)
        assert len(result["sources"]) == 1

    def test_prints_duplication_warning_for_duplicate_source(self, helper, capsys):
        """Test that a duplication warning is printed for a duplicate source_id."""
        soup = self._make_soup("A", "A")
        duplicate = {"id": "source_A"}
        with patch.object(
            helper,
            "_process_source_description",
            side_effect=[duplicate, duplicate],
        ):
            helper.create_source_list(soup)
        assert (
            "Duplication: Source description for source_A included. Please check the source file."
            in capsys.readouterr().out
        )


class TestCreateSourceDescription:
    """Tests for the _process_source_description public method."""

    def _make_paras(self, siglum_html: str = "<p><strong>A</strong></p>") -> list:
        """Build a minimal paras list (siglum, type, location, condition)."""
        html = (
            siglum_html
            + "<p>Typenbeschreibung</p>"
            + "<p>CH-Basel, Paul Sacher Stiftung</p>"
            + "<p>gut erhalten</p>"
        )
        return BeautifulSoup(html, "html.parser").find_all("p")

    def test_sets_empty_id_when_siglum_is_empty(self, helper):
        """Test that id is empty when siglum cannot be extracted."""
        paras = self._make_paras("<p></p>")
        with patch.object(helper, "_process_phys_desc", return_value={}):
            result = helper._process_source_description(paras)
        assert result["id"] == ""

    def test_sets_id_from_siglum(self, helper):
        """Test that id is built as 'source_<siglum>'."""
        paras = self._make_paras()
        with patch.object(helper, "_process_phys_desc", return_value={}):
            result = helper._process_source_description(paras)
        assert result["id"] == "source_A"

    def test_sets_id_from_siglum_with_addendum(self, helper):
        """Test that id includes the addendum when present."""
        paras = self._make_paras("<p><strong>A<sup>c</sup></strong></p>")
        with patch.object(helper, "_process_phys_desc", return_value={}):
            result = helper._process_source_description(paras)
        assert result["id"] == "source_Ac"

    def test_sets_siglum_and_siglum_addendum(self, helper):
        """Test that siglum and siglumAddendum are set correctly."""
        paras = self._make_paras("<p><strong>B<sup>H</sup></strong></p>")
        with patch.object(helper, "_process_phys_desc", return_value={}):
            result = helper._process_source_description(paras)
        assert result["siglum"] == "B"
        assert result["siglumAddendum"] == "H"

    def test_missing_key_absent_for_non_missing_siglum(self, helper):
        """Test that 'missing' key is not present for a normal siglum."""
        paras = self._make_paras()
        with patch.object(helper, "_process_phys_desc", return_value={}):
            result = helper._process_source_description(paras)
        assert "missing" not in result

    def test_missing_key_inserted_at_position_3_for_bracketed_siglum(self, helper):
        """Test that 'missing: True' is inserted at position 3 for a bracketed siglum."""
        paras = self._make_paras("<p><strong>[A]</strong></p>")
        with patch.object(helper, "_process_phys_desc", return_value={}):
            result = helper._process_source_description(paras)
        keys = list(result.keys())
        assert result.get("missing") is True
        assert keys.index("missing") == 3

    def test_sets_type_from_paras_index_1(self, helper):
        """Test that 'type' is set from the stripped text of paras[1]."""
        paras = self._make_paras()
        with patch.object(helper, "_process_phys_desc", return_value={}):
            result = helper._process_source_description(paras)
        assert result["type"] == "Typenbeschreibung"

    def test_sets_location_from_paras_index_2(self, helper):
        """Test that 'location' is set from the stripped text of paras[2]."""
        paras = self._make_paras()
        with patch.object(helper, "_process_phys_desc", return_value={}):
            result = helper._process_source_description(paras)
        assert result["location"] == "CH-Basel, Paul Sacher Stiftung"

    def test_delegates_phys_desc_to_process_phys_desc(self, helper):
        """Test that physDesc is the return value of _process_phys_desc called with (paras, source_id)."""
        paras = self._make_paras()
        sentinel = {"conditions": ["gut erhalten"]}
        with patch.object(
            helper, "_process_phys_desc", return_value=sentinel
        ) as mock_phys:
            result = helper._process_source_description(paras)
        mock_phys.assert_called_once_with(paras, "source_A")
        assert result["physDesc"] == sentinel


class TestProcessSiglum:
    """Tests for the _process_siglum helper function."""

    def test_returns_simple_siglum(self, helper):
        """Test that a plain single-letter siglum is extracted."""
        # Arrange
        para = BeautifulSoup("<p><strong>A</strong></p>", "html.parser").p
        # Act
        siglum, addendum, is_missing = helper._process_siglum([para])
        # Assert
        assert siglum == "A"
        assert addendum == ""
        assert is_missing is False

    def test_returns_siglum_with_brackets(self, helper):
        """Test that a bracketed (missing) siglum strips brackets and sets the missing flag."""
        # Arrange
        para = BeautifulSoup("<p><strong>[A]</strong></p>", "html.parser").p
        # Act
        siglum, addendum, is_missing = helper._process_siglum([para])
        # Assert
        assert siglum == "A"
        assert addendum == ""
        assert is_missing is True

    def test_returns_siglum_with_lowercase_addendum(self, helper):
        """Test that a siglum with a lowercase superscript addendum is extracted."""
        # Arrange
        para = BeautifulSoup("<p><strong>A<sup>c</sup></strong></p>", "html.parser").p
        # Act
        siglum, addendum, is_missing = helper._process_siglum([para])
        # Assert
        assert siglum == "A"
        assert addendum == "c"
        assert is_missing is False

    def test_returns_siglum_with_uppercase_addendum(self, helper):
        """Test that a siglum with an uppercase superscript addendum is extracted."""
        # Arrange
        para = BeautifulSoup("<p><strong>B<sup>H</sup></strong></p>", "html.parser").p
        # Act
        siglum, addendum, is_missing = helper._process_siglum([para])
        # Assert
        assert siglum == "B"
        assert addendum == "H"
        assert is_missing is False

    def test_returns_siglum_with_addendum_and_digit(self, helper):
        """Test that a siglum with an alphanumeric superscript addendum is extracted."""
        # Arrange
        para = BeautifulSoup("<p><strong>C<sup>F1</sup></strong></p>", "html.parser").p
        # Act
        siglum, addendum, is_missing = helper._process_siglum([para])
        # Assert
        assert siglum == "C"
        assert addendum == "F1"
        assert is_missing is False

    def test_returns_siglum_with_addendum_range(self, helper):
        """Test that a siglum with a range superscript addendum is extracted."""
        # Arrange
        para = BeautifulSoup(
            "<p><strong>C<sup>F1–2</sup></strong></p>", "html.parser"
        ).p
        # Act
        siglum, addendum, is_missing = helper._process_siglum([para])
        # Assert
        assert siglum == "C"
        assert addendum == "F1–2"
        assert is_missing is False

    def test_returns_bracketed_siglum_with_addendum(self, helper):
        """Test that a bracketed siglum with a superscript addendum strips brackets and sets the missing flag."""
        # Arrange
        para = BeautifulSoup("<p><strong>[A<sup>c</sup>]</strong></p>", "html.parser").p
        # Act
        siglum, addendum, is_missing = helper._process_siglum([para])
        # Assert
        assert siglum == "A"
        assert addendum == "c"
        assert is_missing is True

    def test_falls_back_to_text_for_non_matching_para(self, helper):
        """Test that a non-siglum paragraph falls back to plain text with no addendum."""
        # Arrange
        para = BeautifulSoup("<p>Some plain text</p>", "html.parser").p
        # Act
        siglum, addendum, is_missing = helper._process_siglum([para])
        # Assert
        assert siglum == "Some plain text"
        assert addendum == ""
        assert is_missing is False


class TestProcessPhysDesc:
    """Tests for the _process_phys_desc helper function."""

    def _make_paras(self, extra_html: str = "") -> list:
        """Build a minimal paras list with 4 required entries plus optional extra paragraphs."""
        html = (
            "<p><strong>A</strong></p>"
            "<p>Typenbeschreibung</p>"
            "<p>CH-Basel, Paul Sacher Stiftung</p>"
            "<p>gut erhalten</p>" + extra_html
        )
        return BeautifulSoup(html, "html.parser").find_all("p")

    def test_appends_condition_from_paras_index_3(self, helper):
        """Test that the stripped text of paras[3] is appended to conditions."""
        paras = self._make_paras()
        with (
            patch.object(
                helper,
                "_process_writing_instruments",
                return_value={"main": "", "secondary": []},
            ),
            patch.object(helper, "_process_contents", return_value=[]),
        ):
            result = helper._process_phys_desc(paras, "source_A")
        assert result["conditions"] == ["gut erhalten"]

    def test_appends_empty_string_when_paras_index_3_is_empty(self, helper):
        """Test that an empty string is appended to conditions when paras[3] has no text."""
        html = (
            "<p><strong>A</strong></p>"
            "<p>Typenbeschreibung</p>"
            "<p>CH-Basel, Paul Sacher Stiftung</p>"
            "<p></p>"
        )
        paras = BeautifulSoup(html, "html.parser").find_all("p")
        with (
            patch.object(
                helper,
                "_process_writing_instruments",
                return_value={"main": "", "secondary": []},
            ),
            patch.object(helper, "_process_contents", return_value=[]),
        ):
            result = helper._process_phys_desc(paras, "source_A")
        assert result["conditions"] == [""]

    @pytest.mark.parametrize(
        "label, key, content",
        [
            ("Beschreibstoff: Notenpapier", "writingMaterialStrings", ["Notenpapier"]),
            ("Titel: Sonate", "titles", ["Sonate"]),
            ("Datierung: 1920", "dates", ["1920"]),
            ("Paginierung: 1–10", "paginations", ["1–10"]),
            ("Taktzahlen: 1–30", "measureNumbers", ["1–30"]),
            ("Besetzung: Klavier", "instrumentations", ["Klavier"]),
            ("Eintragungen: mit Bleistift", "annotations", ["mit Bleistift"]),
        ],
    )
    def test_sets_bulk_key_from_label_lookup(self, helper, label, key, content):
        """Test that each label-based key is populated from its matching paragraph."""
        paras = self._make_paras(f"<p>{label}</p>")
        with (
            patch.object(
                helper,
                "_process_writing_instruments",
                return_value={"main": "", "secondary": []},
            ),
            patch.object(helper, "_process_contents", return_value=[]),
        ):
            result = helper._process_phys_desc(paras, "source_A")
        assert result[key] == content

    def test_preserves_default_writing_instruments_when_schreibstoff_absent(
        self, helper
    ):
        """Test that writingInstruments keeps the default when no Schreibstoff paragraph is found."""
        paras = self._make_paras()
        with patch.object(helper, "_process_contents", return_value=[]):
            result = helper._process_phys_desc(paras, "source_A")
        assert result["writingInstruments"] == {"main": "", "secondary": []}

    def test_delegates_writing_instruments_to_helper(self, helper):
        """Test that _process_writing_instruments is triggered with the Schreibstoff content."""
        paras = self._make_paras("<p>Schreibstoff: Bleistift</p>")
        sentinel = {"main": "Bleistift", "secondary": []}
        with (
            patch.object(
                helper, "_process_writing_instruments", return_value=sentinel
            ) as mock_wi,
            patch.object(helper, "_process_contents", return_value=[]),
        ):
            result = helper._process_phys_desc(paras, "source_A")
        mock_wi.assert_called_once_with("Bleistift")
        assert result["writingInstruments"] == sentinel

    def test_delegates_contents_to_process_contents(self, helper):
        """Test that _process_contents is triggered with paras and source_id, and its result is stored."""
        paras = self._make_paras()
        sentinel = [{"item": "M 34 Sk1", "folios": []}]
        with (
            patch.object(
                helper,
                "_process_writing_instruments",
                return_value={"main": "", "secondary": []},
            ),
            patch.object(
                helper, "_process_contents", return_value=sentinel
            ) as mock_contents,
        ):
            result = helper._process_phys_desc(paras, "source_A")
        mock_contents.assert_called_once_with(paras, "source_A")
        assert result["contents"] == sentinel


class TestProcessWritingInstruments:
    """Tests for the _process_writing_instruments helper function."""

    def test_returns_default_when_input_is_none(self, helper):
        """Test that the default empty dict is returned when input is None."""
        result = helper._process_writing_instruments(None)
        assert result == {"main": "", "secondary": []}

    def test_returns_main_only_when_no_semicolon(self, helper):
        """Test that only main is set when there is no semicolon in the input."""
        result = helper._process_writing_instruments("Bleistift")
        assert result["main"] == "Bleistift"
        assert result["secondary"] == []

    def test_strips_trailing_full_stop_from_main(self, helper):
        """Test that a trailing full stop is stripped from the main instrument."""
        result = helper._process_writing_instruments("Bleistift.")
        assert result["main"] == "Bleistift"
        assert result["secondary"] == []

    def test_returns_main_and_single_secondary(self, helper):
        """Test that main and a single secondary instrument are extracted."""
        result = helper._process_writing_instruments("Bleistift; roter Buntstift")
        assert result["main"] == "Bleistift"
        assert result["secondary"] == ["roter Buntstift"]

    def test_strips_trailing_full_stop_from_secondary(self, helper):
        """Test that a trailing full stop is stripped from secondary instruments."""
        result = helper._process_writing_instruments("Bleistift; roter Buntstift.")
        assert result["main"] == "Bleistift"
        assert result["secondary"] == ["roter Buntstift"]

    def test_returns_main_and_multiple_secondaries(self, helper):
        """Test that multiple secondary instruments separated by commas are extracted."""
        result = helper._process_writing_instruments(
            "Bleistift; roter Buntstift, blaue Tinte"
        )
        assert result["main"] == "Bleistift"
        assert result["secondary"] == ["roter Buntstift", "blaue Tinte"]

    def test_strips_trailing_full_stop_from_multiple_secondaries(self, helper):
        """Test that trailing full stops are stripped from each secondary instrument."""
        result = helper._process_writing_instruments(
            "Bleistift; roter Buntstift, blaue Tinte."
        )
        assert result["main"] == "Bleistift"
        assert result["secondary"] == ["roter Buntstift", "blaue Tinte"]

    def test_strips_whitespace_from_main(self, helper):
        """Test that surrounding whitespace is stripped from the main instrument."""
        result = helper._process_writing_instruments("  Bleistift  ")
        assert result["main"] == "Bleistift"
        assert result["secondary"] == []

    def test_strips_whitespace_from_secondary_instruments(self, helper):
        """Test that surrounding whitespace is stripped from secondary instruments."""
        result = helper._process_writing_instruments("Bleistift;  Rotstift ,  Tinte ")
        assert result["main"] == "Bleistift"
        assert result["secondary"] == ["Rotstift", "Tinte"]


class TestProcessContents:
    """Tests for the _process_contents helper function."""

    def test_returns_empty_list_when_no_contents_found(self, helper):
        """Test that an empty list is returned when contents_start_index is -1."""
        para = BeautifulSoup("<p>no content label</p>", "html.parser").p
        with patch.object(IndexUtils, "find_contents_indices", return_value=(-1, 0)):
            result = helper._process_contents([para], "source_A")
        assert result == []

    def test_prints_warning_when_no_contents_found(self, helper, capsys):
        """Test that a warning is printed when contents_start_index is -1."""
        para = BeautifulSoup("<p>no content label</p>", "html.parser").p
        with patch.object(IndexUtils, "find_contents_indices", return_value=(-1, 0)):
            helper._process_contents([para], "source_A")
        captured = capsys.readouterr()
        assert "No content found for source_A" in captured.out

    def test_does_not_call_process_items_when_contents_not_found(self, helper):
        """Test that _process_items is not called when contents_start_index is -1."""
        para = BeautifulSoup("<p>no content label</p>", "html.parser").p
        with (
            patch.object(IndexUtils, "find_contents_indices", return_value=(-1, 0)),
            patch.object(helper, "_process_items") as mock_items,
        ):
            helper._process_contents([para], "source_A")
        mock_items.assert_not_called()

    def test_returns_result_from_process_items(self, helper):
        """Test that the return value from _process_items is returned."""
        soup = BeautifulSoup(
            "<p>Inhalt:</p><p>item</p><p>Textkritischer Kommentar:</p>",
            "html.parser",
        )
        paras = soup.find_all("p")
        sentinel = [{"item": "M 34 Sk1", "folios": []}]
        with (
            patch.object(IndexUtils, "find_contents_indices", return_value=(0, 2)),
            patch.object(helper, "_process_items", return_value=sentinel),
        ):
            result = helper._process_contents(paras, "source_A")
        assert result == sentinel

    def test_calls_process_items_with_slice_between_indices(self, helper):
        """Test that _process_items is called with paras[content+1:comments]."""
        soup = BeautifulSoup(
            "<p>Inhalt:</p><p><strong>M 34 Sk1</strong></p><p><strong>M* 414 Sk2</strong></p><p>Textkritischer Kommentar:</p>",
            "html.parser",
        )
        paras = soup.find_all("p")
        with (
            patch.object(IndexUtils, "find_contents_indices", return_value=(0, 3)),
            patch.object(helper, "_process_items", return_value=[]) as mock_items,
        ):
            helper._process_contents(paras, "source_A")
        mock_items.assert_called_once_with(paras[1:3])

    def test_delegates_index_search_to_find_contents_indices(self, helper):
        """Test that IndexUtils.find_contents_indices is called with the paragraphs list."""
        para = BeautifulSoup("<p>Inhalt:</p>", "html.parser").p
        with (
            patch.object(
                IndexUtils, "find_contents_indices", return_value=(0, 0)
            ) as mock_indices,
            patch.object(helper, "_process_items", return_value=[]),
        ):
            helper._process_contents([para], "source_A")
        mock_indices.assert_called_once_with([para])


class TestProcessItems:
    """Tests for the _process_items helper function."""

    def test_returns_empty_list_for_empty_input(self, helper):
        """Test that an empty list is returned when no paragraphs are given."""
        assert helper._process_items([]) == []

    def test_skips_tab_prefixed_paragraphs(self, helper):
        """Test that paragraphs starting with a tab are skipped."""
        para = BeautifulSoup("<p>\tBl. 1r\tsome description.</p>", "html.parser").p
        assert helper._process_items([para]) == []

    def test_skips_folio_str_paragraphs(self, helper):
        """Test that paragraphs starting with FOLIO_STR ('Bl.') are skipped."""
        para = BeautifulSoup("<p>Bl. 1r\tsome description.</p>", "html.parser").p
        assert helper._process_items([para]) == []

    def test_skips_page_str_paragraphs(self, helper):
        """Test that paragraphs starting with PAGE_STR ('S.') are skipped."""
        para = BeautifulSoup("<p>S. 12\tsome description.</p>", "html.parser").p
        assert helper._process_items([para]) == []

    def test_appends_item_for_non_skipped_paragraph(self, helper):
        """Test that a non-skipped paragraph results in one item being appended to the result."""
        soup = BeautifulSoup(
            "<div><p><strong>M 34 Sk1 </strong>(Skizze zu Studienkomposition):</p></div>",
            "html.parser",
        )
        para = soup.find("p")
        stub = {"item": "", "itemLinkTo": {}, "itemDescription": "", "folios": []}
        with (
            patch.object(helper, "_process_item", return_value=stub),
            patch.object(helper, "_find_siblings", return_value=[]),
            patch.object(helper, "_process_folios", return_value=[]),
        ):
            result = helper._process_items([para])
        assert len(result) == 1

    def test_triggers_process_item_for_each_non_skipped_paragraph(self, helper):
        """Test that _process_item is triggered once per non-skipped paragraph."""
        soup = BeautifulSoup(
            "<div><p><strong>M 34 Sk1 </strong>(Skizze zu Studienkomposition):</p><p>\tBl. 1r\tdesc.</p><p><strong>M* 414 Sk3 </strong>(Adagio):</p></div>",
            "html.parser",
        )
        paras = soup.find_all("p")
        stub = {"item": "", "itemLinkTo": {}, "itemDescription": "", "folios": []}
        with (
            patch.object(helper, "_process_item", return_value=stub) as mock_item,
            patch.object(helper, "_find_siblings", return_value=[]),
            patch.object(helper, "_process_folios", return_value=[]),
        ):
            helper._process_items(paras)
        assert mock_item.call_count == 2

    def test_triggers_find_siblings_for_each_item(self, helper):
        """Test that _find_siblings is triggered for each non-skipped paragraph."""
        soup = BeautifulSoup(
            "<div><p><strong>M 34 Sk1 </strong>(Skizze zu Studienkomposition):</p></div>",
            "html.parser",
        )
        para = soup.find("p")
        stub = {"item": "", "itemLinkTo": {}, "itemDescription": "", "folios": []}
        with (
            patch.object(helper, "_process_item", return_value=stub),
            patch.object(helper, "_find_siblings", return_value=[]) as mock_siblings,
            patch.object(helper, "_process_folios", return_value=[]),
        ):
            helper._process_items([para])
        mock_siblings.assert_called_once()

    def test_triggers_process_folios_with_sibling_paras(self, helper):
        """Test that _process_folios is triggered with the sibling paragraphs found."""
        soup = BeautifulSoup(
            "<div><p><strong>M 34 Sk1 </strong>(Skizze zu Studienkomposition):</p></div>",
            "html.parser",
        )
        para = soup.find("p")
        stub = {"item": "", "itemLinkTo": {}, "itemDescription": "", "folios": []}
        sentinel = [object()]
        with (
            patch.object(helper, "_process_item", return_value=stub),
            patch.object(helper, "_find_siblings", return_value=sentinel),
            patch.object(helper, "_process_folios", return_value=[]) as mock_folios,
        ):
            helper._process_items([para])
        mock_folios.assert_called_once_with(sentinel)

    def test_sets_folios_on_item_from_process_folios_result(self, helper):
        """Test that the folios returned by _process_folios are assigned to the item."""
        soup = BeautifulSoup(
            "<div><p><strong>M 34 Sk1 </strong>(Skizze zu Studienkomposition):</p></div>",
            "html.parser",
        )
        para = soup.find("p")
        stub = {"item": "", "itemLinkTo": {}, "itemDescription": "", "folios": []}
        folio_stub = [
            {
                "folio": "1r",
                "folioLinkTo": "",
                "folioDescription": "",
                "systemGroups": [],
            }
        ]
        with (
            patch.object(helper, "_process_item", return_value=stub),
            patch.object(helper, "_find_siblings", return_value=[]),
            patch.object(helper, "_process_folios", return_value=folio_stub),
        ):
            result = helper._process_items([para])
        assert result[0]["folios"] == folio_stub


class TestProcessItem:
    """Tests for the _process_item helper function."""

    def test_process_item_uses_compact_sheet_id_for_m_number(self, helper):
        """Test that 'M 34' gets normalized in sheetId."""
        # Arrange
        para = BeautifulSoup(
            "<p><strong>M 34 Sk1 </strong>(Skizze zu Studienkomposition):</p>",
            "html.parser",
        ).p

        # Act
        item = helper._process_item(para)

        # Assert
        assert item["item"] == "M 34 Sk1"
        assert item["itemLinkTo"]["sheetId"] == "M34_Sk1"
        assert item["itemLinkTo"]["complexId"] == "m34"
        assert item["itemDescription"] == "(Skizze zu Studienkomposition)"

    def test_process_item_handles_starred_siglum_with_space(self, helper):
        """Test that 'M* 414' gets normalized in sheetId/complexId."""
        # Arrange
        para = BeautifulSoup(
            "<p><strong>M* 414 Sk1 </strong>(Skizze zu Studienkomposition):</p>",
            "html.parser",
        ).p

        # Act
        item = helper._process_item(para)

        # Assert
        assert item["item"] == "M* 414 Sk1"
        assert item["itemLinkTo"]["sheetId"] == "Mx414_Sk1"
        assert item["itemLinkTo"]["complexId"] == "mx414"
        assert item["itemDescription"] == "(Skizze zu Studienkomposition)"

    def test_process_item_triggers_process_item_link_to_for_m_sigle(self, helper):
        """Test that _process_item_link_to is triggered with the item label for M/M* paragraphs."""
        # Arrange
        para = BeautifulSoup(
            "<p><strong>M 34 Sk1 </strong>(Skizze zu Studienkomposition):</p>",
            "html.parser",
        ).p

        # Act
        with patch.object(
            helper, "_process_item_link_to", return_value={}
        ) as mock_build:
            helper._process_item(para)

        # Assert
        mock_build.assert_called_once_with("M 34 Sk1")

    def test_strong_tag_without_m_sigle_returns_default_item(self, helper):
        """Test that a strong tag not starting with M/M* sigle returns a default item."""
        # Arrange
        para = BeautifulSoup(
            "<p><strong>K 23</strong> Skizze</p>",
            "html.parser",
        ).p

        # Act
        item = helper._process_item(para)

        # Assert
        assert item["item"] == ""
        assert item["itemLinkTo"] == {}
        assert item["itemDescription"] == ""

    def test_strong_tag_without_m_sigle_prints_warning(self, helper, capsys):
        """Test that a warning is printed when a strong tag is found without M/M* sigle."""
        # Arrange
        para = BeautifulSoup(
            "<p><strong>K 23</strong> Skizze</p>",
            "html.parser",
        ).p

        # Act
        helper._process_item(para)

        # Assert
        captured = capsys.readouterr()
        assert "--- Potential error? Strong tag found in para:" in captured.out

    def test_no_strong_tag_sets_item_description_only(self, helper):
        """Test that a plain paragraph without a strong tag sets only itemDescription."""
        # Arrange
        para = BeautifulSoup(
            "<p>Allegro moderato:</p>",
            "html.parser",
        ).p

        # Act
        item = helper._process_item(para)

        # Assert
        assert item["item"] == ""
        assert item["itemLinkTo"] == {}
        assert item["itemDescription"] == "Allegro moderato"


class TestProcessItemLinkTo:
    """Tests for the _process_item_link_to helper function."""

    def test_plain_m_label(self, helper):
        """Test that a plain 'M 34 Sk1' label produces the correct sheetId and complexId."""
        assert helper._process_item_link_to("M 34 Sk1") == {
            "complexId": "m34",
            "sheetId": "M34_Sk1",
        }

    def test_starred_m_label(self, helper):
        """Test that 'M* 414 Sk1' replaces '*' with 'x' in IDs."""
        assert helper._process_item_link_to("M* 414 Sk1") == {
            "complexId": "mx414",
            "sheetId": "Mx414_Sk1",
        }

    def test_dot_in_label_becomes_underscore(self, helper):
        """Test that a full stop in the label is replaced with an underscore in sheetId."""
        assert helper._process_item_link_to("M 34 Sk1.2") == {
            "complexId": "m34",
            "sheetId": "M34_Sk1_2",
        }

    def test_slash_in_label_uses_rowtable_sheet_id(self, helper):
        """Test that a slash in the label sets sheetId to ROWTABLE_SHEET_ID."""
        assert helper._process_item_link_to(
            "M 286 / M 287 RT (Reihentabelle op. 19)"
        ) == {
            "complexId": "m286",
            "sheetId": "SkRT",
        }

    def test_complex_id_is_always_lowercase(self, helper):
        """Test that complexId is always lowercase."""
        result1 = helper._process_item_link_to("M 34 Sk1")
        result2 = helper._process_item_link_to("M* 414 Sk1")
        assert result1["complexId"] == result1["complexId"].lower()
        assert result2["complexId"] == result2["complexId"].lower()


class TestFindSiblings:
    """Tests for the _find_siblings helper function."""

    def test_returns_empty_list_when_sibling_has_strong_tag(self, helper):
        """Test that recursion stops immediately and nothing is added when sibling has a strong tag."""
        soup = BeautifulSoup(
            "<div><p><strong>M 34 Sk1</strong></p><p>next para</p></div>",
            "html.parser",
        )
        paras = soup.find_all("p")
        result = helper._find_siblings(paras[0], [])
        assert result == []

    def test_includes_sibling_ending_with_period_and_stops(self, helper):
        """Test that a sibling ending with a period is included and recursion stops."""
        soup = BeautifulSoup(
            "<div><p>Bl. 1r\tSystem 1: T. 1–3.</p><p>next para</p></div>",
            "html.parser",
        )
        paras = soup.find_all("p")
        result = helper._find_siblings(paras[0], [])
        assert len(result) == 1
        assert result[0] is paras[0]

    def test_collects_sibling_without_period_then_stops_at_strong(self, helper):
        """Test that a sibling without a period is included, then recursion stops at a strong tag."""
        soup = BeautifulSoup(
            "<div><p>Bl. 1r\tSystem 1: T. 1–3</p><p><strong>M 34 Sk1</strong></p></div>",
            "html.parser",
        )
        paras = soup.find_all("p")
        result = helper._find_siblings(paras[0], [])
        assert len(result) == 1
        assert result[0] is paras[0]

    def test_collects_multiple_siblings_until_period(self, helper):
        """Test that multiple siblings are collected until one ends with a period."""
        soup = BeautifulSoup(
            "<div>"
            "<p>Bl. 1r\tSystem 1: T. 1–3</p>"
            "<p>\tSystem 2: T. 4–6</p>"
            "<p>\tSystem 3: T. 7–9.</p>"
            "<p>next para</p>"
            "</div>",
            "html.parser",
        )
        paras = soup.find_all("p")
        result = helper._find_siblings(paras[0], [])
        assert len(result) == 3
        assert result[0] is paras[0]
        assert result[1] is paras[1]
        assert result[2] is paras[2]

    def test_appends_to_existing_paras_list(self, helper):
        """Test that the method appends to an already-populated paras list."""
        soup = BeautifulSoup(
            "<div><p>Bl. 1r\tSystem 1: T. 1–3.</p><p>next para</p></div>",
            "html.parser",
        )
        existing = BeautifulSoup("<p>already here</p>", "html.parser").p
        paras = soup.find_all("p")
        result = helper._find_siblings(paras[0], [existing])
        assert len(result) == 2
        assert result[0] is existing
        assert result[1] is paras[0]


class TestProcessFolios:
    """Tests for the _process_folios helper function."""

    def test_returns_empty_list_for_empty_input(self, helper):
        """Test that an empty list is returned when no sibling paragraphs are given."""
        assert helper._process_folios([]) == []

    def test_appends_folio_for_folio_str_paragraph(self, helper):
        """Test that a folio entry is appended for a FOLIO_STR ('Bl.') paragraph."""
        para = BeautifulSoup("<p>Bl. 1r\tsome description.</p>", "html.parser").p
        result = helper._process_folios([para])
        assert len(result) == 1
        assert result[0]["folio"] == "1r"

    def test_appends_folio_for_page_str_paragraph(self, helper):
        """Test that a folio entry with isPage=True is appended for a PAGE_STR ('S.') paragraph."""
        para = BeautifulSoup("<p>S. 12\tsome description.</p>", "html.parser").p
        result = helper._process_folios([para])
        assert len(result) == 1
        assert result[0]["folio"] == "12"
        assert result[0]["isPage"] is True

    def test_appends_system_group_to_last_folio_for_system_paragraph(self, helper):
        """Test that a system-only paragraph appends a system group to the last folio's systemGroups."""
        soup = BeautifulSoup(
            "<div><p>Bl. 1r\tSystem 1: T. 1–3.</p><p>\tSystem 2: T. 4–6.</p></div>",
            "html.parser",
        )
        paras = soup.find_all("p")
        result = helper._process_folios(paras)
        assert len(result) == 1
        assert len(result[0]["systemGroups"]) == 2

    def test_returns_multiple_folios_for_multiple_folio_paragraphs(self, helper):
        """Test that multiple folio paragraphs produce multiple folio entries in the result."""
        para1 = BeautifulSoup("<p>Bl. 1r\tsome description.</p>", "html.parser").p
        para2 = BeautifulSoup("<p>Bl. 2v\tother description.</p>", "html.parser").p
        result = helper._process_folios([para1, para2])
        assert len(result) == 2
        assert result[0]["folio"] == "1r"
        assert result[1]["folio"] == "2v"

    def test_triggers_process_folio_with_page_found_false_for_folio_str(self, helper):
        """Test that _process_folio is triggered with page_found=False for a FOLIO_STR paragraph."""
        para = BeautifulSoup("<p>Bl. 1r\tsome description.</p>", "html.parser").p
        stub = {
            "folio": "1r",
            "folioLinkTo": "",
            "folioDescription": "",
            "systemGroups": [],
        }
        with patch.object(helper, "_process_folio", return_value=stub) as mock_folio:
            helper._process_folios([para])
        mock_folio.assert_called_once()
        _, _, page_found = mock_folio.call_args.args
        assert page_found is False

    def test_triggers_process_folio_with_page_found_true_for_page_str(self, helper):
        """Test that _process_folio is triggered with page_found=True for a PAGE_STR paragraph."""
        para = BeautifulSoup("<p>S. 12\tsome description.</p>", "html.parser").p
        stub = {
            "folio": "12",
            "folioLinkTo": "",
            "folioDescription": "",
            "systemGroups": [],
        }
        with patch.object(helper, "_process_folio", return_value=stub) as mock_folio:
            helper._process_folios([para])
        mock_folio.assert_called_once()
        _, _, page_found = mock_folio.call_args.args
        assert page_found is True

    def test_falls_back_to_tab_split_when_space_tab_split_not_two_parts(self, helper):
        """Test that the tab-only delimiter is used when space+tab split does not yield exactly two parts."""
        para = BeautifulSoup("<p>Bl. 1r\tsome description.</p>", "html.parser").p
        stub = {
            "folio": "1r",
            "folioLinkTo": "",
            "folioDescription": "",
            "systemGroups": [],
        }
        with patch.object(helper, "_process_folio", return_value=stub) as mock_folio:
            helper._process_folios([para])
        _, stripped_para_text, _ = mock_folio.call_args.args
        assert stripped_para_text == ["Bl. 1r", "some description."]

    def test_system_paragraph_without_prior_folio_prints_warning(self, helper, capsys):
        """Test that a system-only paragraph with no preceding folio prints a warning and is skipped."""
        para = BeautifulSoup("<p>\tSystem 1: T. 1–3.</p>", "html.parser").p
        result = helper._process_folios([para])
        assert result == []
        captured = capsys.readouterr()
        assert "--- Potential error? Unexpected paragraph in folios:" in captured.out

    def test_unexpected_paragraph_after_folio_prints_warning(self, helper, capsys):
        """Test that a paragraph that is neither folio/page nor system prints a warning."""
        para_folio = BeautifulSoup("<p>Bl. 1r\tsome description.</p>", "html.parser").p
        para_unexpected = BeautifulSoup("<p>unexpected content</p>", "html.parser").p
        helper._process_folios([para_folio, para_unexpected])
        captured = capsys.readouterr()
        assert "--- Potential error? Unexpected paragraph in folios:" in captured.out


class TestProcessFolio:
    """Tests for the _process_folio helper function."""

    def test_extracts_folio_label_from_folio_str(self, helper):
        """Test that the folio label is extracted from a 'Bl.' paragraph."""
        para = BeautifulSoup("<p>Bl. 1r\tsome description.</p>", "html.parser").p
        stripped = ["Bl. 1r", "some description."]
        folio = helper._process_folio(para, stripped, page_found=False)
        assert folio["folio"] == "1r"

    def test_no_is_page_flag_when_not_page(self, helper):
        """Test that 'isPage' is not present when page_found is False."""
        para = BeautifulSoup("<p>Bl. 1r\tsome description.</p>", "html.parser").p
        stripped = ["Bl. 1r", "some description."]
        folio = helper._process_folio(para, stripped, page_found=False)
        assert "isPage" not in folio

    def test_extracts_folio_label_from_page_str(self, helper):
        """Test that the folio label is extracted from a 'S.' paragraph."""
        para = BeautifulSoup("<p>S. 12\tsome description.</p>", "html.parser").p
        stripped = ["S. 12", "some description."]
        folio = helper._process_folio(para, stripped, page_found=True)
        assert folio["folio"] == "12"

    def test_inserts_is_page_flag_when_page_found(self, helper):
        """Test that 'isPage' is inserted at position 1 when page_found is True."""
        para = BeautifulSoup("<p>S. 12\tsome description.</p>", "html.parser").p
        stripped = ["S. 12", "some description."]
        folio = helper._process_folio(para, stripped, page_found=True)
        keys = list(folio.keys())
        assert "isPage" in keys
        assert keys.index("isPage") == 1
        assert folio["isPage"] is True

    def test_triggers_process_folio_label_with_folio_part(self, helper):
        """Test that _process_folio_label is triggered with the folio part of stripped_para_text."""
        para = BeautifulSoup("<p>Bl. 2v\tsome description.</p>", "html.parser").p
        stripped = ["Bl. 2v", "some description."]
        with patch.object(
            helper, "_process_folio_label", return_value="2v"
        ) as mock_label:
            helper._process_folio(para, stripped, page_found=False)
        mock_label.assert_called_once_with("Bl. 2v")

    def test_sets_folio_description_when_no_system_str(self, helper):
        """Test that folioDescription is set when no 'System' string in the paragraph."""
        para = BeautifulSoup("<p>Bl. 1r\tsome description.</p>", "html.parser").p
        stripped = ["Bl. 1r", "some description."]
        folio = helper._process_folio(para, stripped, page_found=False)
        assert folio["folioDescription"] == "some description."
        assert folio["systemGroups"] == []

    def test_sets_system_groups_when_system_str_present(self, helper):
        """Test that systemGroups is set when 'System' appears in the paragraph."""
        para = BeautifulSoup("<p>Bl. 1r\tSystem 1: T. 1–3.</p>", "html.parser").p
        stripped = ["Bl. 1r", "System 1: T. 1–3."]
        folio = helper._process_folio(para, stripped, page_found=False)
        assert len(folio["systemGroups"]) == 1
        assert folio["folioDescription"] == ""

    def test_triggers_process_system_group_when_system_str_present(self, helper):
        """Test that _process_system_group is triggered when 'System' appears in the paragraph."""
        para = BeautifulSoup("<p>Bl. 1r\tSystem 1: T. 1–3.</p>", "html.parser").p
        stripped = ["Bl. 1r", "System 1: T. 1–3."]
        with patch.object(
            helper, "_process_system_group", return_value=[]
        ) as mock_group:
            helper._process_folio(para, stripped, page_found=False)
        mock_group.assert_called_once_with(stripped)


class TestProcessFolioLabel:
    """Tests for the _process_folio_label helper function."""

    def test_returns_folio_label_for_folio_str(self, helper):
        """Test that the folio label is extracted for a FOLIO_STR ('Bl.') input."""
        assert helper._process_folio_label("Bl. 1r") == "1r"

    def test_returns_folio_label_for_page_str(self, helper):
        """Test that the folio label is extracted for a PAGE_STR ('S.') input."""
        assert helper._process_folio_label("S. 12") == "12"

    def test_folio_str_takes_priority_over_page_str(self, helper):
        """Test that FOLIO_STR is used when both markers are present."""
        assert helper._process_folio_label("Bl. 3r S. 12") == "3r S. 12"

    def test_returns_empty_string_when_no_marker(self, helper):
        """Test that an empty string is returned when neither marker is present."""
        assert helper._process_folio_label("System 1: T. 1–3") == ""

    def test_strips_non_breaking_space_after_folio_str(self, helper):
        """Test that a non-breaking space after the folio marker is stripped."""
        assert helper._process_folio_label("Bl.\xa01r") == "1r"

    def test_strips_non_breaking_space_after_page_str(self, helper):
        """Test that a non-breaking space after the page marker is stripped."""
        assert helper._process_folio_label("S.\xa07") == "7"

    def test_triggers_strip_label_from_text_with_folio_str(self, helper):
        """Test that strip_label_from_text is triggered with FOLIO_STR when FOLIO_STR is present."""
        with patch.object(
            StrippingUtils, "strip_label_from_text", return_value="1r"
        ) as mock_strip:
            helper._process_folio_label("Bl. 1r")
            mock_strip.assert_called_once_with("Bl. 1r", "Bl.")

    def test_triggers_strip_label_from_text_with_page_str(self, helper):
        """Test that strip_label_from_text is triggered with PAGE_STR when PAGE_STR is present."""
        with patch.object(
            StrippingUtils, "strip_label_from_text", return_value="12"
        ) as mock_strip:
            helper._process_folio_label("S. 12")
            mock_strip.assert_called_once_with("S. 12", "S.")


class TestProcessSystemGroup:
    """Tests for the _process_system_group helper function."""

    def test_returns_empty_list_for_empty_input(self, helper):
        """Test that an empty list is returned for empty input."""
        assert helper._process_system_group([]) == []

    def test_returns_empty_list_when_no_system_str_in_any_text(self, helper):
        """Test that an empty list is returned when no text contains 'System'."""
        result = helper._process_system_group(["T. 1–3", "Gg (1)"])
        assert result == []

    def test_skips_folio_str_entries(self, helper):
        """Test that entries containing FOLIO_STR ('Bl.') are skipped."""
        result = helper._process_system_group(["Bl. 1r", "System 1: T. 1–3"])
        assert len(result) == 1
        assert result[0]["system"] == "1"

    def test_skips_page_str_entries(self, helper):
        """Test that entries containing PAGE_STR ('S.') are skipped."""
        result = helper._process_system_group(["S. 1", "System 12: T. 4"])
        assert len(result) == 1
        assert result[0]["system"] == "12"

    def test_returns_single_system_for_single_matching_entry(self, helper):
        """Test that a single system is returned for a single matching entry."""
        result = helper._process_system_group(["System 1: T. 1–3"])
        assert len(result) == 1
        assert result[0]["system"] == "1"
        assert result[0]["measure"] == "1–3"

    def test_returns_multiple_systems_for_multiple_matching_entries(self, helper):
        """Test that multiple systems are returned for multiple matching entries."""
        result = helper._process_system_group(["System 1: T. 1–3", "System 2: Gg (1)"])
        assert len(result) == 2
        assert result[0]["system"] == "1"
        assert result[0]["measure"] == "1–3"
        assert result[1]["system"] == "2"
        assert result[1]["row"]["rowType"] == "G"

    def test_excludes_entries_for_which_process_system_returns_none(self, helper):
        """Test that entries for which _process_system returns None are excluded."""
        result = helper._process_system_group(["System 1", "not a system", "System 2"])
        assert len(result) == 2

    def test_triggers_process_system_for_each_non_skipped_entry(self, helper):
        """Test that _process_system is triggered once per non-skipped entry."""
        texts = ["Bl. 1r", "System 1: T. 1", "S. 2", "System 2: Gg (1)"]
        with patch.object(
            helper, "_process_system", return_value=None
        ) as mock_system_group:
            helper._process_system_group(texts)
            assert mock_system_group.call_count == 2
            mock_system_group.assert_any_call("System 1: T. 1")
            mock_system_group.assert_any_call("System 2: Gg (1)")


class TestProcessSystem:
    """Tests for the _process_system helper function."""

    def test_returns_none_when_system_str_not_in_text(self, helper):
        """Test that None is returned when 'System' is not present in the text."""
        assert helper._process_system("T. 1–3") is None

    def test_returns_none_for_empty_string(self, helper):
        """Test that None is returned for an empty string."""
        assert helper._process_system("") is None

    def test_returns_system_without_measure_or_row_when_no_colon(self, helper):
        """Test that only the system number is set when there is no colon separator."""
        system = helper._process_system("System 1")
        assert system["system"] == "1"
        assert system["measure"] == ""
        assert system.get("row") is None

    def test_returns_system_with_plain_numeral_range(self, helper):
        """Test that a plain numeral range like '16–17' is set as the system value."""
        system = helper._process_system("System 16–17")
        assert system["system"] == "16–17"
        assert system["measure"] == ""
        assert system.get("row") is None

    def test_returns_system_with_alphanumeric_range(self, helper):
        """Test that an alphanumeric range like '13b–17a' is set as the system value."""
        system = helper._process_system("System 13b–17a")
        assert system["system"] == "13b–17a"
        assert system["measure"] == ""
        assert system.get("row") is None

    def test_returns_system_with_measure_when_measure_str_present(self, helper):
        """Test that the measure is extracted when 'T.' follows the colon."""
        system = helper._process_system("System 2: T. 1–3")
        assert system["system"] == "2"
        assert system["measure"] == "1–3"
        assert system.get("row") is None

    def test_returns_system_with_row_when_row_pattern_present(self, helper):
        """Test that the row is extracted when a row pattern follows the colon."""
        system = helper._process_system("System 3: Gg (1)")
        assert system["system"] == "3"
        assert system["measure"] == ""
        assert system["row"]["rowType"] == "G"
        assert system["row"]["rowBase"] == "g"
        assert system["row"]["rowNumber"] == "1"

    def test_returns_system_without_row_when_second_part_matches_neither(self, helper):
        """Test that no 'row' key is added when the second part is neither a measure nor a row."""
        system = helper._process_system("System 16–17: some text")
        assert system["system"] == "16–17"
        assert system["measure"] == ""
        assert system.get("row") is None

    def test_system_number_is_stripped_of_system_str(self, helper):
        """Test that the 'System' prefix is removed from the system value."""
        system = helper._process_system("System 13b–17a: T. 5")
        assert "System" not in system["system"]
        assert system["system"] == "13b–17a"

    def test_returns_system_with_roman_numeral_row_number(self, helper):
        """Test that a row with a roman numeral row number is handled correctly."""
        system = helper._process_system("System 1: KUgis (XXXVIII)")
        assert system["system"] == "1"
        assert system["row"]["rowType"] == "KU"
        assert system["row"]["rowBase"] == "gis"
        assert system["row"]["rowNumber"] == "XXXVIII"

    def test_triggers_process_measure_and_not_process_row_when_measure_str_present(
        self, helper
    ):
        """Test that _process_measure is triggered and _process_row is not when 'T.' is present."""
        with (
            patch.object(
                helper, "_process_measure", return_value="1–3"
            ) as mock_measure,
            patch.object(helper, "_process_row") as mock_row,
        ):
            helper._process_system("System 1: T. 1–3")
            mock_measure.assert_called_once_with("T. 1–3")
            mock_row.assert_not_called()

    def test_triggers_process_row_and_not_process_measure_when_measure_str_absent(
        self, helper
    ):
        """Test that _process_row is triggered and _process_measure is not when 'T.' is absent."""
        with (
            patch.object(helper, "_process_row", return_value=None) as mock_row,
            patch.object(helper, "_process_measure") as mock_measure,
        ):
            helper._process_system("System 1: Gg (1)")
            mock_row.assert_called_once_with("Gg (1)")
            mock_measure.assert_not_called()

    def test_neither_sub_method_called_when_no_colon(self, helper):
        """Test that neither _process_measure nor _process_row is triggered when there's no colon."""
        with (
            patch.object(helper, "_process_measure") as mock_measure,
            patch.object(helper, "_process_row") as mock_row,
        ):
            helper._process_system("System 1")
            mock_measure.assert_not_called()
            mock_row.assert_not_called()

    def test_prints_warning_when_content_has_multiple_colons(self, helper, capsys):
        """Test that a warning is printed when the content contains more than one colon."""
        helper._process_system("System 1: T. 1: unexpected")
        captured = capsys.readouterr()
        assert "Potential error" in captured.out

    def test_no_warning_printed_for_single_colon(self, helper, capsys):
        """Test that no warning is printed for a normal single-colon input."""
        helper._process_system("System 1: T. 1–3")
        captured = capsys.readouterr()
        assert captured.out == ""


class TestProcessMeasure:
    """Tests for the _process_measure helper function."""

    def test_process_measure_returns_measure_label(self, helper):
        """Test that the measure string prefix and trailing punctuation are stripped."""
        assert helper._process_measure("T. 1–3.") == "1–3"

    def test_process_measure_strips_trailing_semicolon(self, helper):
        """Test that a trailing semicolon is stripped."""
        assert helper._process_measure("T. 4–6;") == "4–6"

    def test_process_measure_strips_whitespace(self, helper):
        """Test that leading and trailing whitespace is stripped."""
        assert helper._process_measure("T.  12 ") == "12"

    def test_process_measure_returns_empty_string_when_only_measure_str(self, helper):
        """Test that an empty string is returned when the text is only the measure string."""
        assert helper._process_measure("T.") == ""


class TestProcessRow:
    """Tests for the _process_row helper function."""

    def test_process_row_returns_single_letter_row_without_row_number(self, helper):
        """Test that a single-letter row without a row number is extracted correctly."""
        row = helper._process_row("Gc")
        assert row["rowType"] == "G"
        assert row["rowBase"] == "c"
        assert row["rowNumber"] == ""

    def test_process_row_returns_multi_letter_row_without_row_number(self, helper):
        """Test that a multi-letter row without a row number is extracted correctly."""
        row = helper._process_row("KUg")
        assert row["rowType"] == "KU"
        assert row["rowBase"] == "g"
        assert row["rowNumber"] == ""

    def test_process_row_returns_row_with_single_letter_base(self, helper):
        """Test that a row with a single-letter base is extracted correctly."""
        row = helper._process_row("Ua")
        assert row["rowType"] == "U"
        assert row["rowBase"] == "a"
        assert row["rowNumber"] == ""

    def test_process_row_returns_row_with_multi_letter_base(self, helper):
        """Test that a row with a multi-letter base is extracted correctly."""
        row = helper._process_row("KUgis")
        assert row["rowType"] == "KU"
        assert row["rowBase"] == "gis"
        assert row["rowNumber"] == ""

    def test_process_row_returns_row_with_integer_row_number(self, helper):
        """Test that a row with an integer row number is extracted correctly."""
        row = helper._process_row("Gg (1)")
        assert row["rowType"] == "G"
        assert row["rowBase"] == "g"
        assert row["rowNumber"] == "1"

    def test_process_row_returns_row_with_roman_numeral_row_number(self, helper):
        """Test that a row with a roman numeral row number is extracted correctly."""
        row = helper._process_row("KUgis (XXXVIII)")
        assert row["rowType"] == "KU"
        assert row["rowBase"] == "gis"
        assert row["rowNumber"] == "XXXVIII"

    def test_process_row_returns_none_when_pattern_does_not_match(self, helper):
        """Test that None is returned when the text does not match the row pattern."""
        assert helper._process_row("T. 1–3") is None

    def test_process_row_returns_none_for_empty_string(self, helper):
        """Test that None is returned for an empty string."""
        assert helper._process_row("") is None
