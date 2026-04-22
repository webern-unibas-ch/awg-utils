# pylint: disable=protected-access
"""Tests for sources_utils.py – folio and system processing."""

from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup

from utils.sources_utils import SourcesUtils
from utils.stripping_utils import StrippingUtils


@pytest.fixture(name="helper")
def fixture_helper():
    """Return an instance of SourcesUtils."""
    return SourcesUtils()


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
        """Test that a system-only paragraph appends a system group
        to the last folio's systemGroups."""
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

    def test_skips_folio_row_with_no_tab_delimiter(self, helper, capsys):
        """Test that a paragraph without a tab delimiter is skipped with a warning."""
        para = BeautifulSoup("<p>Bl. 1r</p>", "html.parser").p
        result = helper._process_folios([para])
        assert result == []
        assert (
            "--- Potential error? Paragraph has fewer than 2 parts, skipped:"
            in capsys.readouterr().out
        )

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
        """Test that the tab-only delimiter is used
        when space+tab split does not yield exactly two parts."""
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
        """Test that a system-only paragraph with no preceding folio
        prints a warning and is skipped."""
        para = BeautifulSoup("<p>\tSystem 1: T. 1–3.</p>", "html.parser").p
        result = helper._process_folios([para])
        assert result == []
        captured = capsys.readouterr()
        assert "--- Potential error? Unexpected paragraph in folios:" in captured.out

    def test_unexpected_paragraph_after_folio_prints_warning(self, helper, capsys):
        """Test that a paragraph that is neither folio/page nor system prints a warning."""
        para_folio = BeautifulSoup("<p>Bl. 1r\tsome description.</p>", "html.parser").p
        para_unexpected = BeautifulSoup("<p>unexpected\tcontent</p>", "html.parser").p
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
        """Test that neither _process_measure nor _process_row is triggered
        when there's no colon."""
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
