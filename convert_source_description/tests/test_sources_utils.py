# pylint: disable=protected-access
"""Tests for sources_utils.py"""

from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup

from utils.index_utils import IndexUtils
from utils.sources_utils import SourcesUtils


@pytest.fixture(name="helper")
def fixture_helper():
    """Return an instance of SourcesUtils."""
    return SourcesUtils()


class TestCreateSourceList:
    """Tests for the create_source_list public method."""

    def _make_soup(self, *siglums: str) -> BeautifulSoup:
        """Build a minimal soup with one block of fixed paragraphs per siglum."""
        html = "".join(
            f"<p><strong>{siglum}</strong></p>"
            "<p>Typenbeschreibung</p>"
            "<p>CH-Basel, Paul Sacher Stiftung</p>"
            "<p>gut erhalten</p>"
            for siglum in siglums
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

    def test_does_not_append_duplicate_source(self, helper):
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
        """Test that physDesc is the return value of _process_phys_desc
        called with (paras, source_id)."""
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
        """Test that a bracketed siglum with a superscript addendum
        strips brackets and sets the missing flag."""
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
        """Test that writingInstruments keeps the default
        when no Schreibstoff paragraph is found."""
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
        """Test that _process_contents is triggered with paras and source_id,
        and its result is stored."""
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
            "<p>Inhalt:</p>"
            "<p><strong>M 34 Sk1</strong></p>"
            "<p><strong>M* 414 Sk2</strong></p>"
            "<p>Textkritischer Kommentar:</p>",
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
            "<div>"
            "<p><strong>M 34 Sk1 </strong>(Skizze zu Studienkomposition):</p>"
            "<p>\tBl. 1r\tdesc.</p>"
            "<p><strong>M* 414 Sk3 </strong>(Adagio):</p>"
            "</div>",
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
        """Test that recursion stops immediately and nothing is added
        when sibling has a strong tag."""
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
        """Test that a sibling without a period is included,
        then recursion stops at a strong tag."""
        soup = BeautifulSoup(
            "<div>"
            "<p>Bl. 1r\tSystem 1: T. 1–3</p>"
            "<p><strong>M 34 Sk1</strong></p>"
            "</div>",
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

    def test_returns_paras_unchanged_when_sibling_is_none(self, helper):
        """Test that paras is returned unchanged when the sibling is None (last element)."""
        result = helper._find_siblings(None, [])
        assert result == []

    def test_skips_navigable_string_and_collects_next_p_tag(self, helper):
        """Test that NavigableStrings (whitespace between tags) are skipped
        and the next <p> tag is still collected."""
        soup = BeautifulSoup(
            "<div>\n"
            "<p>Bl. 1r\tSystem 1: T. 1–3</p>\n"
            "<p>\tSystem 2: T. 4–6.</p>\n"
            "</div>",
            "html.parser",
        )
        paras = soup.find_all("p")
        result = helper._find_siblings(paras[0].next_sibling, [])
        assert len(result) == 1
        assert result[0] is paras[1]

    def test_returns_paras_unchanged_when_sibling_is_not_p_tag(self, helper):
        """Test that paras is returned unchanged when the next real sibling is not a <p> tag."""
        soup = BeautifulSoup(
            "<div><p>Bl. 1r\tSystem 1: T. 1–3</p><div>other</div></div>",
            "html.parser",
        )
        para = soup.find("p")
        result = helper._find_siblings(para.next_sibling, [])
        assert result == []
