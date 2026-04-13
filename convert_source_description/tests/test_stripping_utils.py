"""Tests for stripping_utils.py."""

import pytest

from utils.stripping_utils import StrippingUtils


class TestStripByDelimiter:
    """Tests for the strip_by_delimiter function."""

    @pytest.mark.parametrize(
        "input_string, delimiter, expected_result",
        [
            ("a, b, c", ",", ["a", "b", "c"]),
            ("a; b; c", ";", ["a", "b", "c"]),
            ("a: b: c", ":", ["a", "b", "c"]),
            ("a| b| c", "|", ["a", "b", "c"]),
        ],
    )
    def test_with_single_occurence(self, input_string, delimiter, expected_result):
        """Test that the input string with single occurcence is stripped correctly."""
        actual_stripped_result = StrippingUtils.strip_by_delimiter(input_string, delimiter)
        assert actual_stripped_result == expected_result

    @pytest.mark.parametrize(
        "input_string, delimiter, expected_result",
        [
            ("a ,b ,, c", ",", ["a", "b", "", "c"]),
            ("a ;b ;; c", ";", ["a", "b", "", "c"]),
            ("a :b :: c", ":", ["a", "b", "", "c"]),
            ("a |b || c", "|", ["a", "b", "", "c"]),
        ],
    )
    def test_with_multiple_occurences(self, input_string, delimiter, expected_result):
        """Test that the input string with multiple occurences is stripped correctly."""
        actual_stripped_result = StrippingUtils.strip_by_delimiter(input_string, delimiter)
        assert actual_stripped_result == expected_result

    @pytest.mark.parametrize(
        "input_string, delimiter, expected_result",
        [
            ("a, b; c", ";", ["a, b", "c"]),
            ("a, b; c", ",", ["a", "b; c"]),
            ("a, b; c", ":", ["a, b; c"]),
            ("a, b; c", "|", ["a, b; c"]),
        ],
    )
    def test_with_different_delimiters(self, input_string, delimiter, expected_result):
        """Test that the input string is stripped correctly with different delimiters."""
        actual_stripped_result = StrippingUtils.strip_by_delimiter(input_string, delimiter)
        assert actual_stripped_result == expected_result

    def test_with_leading_delimiter(self):
        """Test that the input string with leading delimiter is stripped correctly."""
        expected_result = ["", "a", "b", "c"]
        actual_stripped_result = StrippingUtils.strip_by_delimiter(",a, b, c", ",")
        assert actual_stripped_result == expected_result

    def test_with_trailing_delimiter(self):
        """Test that the input string with trailing delimiter is stripped correctly."""
        expected_result = ["a", "b", "c", ""]
        actual_stripped_result = StrippingUtils.strip_by_delimiter("a, b, c,", ",")
        assert actual_stripped_result == expected_result

    @pytest.mark.parametrize(
        "input_string, delimiter, expected_result",
        [
            ("a, b, c", ",", ["a", "b", "c"]),
            (" a ,b, c ", ",", ["a", "b", "c"]),
            ("   a   ,   b   ,   c   ", ",", ["a", "b", "c"]),
        ],
    )
    def test_with_whitespace(self, input_string, delimiter, expected_result):
        """Test that the input string with whitespace is stripped correctly."""
        actual_stripped_result = StrippingUtils.strip_by_delimiter(input_string, delimiter)
        assert actual_stripped_result == expected_result

    def test_with_delimiter_not_found(self):
        """Test that it returns the input string when the delimiter is not found."""
        expected_result = ["abcd"]
        actual_stripped_result = StrippingUtils.strip_by_delimiter("abcd", ",")
        assert actual_stripped_result == expected_result

    def test_with_empty_string_input(self):
        """Test that it returns an empty list when the input string is empty."""
        expected_result = [""]
        actual_stripped_result = StrippingUtils.strip_by_delimiter("", ",")
        assert actual_stripped_result == expected_result


