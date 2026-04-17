# pylint: disable=protected-access
"""Tests for utils_helper.py"""

from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup

from utils.utils_helper import ConversionUtilsHelper


@pytest.fixture(name="helper")
def fixture_helper():
    """Return an instance of ConversionUtilsHelper."""
    return ConversionUtilsHelper()


class TestFindSiglumIndices:
    """Tests for the find_siglum_indices function."""

    def test_with_single_siglum(self, helper):
        """Test that a single siglum is found."""
        # Arrange
        para1 = BeautifulSoup("<p><strong>A</strong></p>", "html.parser").p
        para2 = BeautifulSoup("<p><strong>B</strong></p>", "html.parser").p
        para3 = BeautifulSoup("<p><strong>Z</strong></p>", "html.parser").p
        para4 = BeautifulSoup("<p><strong>D</strong> Text</p>", "html.parser").p
        para5 = BeautifulSoup("<p>E</p>", "html.parser").p
        paras = [para1, para2, para3, para4, para5]
        expected_indices = [0, 1, 2]
        # Act
        actual_indices = helper.find_siglum_indices(paras)
        # Assert
        assert actual_indices == expected_indices

    def test_with_multiple_siglums(self, helper):
        """Test that multiple siglums are found."""
        # Arrange
        para1 = BeautifulSoup("<p><strong>C</strong></p>", "html.parser").p
        para2 = BeautifulSoup("<p><strong>I</strong></p>", "html.parser").p
        para3 = BeautifulSoup("<p><strong>AB</strong></p>", "html.parser").p
        para4 = BeautifulSoup("<p><strong>E</strong>F</p>", "html.parser").p
        para5 = BeautifulSoup(
            "<p><strong>G</strong><strong>H</strong></p>", "html.parser"
        ).p
        paras = [para1, para2, para3, para4, para5]
        expected_indices = [0, 1]
        # Act
        actual_indices = helper.find_siglum_indices(paras)
        # Assert
        assert actual_indices == expected_indices

    def test_with_siglum_in_brackets(self, helper):
        """Test that a siglum in brackets (missing) is found."""
        # Arrange
        para1 = BeautifulSoup("<p><strong>[A]</strong></p>", "html.parser").p
        para2 = BeautifulSoup("<p><strong>[B]</strong></p>", "html.parser").p
        para3 = BeautifulSoup("<p><strong>[Z]</strong></p>", "html.parser").p
        para4 = BeautifulSoup("<p><strong>[D]</strong> Text</p>", "html.parser").p
        para5 = BeautifulSoup("<p>E</p>", "html.parser").p
        paras = [para1, para2, para3, para4, para5]
        expected_indices = [0, 1, 2]
        # Act
        actual_indices = helper.find_siglum_indices(paras)
        # Assert
        assert actual_indices == expected_indices

    def test_with_optional_additional_siglum(self, helper):
        """Test that an optional (superscripted) additional siglum is found."""
        # Arrange
        para1 = BeautifulSoup("<p><strong>A<sup>a</sup></strong></p>", "html.parser").p
        para2 = BeautifulSoup("<p><strong>B<sup>H</sup></strong></p>", "html.parser").p
        para3 = BeautifulSoup("<p><strong>C<sup>F1</sup></strong></p>", "html.parser").p
        para4 = BeautifulSoup(
            "<p><strong>C<sup>F1–2</sup></strong></p>", "html.parser"
        ).p
        para5 = BeautifulSoup("<p><strong>A<sup>aa</sup></strong></p>", "html.parser").p
        para6 = BeautifulSoup("<p><strong>AA</strong></p>", "html.parser").p
        para7 = BeautifulSoup("<p><strong>A</strong>a</p>", "html.parser").p
        para8 = BeautifulSoup("<p><strong>A</strong>A", "html.parser").p
        para9 = BeautifulSoup(
            "<p><strong>A</strong><strong>a</strong></p>", "html.parser"
        ).p
        paras = [para1, para2, para3, para4, para5, para6, para7, para8, para9]
        expected_indices = [0, 1, 2, 3]
        # Act
        actual_indices = helper.find_siglum_indices(paras)
        # Assert
        assert actual_indices == expected_indices

    def test_with_no_siglums(self, helper):
        """Test that no siglums are found."""
        # Arrange
        para1 = BeautifulSoup("<p>A</p>", "html.parser").p
        para2 = BeautifulSoup("<p>BB</p>", "html.parser").p
        para4 = BeautifulSoup("<p>C<strong></strong></p>", "html.parser").p
        para3 = BeautifulSoup("<p><strong></strong>D</p>", "html.parser").p
        para5 = BeautifulSoup("<p><strong></strong></p>", "html.parser").p
        paras = [para1, para2, para3, para4, para5]
        expected_indices = []
        # Act
        actual_indices = helper.find_siglum_indices(paras)
        # Assert
        assert actual_indices == expected_indices

    def test_in_fixture_paras(self, helper, sample_soup_paras):
        """Test that the correct indices are found in the fixture sample paras."""
        # Arrange
        expected_indices = [1, 16]
        # Act
        actual_indices = helper.find_siglum_indices(sample_soup_paras)
        # Assert
        assert actual_indices == expected_indices


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
        result = helper._process_writing_instruments("Bleistift; Rotstift")
        assert result["main"] == "Bleistift"
        assert result["secondary"] == ["Rotstift"]

    def test_strips_trailing_full_stop_from_secondary(self, helper):
        """Test that a trailing full stop is stripped from secondary instruments."""
        result = helper._process_writing_instruments("Bleistift; Rotstift.")
        assert result["main"] == "Bleistift"
        assert result["secondary"] == ["Rotstift"]

    def test_returns_main_and_multiple_secondaries(self, helper):
        """Test that multiple secondary instruments separated by commas are extracted."""
        result = helper._process_writing_instruments("Bleistift; Rotstift, Tinte")
        assert result["main"] == "Bleistift"
        assert result["secondary"] == ["Rotstift", "Tinte"]

    def test_strips_trailing_full_stop_from_multiple_secondaries(self, helper):
        """Test that trailing full stops are stripped from each secondary instrument."""
        result = helper._process_writing_instruments("Bleistift; Rotstift, Tinte.")
        assert result["main"] == "Bleistift"
        assert result["secondary"] == ["Rotstift", "Tinte"]

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


