# pylint: disable=protected-access
"""Tests for paragraph_utils.py."""

from unittest.mock import patch

from bs4 import BeautifulSoup, Tag

from utils.paragraph_utils import ParagraphUtils


class TestGetParagraphContentByLabel:
    """Tests for the get_paragraph_content_by_label function."""

    def test_get_paragraph_content_by_label_with_label_found(self):
        """Test that the correct content of a paragraph is returned as array if label is found."""
        paras = [
            BeautifulSoup("<p>Paragraph 1</p>", "html.parser").p,
            BeautifulSoup("<p>Label: Paragraph 2</p>", "html.parser").p,
        ]
        label = "Label:"
        expected_content = ["Paragraph 2"]
        actual_content = ParagraphUtils.get_paragraph_content_by_label(label, paras)
        assert actual_content == expected_content

    def test_get_paragraph_content_by_label_strips_punctuation_marks(self):
        """Test that paragraph content strips final punctuation marks when label is found."""
        paras = [
            BeautifulSoup("<p>Paragraph 1</p>", "html.parser").p,
            BeautifulSoup("<p>Label: Paragraph 2.</p>", "html.parser").p,
        ]
        label = "Label:"
        expected_content = ["Paragraph 2"]
        actual_content = ParagraphUtils.get_paragraph_content_by_label(label, paras)
        assert actual_content == expected_content

    def test_get_paragraph_content_by_label_with_label_not_found(self):
        """Test that empty array is returned if the label is not found."""
        paras = [
            BeautifulSoup("<p>Paragraph 1</p>", "html.parser").p,
            BeautifulSoup("<p>Paragraph 2</p>", "html.parser").p,
        ]
        label = "Label:"
        expected_content = []
        actual_content = ParagraphUtils.get_paragraph_content_by_label(label, paras)
        assert actual_content == expected_content

    def test_get_paragraph_content_by_label_in_fixture(self, sample_soup_paras):
        """Test that the correct content of a paragraph is returned if label is found."""
        label = "Beschreibstoff:"
        expected_content = [
            "Notenpapier, 28 Systeme, Format: hoch 343 × 264 mm, Firmenzeichen abgerissen",
            (
                "Notenpapier, 12 Systeme (unten beschnitten), Format (quer): "
                "163 × 255 mm, kein Firmenzeichen"
            ),
        ]
        actual_content = ParagraphUtils.get_paragraph_content_by_label(
            label, sample_soup_paras
        )
        assert actual_content == expected_content

    def test_get_paragraph_content_by_label_triggers_siblings_method_when_ends_with_semicolon(
        self,
    ):
        """Test that sibling processing is triggered for semicolon-terminated initial content."""
        html = """
            <p>Label: Content 1; </p><p>Content 2;</p><p>Content 3.</p>
            """
        soup = BeautifulSoup(html, "html.parser")
        paras = soup.find_all("p")

        with patch.object(
            ParagraphUtils,
            "_get_paragraph_siblings",
            wraps=ParagraphUtils._get_paragraph_siblings,
        ) as mock_siblings:
            ParagraphUtils.get_paragraph_content_by_label("Label:", paras)
            mock_siblings.assert_called_once()

    def test_get_paragraph_content_by_label_skips_siblings_without_semicolon(
        self,
    ):
        """Test that sibling processing is not triggered without trailing semicolon."""
        html = """
            <p>Label: Content 1.</p><p>Content 2</p>
            """
        soup = BeautifulSoup(html, "html.parser")
        paras = soup.find_all("p")

        with patch.object(ParagraphUtils, "_get_paragraph_siblings") as mock_siblings:
            ParagraphUtils.get_paragraph_content_by_label("Label:", paras)
            mock_siblings.assert_not_called()


