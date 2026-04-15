# pylint: disable=protected-access
"""Tests for utils_helper.py"""

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