class TestGetItem:
    """Tests for the _get_item helper function."""

    def test_get_item_uses_compact_sheet_id_for_m_number(self, helper):
        """Test that 'M 34' gets normalized in sheetId."""
        # Arrange
        para = BeautifulSoup(
            "<p><strong>M 34 Sk1 </strong>(Skizze zu Studienkomposition):</p>",
            "html.parser",
        ).p

        # Act
        item = helper._get_item(para)

        # Assert
        assert item["item"] == "M 34 Sk1"
        assert item["itemLinkTo"]["sheetId"] == "M34_Sk1"
        assert item["itemLinkTo"]["complexId"] == "m34"
        assert item["itemDescription"] == "(Skizze zu Studienkomposition)"

    def test_get_item_handles_starred_siglum_with_space(self, helper):
        """Test that 'M* 414' gets normalized in sheetId/complexId."""
        # Arrange
        para = BeautifulSoup(
            "<p><strong>M* 414 Sk1 </strong>(Skizze zu Studienkomposition):</p>",
            "html.parser",
        ).p

        # Act
        item = helper._get_item(para)

        # Assert
        assert item["item"] == "M* 414 Sk1"
        assert item["itemLinkTo"]["sheetId"] == "Mx414_Sk1"
        assert item["itemLinkTo"]["complexId"] == "mx414"
        assert item["itemDescription"] == "(Skizze zu Studienkomposition)"


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

    def test_calls_process_system_for_each_non_skipped_entry(self, helper):
        """Test that _process_system is called once per non-skipped entry."""
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

    def test_calls_process_measure_and_not_process_row_when_measure_str_present(
        self, helper
    ):
        """Test that _process_measure is called and _process_row is not when 'T.' is present."""
        with (
            patch.object(
                helper, "_process_measure", return_value="1–3"
            ) as mock_measure,
            patch.object(helper, "_process_row") as mock_row,
        ):
            helper._process_system("System 1: T. 1–3")
            mock_measure.assert_called_once_with("T. 1–3")
            mock_row.assert_not_called()

    def test_calls_process_row_and_not_process_measure_when_measure_str_absent(
        self, helper
    ):
        """Test that _process_row is called and _process_measure is not when 'T.' is absent."""
        with (
            patch.object(helper, "_process_row", return_value=None) as mock_row,
            patch.object(helper, "_process_measure") as mock_measure,
        ):
            helper._process_system("System 1: Gg (1)")
            mock_row.assert_called_once_with("Gg (1)")
            mock_measure.assert_not_called()

    def test_neither_sub_method_called_when_no_colon(self, helper):
        """Test that neither _process_measure nor _process_row is called when there's no colon."""
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