class TestGetParagraphIndexByLabel:
    """Tests for the get_paragraph_index_by_label function."""

    def test_get_paragraph_index_by_label_with_label_found(self):
        """Test that the correct index is returned if the label is found."""
        paras = [
            BeautifulSoup("<p>Paragraph 1</p>", "html.parser").p,
            BeautifulSoup("<p>Label: Paragraph 2</p>", "html.parser").p,
        ]
        label = "Label:"
        expected_index = 1
        actual_index = ParagraphUtils.get_paragraph_index_by_label(label, paras)
        assert actual_index == expected_index

    def test_get_paragraph_index_by_label_with_label_not_found(self):
        """Test that -1 is returned if the label is not found."""
        paras = [
            BeautifulSoup("<p>Paragraph 1</p>", "html.parser").p,
            BeautifulSoup("<p>Paragraph 2</p>", "html.parser").p,
        ]
        label = "Label:"
        expected_index = -1
        actual_index = ParagraphUtils.get_paragraph_index_by_label(label, paras)
        assert actual_index == expected_index

    def test_get_paragraph_index_by_label_with_empty_label(self):
        """Test that -1 is returned if the label is empty."""
        paras = [
            BeautifulSoup("<p>Paragraph 1</p>", "html.parser").p,
            BeautifulSoup("<p>Paragraph 2</p>", "html.parser").p,
        ]
        label = ""
        expected_index = -1
        actual_index = ParagraphUtils.get_paragraph_index_by_label(label, paras)
        assert actual_index == expected_index

    def test_get_paragraph_index_by_label_with_none_label(self):
        """Test that -1 is returned if the label is None."""
        paras = [
            BeautifulSoup("<p>Paragraph 1</p>", "html.parser").p,
            BeautifulSoup("<p>Paragraph 2</p>", "html.parser").p,
        ]
        label = None
        expected_index = -1
        actual_index = ParagraphUtils.get_paragraph_index_by_label(label, paras)
        assert actual_index == expected_index

    def test_get_paragraph_index_by_label_in_fixture(self, sample_soup_paras):
        """Test that the correct index is returned if the label is found in fixture paras."""
        label = "Inhalt:"
        expected_index = 8
        actual_index = ParagraphUtils.get_paragraph_index_by_label(
            label, sample_soup_paras
        )
        assert actual_index == expected_index


class TestGetParagraphSiblings:
    """Tests for the _get_paragraph_siblings function."""

    def test_get_paragraph_siblings_with_semicolon_to_fullstop(self):
        """Test that siblings are processed until one ends with full stop."""
        html = """
            <p>Content 1; </p><p>Content 2;</p><p>Content 3.</p><p>Content 4</p>
            """
        soup = BeautifulSoup(html, "html.parser")
        paras = soup.find_all("p")
        content_paragraph = paras[0]
        content_lines = ["Content 1"]

        ParagraphUtils._get_paragraph_siblings(content_paragraph, content_lines)

        expected_content = ["Content 1", "Content 2", "Content 3"]
        assert content_lines == expected_content

    def test_get_paragraph_siblings_breaks_at_fullstop(self):
        """Test that loop breaks when sibling ends with full stop."""
        html = """
            <p>Content 1; </p><p>Content 2.</p><p>Content 3</p>
            """
        soup = BeautifulSoup(html, "html.parser")
        paras = soup.find_all("p")
        content_paragraph = paras[0]
        content_lines = ["Content 1"]

        ParagraphUtils._get_paragraph_siblings(content_paragraph, content_lines)

        # Should NOT include Content 3 because loop breaks after Content 2 (ends with .)
        expected_content = ["Content 1", "Content 2"]
        assert content_lines == expected_content

    def test_get_paragraph_siblings_breaks_at_no_punctuation(self):
        """Test that loop breaks when sibling doesn't end with full stop or semicolon."""
        html = """
            <p>Content 1; </p><p>Content 2;</p><p>Content 3 no punctuation</p><p>Content 4</p>
            """
        soup = BeautifulSoup(html, "html.parser")
        paras = soup.find_all("p")
        content_paragraph = paras[0]
        content_lines = ["Content 1"]

        ParagraphUtils._get_paragraph_siblings(content_paragraph, content_lines)

        # Should include Content 2 but break at Content 3 (no punctuation)
        expected_content = ["Content 1", "Content 2"]
        assert content_lines == expected_content

    def test_get_paragraph_siblings_no_siblings(self):
        """Test sibling processing when there are no siblings."""
        html = "<p>Content 1; </p>"
        soup = BeautifulSoup(html, "html.parser")
        paras = soup.find_all("p")
        content_paragraph = paras[0]
        content_lines = ["Content 1"]

        ParagraphUtils._get_paragraph_siblings(content_paragraph, content_lines)

        # Should remain unchanged
        expected_content = ["Content 1"]
        assert content_lines == expected_content

    def test_get_paragraph_siblings_strips_punctuation(self):
        """Test that sibling content strips FULL_STOP and SEMICOLON punctuation."""
        html = """
            <p>Content 1; </p><p>Content 2 with semicolon;</p><p>Content 3 with period.</p>
            """
        soup = BeautifulSoup(html, "html.parser")
        paras = soup.find_all("p")
        content_paragraph = paras[0]
        content_lines = ["Content 1"]

        ParagraphUtils._get_paragraph_siblings(content_paragraph, content_lines)

        expected_content = [
            "Content 1",
            "Content 2 with semicolon",
            "Content 3 with period",
        ]
        assert content_lines == expected_content

    def test_get_paragraph_siblings_multiple_semicolons(self):
        """Test sibling processing with multiple semicolon-terminated siblings."""
        html = """
            <p>Content 1; </p><p>Content 2;</p><p>Content 3;</p><p>Content 4;</p><p>Content 5.</p>
            """
        soup = BeautifulSoup(html, "html.parser")
        paras = soup.find_all("p")
        content_paragraph = paras[0]
        content_lines = ["Content 1"]

        ParagraphUtils._get_paragraph_siblings(content_paragraph, content_lines)

        expected_content = [
            "Content 1",
            "Content 2",
            "Content 3",
            "Content 4",
            "Content 5",
        ]
        assert content_lines == expected_content


