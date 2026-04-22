"""Tests for index_utils.py"""

from bs4 import BeautifulSoup

from utils.index_utils import IndexUtils


class TestFindSiglumIndices:
    """Tests for IndexUtils.find_siglum_indices."""

    def test_with_single_siglum(self):
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
        actual_indices = IndexUtils.find_siglum_indices(paras)
        # Assert
        assert actual_indices == expected_indices

    def test_with_multiple_siglums(self):
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
        actual_indices = IndexUtils.find_siglum_indices(paras)
        # Assert
        assert actual_indices == expected_indices

    def test_with_siglum_in_brackets(self):
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
        actual_indices = IndexUtils.find_siglum_indices(paras)
        # Assert
        assert actual_indices == expected_indices

    def test_with_optional_additional_siglum(self):
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
        actual_indices = IndexUtils.find_siglum_indices(paras)
        # Assert
        assert actual_indices == expected_indices

    def test_with_no_siglums(self):
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
        actual_indices = IndexUtils.find_siglum_indices(paras)
        # Assert
        assert actual_indices == expected_indices

    def test_in_fixture_paras(self, sample_soup_paras):
        """Test that the correct indices are found in the fixture sample paras."""
        # Arrange
        expected_indices = [1, 16]
        # Act
        actual_indices = IndexUtils.find_siglum_indices(sample_soup_paras)
        # Assert
        assert actual_indices == expected_indices


class TestFindContentsIndices:
    """Tests for IndexUtils.find_contents_indices."""

    def test_returns_minus_one_for_contents_start_index_when_inhalt_not_found(self):
        """Test that contents_start_index is -1 when 'Inhalt:' is absent."""
        soup = BeautifulSoup(
            "<p>other</p><p>Textkritischer Kommentar:</p>", "html.parser"
        )
        paras = soup.find_all("p")
        contents_start_index, _ = IndexUtils.find_contents_indices(paras)
        assert contents_start_index == -1

    def test_returns_correct_contents_start_index_when_inhalt_found(self):
        """Test that contents_start_index matches the position of 'Inhalt:'."""
        soup = BeautifulSoup(
            "<p>other</p><p>Inhalt:</p><p>just another</p>", "html.parser"
        )
        paras = soup.find_all("p")
        contents_start_index, _ = IndexUtils.find_contents_indices(paras)
        assert contents_start_index == 1

    def test_returns_contents_end_index_for_textkritischer_kommentar(self):
        """Test that contents_end_index uses 'Textkritischer Kommentar:' when present."""
        soup = BeautifulSoup(
            "<p>Inhalt:</p><p>item</p><p>Textkritischer Kommentar:</p>",
            "html.parser",
        )
        paras = soup.find_all("p")
        contents_start_index, contents_end_index = IndexUtils.find_contents_indices(
            paras
        )
        assert contents_start_index == 0
        assert contents_end_index == 2

    def test_returns_contents_end_index_for_textkritische_anmerkungen(self):
        """Test that contents_end_index uses 'Textkritische Anmerkungen:' when present."""
        soup = BeautifulSoup(
            "<p>Inhalt:</p><p>item</p><p>Textkritische Anmerkungen:</p>",
            "html.parser",
        )
        paras = soup.find_all("p")
        contents_start_index, contents_end_index = IndexUtils.find_contents_indices(
            paras
        )
        assert contents_start_index == 0
        assert contents_end_index == 2

    def test_returns_last_valid_index_when_no_comments_label_found(self):
        """Test that contents_end_index is len(paras) - 1 when no comments label is found."""
        soup = BeautifulSoup(
            "<p>Inhalt:</p><p>item1</p><p>item2</p><p>last</p>",
            "html.parser",
        )
        paras = soup.find_all("p")
        contents_start_index, contents_end_index = IndexUtils.find_contents_indices(
            paras
        )
        assert contents_start_index == 0
        assert contents_end_index == len(paras) - 1