class TestStripTagAndClean:
    """Tests for the strip_tag_and_clean function."""

    def test_valid_tags(self):
        """Test stripping valid tags and cleaning content."""
        content = "<td><p>Test Content</p></td>"
        tag = "td"
        expected_result = "Test Content"
        result = StrippingUtils.strip_tag_and_clean(content, tag)
        assert result == expected_result

    def test_nested_tags(self):
        """Test stripping nested tags and cleaning content."""
        content = "<td><p><strong>Strong Nested Content</strong></p></td>"
        tag = "td"
        expected_result = "<strong>Strong Nested Content</strong>"
        result = StrippingUtils.strip_tag_and_clean(content, tag)
        assert result == expected_result

    def test_multiple_paragraphs(self):
        """Test replacing multiple <p> tags with <br />."""
        content = "<td><p>First paragraph</p><p>Second paragraph</p></td>"
        tag = "td"
        expected_result = "First paragraph <br /> Second paragraph"
        result = StrippingUtils.strip_tag_and_clean(content, tag)
        assert result == expected_result

    def test_multiple_paragraphs_with_nested_tags(self):
        """Test replacing multiple <p> tags with <br />."""
        content = "<td><p><strong>First paragraph</strong></p><p><em>Second paragraph</em></p></td>"
        tag = "td"
        expected_result = "<strong>First paragraph</strong> <br /> <em>Second paragraph</em>"
        result = StrippingUtils.strip_tag_and_clean(content, tag)
        assert result == expected_result

    def test_malformed_tags(self):
        """Test content with malformed tags."""
        content = "<td><p><strong>Malformed Content</p></td>"
        tag = "td"
        expected_result = "<strong>Malformed Content"
        result = StrippingUtils.strip_tag_and_clean(content, tag)
        assert result == expected_result

    def test_no_matching_tags(self):
        """Test content with no matching tags."""
        content = "<p>No matching tags here</p>"
        tag = "td"
        expected_result = ""
        result = StrippingUtils.strip_tag_and_clean(content, tag)
        assert result == expected_result

    def test_empty_content(self):
        """Test empty content."""
        content = ""
        tag = "td"
        expected_result = ""
        result = StrippingUtils.strip_tag_and_clean(content, tag)
        assert result == expected_result

    def test_with_none(self):
        """Test that it returns an empty string when passed None."""
        content = None
        tag = "strong"
        expected_result = ""
        actual_stripped_result = StrippingUtils.strip_tag_and_clean(content, tag)
        assert actual_stripped_result == expected_result


class TestStripTag:
    """Tests for the strip_tag function."""

    def test_with_p(self):
        """Test that it strips a paragraph tag."""
        content = "<p>Hello, World!</p>"
        expected_result = "Hello, World!"
        actual_stripped_result = StrippingUtils.strip_tag(content, "p")
        assert actual_stripped_result == expected_result

    def test_with_div(self):
        """Test that it strips a div tag."""
        content = "<div> This is a div </div>"
        expected_result = "This is a div"
        actual_stripped_result = StrippingUtils.strip_tag(content, "div")
        assert actual_stripped_result == expected_result

    def test_with_h1(self):
        """Test that it strips a heading tag."""
        content = "<h1> Heading 1 </h1>"
        expected_result = "Heading 1"
        actual_stripped_result = StrippingUtils.strip_tag(content, "h1")
        assert actual_stripped_result == expected_result

    def test_with_nested_tag(self):
        """Test that it strips a nested tag."""
        content = "<p><strong>This is a nested tag</strong></p>"
        expected_result = "<strong>This is a nested tag</strong>"
        actual_stripped_result = StrippingUtils.strip_tag(content, "p")
        assert actual_stripped_result == expected_result

    def test_with_empty_tag(self):
        """Test that it returns an empty tag when passed an empty tag."""
        content = "<p></p>"
        expected_result = ""
        actual_stripped_result = StrippingUtils.strip_tag(content, "p")
        assert actual_stripped_result == expected_result

    def test_with_plain_text(self):
        """Test that it returns the plain text when passed plain text."""
        content = "This is a plain text"
        expected_result = "This is a plain text"
        actual_stripped_result = StrippingUtils.strip_tag(content, "p")
        assert actual_stripped_result == expected_result

    def test_with_empty_string(self):
        """Test that it returns an empty string when passed an empty string."""
        content = ""
        expected_result = ""
        actual_stripped_result = StrippingUtils.strip_tag(content, "p")
        assert actual_stripped_result == expected_result

    def test_with_none(self):
        """Test that it returns an empty string when passed None."""
        content = None
        expected_result = ""
        actual_stripped_result = StrippingUtils.strip_tag(content, "p")
        assert actual_stripped_result == expected_result