class TestFindTagWithLabelInSoup:
    """Tests for the _get_paragraph_tag_with_label function."""

    def test_get_paragraph_tag_with_label_with_label_found(self):
        """Test that a label is found in the tag."""
        # Arrange
        paras = [
            BeautifulSoup("<p>Paragraph 1</p>", "html.parser").p,
            BeautifulSoup("<p>Label: Paragraph 2</p>", "html.parser").p,
        ]
        label = "Label:"
        expected_tag_with_label = paras[1]
        # Act
        actual_tag_with_label = ParagraphUtils._get_paragraph_tag_with_label(
            label, paras
        )
        # Assert
        assert isinstance(actual_tag_with_label, Tag)
        assert actual_tag_with_label == expected_tag_with_label

    def test_get_paragraph_tag_with_label_with_label_not_found(self):
        """Test that the tag is None if the label is not found."""
        # Arrange
        paras = [
            BeautifulSoup("<p>Paragraph 1</p>", "html.parser").p,
            BeautifulSoup("<p>Paragraph 2</p>", "html.parser").p,
        ]
        label = "Label:"
        # Act
        actual_tag_with_label = ParagraphUtils._get_paragraph_tag_with_label(
            label, paras
        )
        # Assert
        assert actual_tag_with_label is None

    def test_get_paragraph_tag_with_label_with_empty_label(self):
        """Test that the tag is None if the label is empty."""
        # Arrange
        paras = [
            BeautifulSoup("<p>Paragraph 1</p>", "html.parser").p,
            BeautifulSoup("<p>Paragraph 2</p>", "html.parser").p,
        ]
        label = ""
        expected_tag_with_label = None
        # Act
        actual_tag_with_label = ParagraphUtils._get_paragraph_tag_with_label(
            label, paras
        )
        # Assert
        assert actual_tag_with_label == expected_tag_with_label

    def test_get_paragraph_tag_with_label_with_none_label(self):
        """Test that the tag is None if the label is None."""
        # Arrange
        paras = [
            BeautifulSoup("<p>Paragraph 1</p>", "html.parser").p,
            BeautifulSoup("<p>Paragraph 2</p>", "html.parser").p,
        ]
        label = None
        expected_tag_with_label = None
        # Act
        actual_tag_with_label = ParagraphUtils._get_paragraph_tag_with_label(
            label, paras
        )
        # Assert
        assert actual_tag_with_label == expected_tag_with_label

    def test_get_paragraph_tag_with_label_in_fixture(self, sample_soup_paras):
        """Test that the correct tag with label is found in the fixture sample paras."""
        # Arrange
        label = "Beschreibstoff:"
        expected_tag_with_label = sample_soup_paras[5]
        # Act
        actual_tag_with_label = ParagraphUtils._get_paragraph_tag_with_label(
            label, sample_soup_paras
        )
        # Assert
        assert isinstance(actual_tag_with_label, Tag)
        assert actual_tag_with_label == expected_tag_with_label
