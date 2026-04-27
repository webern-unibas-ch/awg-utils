# pylint: disable=protected-access
"""Tests for utils/html_utils.py"""

from unittest.mock import patch

from utils.html_utils import HTMLUtils


class TestGroupBlockContent:
    """Tests for the group_block_content function."""

    def test_passes_through_non_small_para(self):
        """Test that a regular paragraph is passed through unchanged."""
        items = ["<p>Regular paragraph.</p>"]
        assert HTMLUtils.group_block_content(items) == items

    def test_single_small_para_wrapped_in_blockquote(self):
        """Test that a single small paragraph is wrapped in a blockquote."""
        items = ["<p class='small'>Small text.</p>"]
        result = HTMLUtils.group_block_content(items)
        assert len(result) == 1
        assert result[0] == "<blockquote><p>Small text.</p></blockquote>"

    def test_consecutive_small_paras_combined(self):
        """Test that consecutive small paragraphs are combined into one blockquote."""
        items = [
            "<p class='small'>First.</p>",
            "<p class='small'>Second.</p>",
        ]
        result = HTMLUtils.group_block_content(items)
        assert len(result) == 1
        assert result[0] == "<blockquote><p>First.</p><p>Second.</p></blockquote>"

    def test_non_consecutive_small_paras_produce_two_blockquotes(self):
        """Test that two separate runs of small paragraphs produce two blockquotes."""
        items = [
            "<p class='small'>First.</p>",
            "<p>Normal.</p>",
            "<p class='small'>Second.</p>",
        ]
        result = HTMLUtils.group_block_content(items)
        assert len(result) == 3
        assert result[0] == "<blockquote><p>First.</p></blockquote>"
        assert result[1] == "<p>Normal.</p>"
        assert result[2] == "<blockquote><p>Second.</p></blockquote>"

    def test_small_list_para_not_grouped(self):
        """Test that a <p> with both 'small' and 'list' classes is not treated as small."""
        items = ["<p class='small list'>List item.</p>"]
        assert HTMLUtils.group_block_content(items) == items

    def test_empty_list_returns_empty(self):
        """Test that an empty input list returns an empty list."""
        assert not HTMLUtils.group_block_content([])

    def test_mixed_content_order_preserved(self):
        """Test that the order of items is preserved in the output."""
        items = [
            "<p>First normal.</p>",
            "<p class='small'>Small.</p>",
            "<p>Last normal.</p>",
        ]
        result = HTMLUtils.group_block_content(items)
        assert result[0] == "<p>First normal.</p>"
        assert result[1] == "<blockquote><p>Small.</p></blockquote>"
        assert result[2] == "<p>Last normal.</p>"

    def test_delegates_to_is_small_para(self):
        """Test that group_block_content triggers _is_small_para for each item."""
        items = ["<p>First.</p>", "<p>Second.</p>"]
        with patch.object(
            HTMLUtils, "_is_small_para", return_value=False
        ) as mock_is_small:
            HTMLUtils.group_block_content(items)
        assert mock_is_small.call_count == len(items)

    def test_delegates_to_combine_small_paras(self):
        """Test that group_block_content triggers _combine_small_paras for a small para run."""
        items = ["<p class='small'>Small.</p>"]
        with patch.object(HTMLUtils, "_is_small_para", return_value=True):
            with patch.object(
                HTMLUtils,
                "_combine_small_paras",
                return_value="<blockquote><p>Small.</p></blockquote>",
            ) as mock_combine:
                HTMLUtils.group_block_content(items)
        mock_combine.assert_called_once_with(items)

    def test_does_not_trigger_combine_small_paras_for_non_small(self):
        """Test that _combine_small_paras is not triggered for non-small paragraphs."""
        items = ["<p>Normal.</p>"]
        with patch.object(HTMLUtils, "_is_small_para", return_value=False):
            with patch.object(HTMLUtils, "_combine_small_paras") as mock_combine:
                HTMLUtils.group_block_content(items)
        mock_combine.assert_not_called()


class TestHtmlToMd:
    """Tests for the html_to_md function."""

    def test_converts_paragraph(self):
        """Test that a plain paragraph is converted to plain text."""
        assert HTMLUtils.html_to_md("<p>Hello world.</p>") == "Hello world."

    def test_converts_bold(self):
        """Test that bold HTML is converted to Markdown bold."""
        assert HTMLUtils.html_to_md("<p><strong>Bold</strong></p>") == "**Bold**"

    def test_converts_heading(self):
        """Test that an h2 element is converted to an ATX heading."""
        assert HTMLUtils.html_to_md("<h2>Title</h2>") == "## Title"

    def test_strips_angular_bindings(self):
        """Test that Angular event bindings are stripped before conversion."""
        html = '<p (click)="doSomething()">Text</p>'
        assert HTMLUtils.html_to_md(html) == "Text"

    def test_tokenizes_footnote_ref(self):
        """Test that a footnote reference anchor is converted to a Markdown footnote ref."""
        html = "<sup><a id='note-ref-1'>1</a></sup>"
        assert HTMLUtils.html_to_md(html) == "[^1]"

    def test_tokenizes_footnote_crossref(self):
        """Test that a cross-reference anchor is converted to an inline link."""
        html = (
            "<a (click)=\"ref.navigateToIntroFragment({fragmentId: 'note-3'})\">3</a>"
        )
        assert HTMLUtils.html_to_md(html) == "[3](#fn3)"

    def test_tokenizes_pipe(self):
        """Test that a pipe character in text is converted to an escaped Markdown pipe."""
        assert HTMLUtils.html_to_md("<p>a | b</p>") == r"a \| b"

    def test_returns_empty_string_for_empty_input(self):
        """Test that an empty string input returns an empty string."""
        assert HTMLUtils.html_to_md("") == ""

    def test_returns_empty_string_for_non_string(self):
        """Test that a non-string input returns an empty string."""
        assert HTMLUtils.html_to_md(None) == ""  # type: ignore[arg-type]


class TestParseBlockNote:
    """Tests for the parse_block_note function."""

    def test_returns_number_and_stripped_html(self):
        """Test that a valid blockNote returns a (number, html) tuple."""
        note = "<p id='note-3'>Content</p>"
        result = HTMLUtils.parse_block_note(note)
        assert result == ("3", "Content")

    def test_double_quoted_id(self):
        """Test that a double-quoted note id attribute is parsed correctly."""
        note = '<p id="note-7">Content</p>'
        result = HTMLUtils.parse_block_note(note)
        assert result == ("7", "Content")

    def test_returns_none_when_no_note_id(self):
        """Test that None is returned when no note id is present."""
        assert HTMLUtils.parse_block_note("<p>No id here</p>") is None

    def test_strips_backlink_anchor(self):
        """Test that the backlink anchor and pipe separator are removed from the result."""
        note = (
            "<p id='note-2'>"
            "<a class='note-backlink' href='#note-ref-2'>↑</a> | "
            "Note content."
            "</p>"
        )
        num, html = HTMLUtils.parse_block_note(note)
        assert num == "2"
        assert html == "Note content."
        assert "note-backlink" not in html

    def test_returns_tuple_not_list(self):
        """Test that the return value is a tuple."""
        note = "<p id='note-1'>Content</p>"
        result = HTMLUtils.parse_block_note(note)
        assert isinstance(result, tuple)

    def test_delegates_to_extract_note_number(self):
        """Test that parse_block_note triggers _extract_note_number with the input."""
        note = "<p id='note-1'>Content</p>"
        with patch.object(
            HTMLUtils, "_extract_note_number", return_value="1"
        ) as mock_extract:
            with patch.object(HTMLUtils, "_strip_note_html", return_value="Content"):
                HTMLUtils.parse_block_note(note)
        mock_extract.assert_called_once_with(note)

    def test_delegates_to_strip_note_html_when_number_found(self):
        """Test that parse_block_note triggers _strip_note_html when a note number is found."""
        note = "<p id='note-1'>Content</p>"
        with patch.object(HTMLUtils, "_extract_note_number", return_value="1"):
            with patch.object(
                HTMLUtils, "_strip_note_html", return_value="Content"
            ) as mock_strip:
                HTMLUtils.parse_block_note(note)
        mock_strip.assert_called_once_with(note)

    def test_does_not_call_strip_note_html_when_no_number(self):
        """Test that _strip_note_html is not triggered when no note number is found."""
        with patch.object(HTMLUtils, "_extract_note_number", return_value=None):
            with patch.object(HTMLUtils, "_strip_note_html") as mock_strip:
                HTMLUtils.parse_block_note("<p>No id</p>")
        mock_strip.assert_not_called()


class TestCombineSmallParas:
    """Tests for the _combine_small_paras function."""

    def test_wraps_single_item_in_blockquote(self):
        """Test that a single small paragraph is wrapped in a blockquote."""
        result = HTMLUtils._combine_small_paras(["<p class='small'>Text.</p>"])
        assert result == "<blockquote><p>Text.</p></blockquote>"

    def test_wraps_multiple_items_in_one_blockquote(self):
        """Test that multiple small paragraphs are combined in a single blockquote."""
        result = HTMLUtils._combine_small_paras(
            [
                "<p class='small'>First.</p>",
                "<p class='small'>Second.</p>",
            ]
        )
        assert result == "<blockquote><p>First.</p><p>Second.</p></blockquote>"

    def test_strips_p_attributes(self):
        """Test that the <p> wrapper attributes are stripped from each item."""
        result = HTMLUtils._combine_small_paras(["<p class='small' id='x'>Body.</p>"])
        assert result == "<blockquote><p>Body.</p></blockquote>"


class TestExtractNoteNumber:
    """Tests for the _extract_note_number function."""

    def test_extracts_single_quoted_id(self):
        """Test that a note number is extracted from a single-quoted id attribute."""
        assert HTMLUtils._extract_note_number("<p id='note-5'>Text</p>") == "5"

    def test_extracts_double_quoted_id(self):
        """Test that a note number is extracted from a double-quoted id attribute."""
        assert HTMLUtils._extract_note_number('<p id="note-12">Text</p>') == "12"

    def test_returns_none_when_no_id(self):
        """Test that None is returned when no note id is present."""
        assert HTMLUtils._extract_note_number("<p>No id</p>") is None

    def test_returns_none_for_non_note_id(self):
        """Test that None is returned when the id does not match the note-N pattern."""
        assert HTMLUtils._extract_note_number("<p id='other-3'>Text</p>") is None


class TestIsSmallPara:
    """Tests for the _is_small_para function."""

    def test_returns_true_for_small_class(self):
        """Test that a <p> with class 'small' is detected as a small paragraph."""
        assert HTMLUtils._is_small_para("<p class='small'>Text</p>") is True

    def test_returns_false_for_small_list_class(self):
        """Test that a <p> with both 'small' and 'list' classes is not a small paragraph."""
        assert HTMLUtils._is_small_para("<p class='small list'>Text</p>") is False

    def test_returns_false_for_regular_para(self):
        """Test that a plain <p> is not a small paragraph."""
        assert HTMLUtils._is_small_para("<p>Normal</p>") is False

    def test_returns_false_for_non_para(self):
        """Test that a non-paragraph element is not a small paragraph."""
        assert HTMLUtils._is_small_para("<table class='small'>Text</table>") is False

    def test_handles_leading_whitespace(self):
        """Test that leading whitespace before the tag is ignored."""
        assert HTMLUtils._is_small_para("  <p class='small'>Text</p>") is True


class TestStripAngularBindings:
    """Tests for the _strip_angular_bindings function."""

    def test_strips_double_quoted_binding(self):
        """Test that a double-quoted Angular event binding is removed."""
        assert (
            HTMLUtils._strip_angular_bindings('<p (click)="fn()">Text</p>')
            == "<p>Text</p>"
        )

    def test_strips_single_quoted_binding(self):
        """Test that a single-quoted Angular event binding is removed."""
        assert (
            HTMLUtils._strip_angular_bindings("<p (click)='fn()'>Text</p>")
            == "<p>Text</p>"
        )

    def test_strips_multiple_bindings(self):
        """Test that multiple Angular event bindings are all removed."""
        html = '<a (click)="a()" (hover)="b()">Link</a>'
        assert HTMLUtils._strip_angular_bindings(html) == "<a>Link</a>"

    def test_plain_html_unchanged(self):
        """Test that HTML without Angular bindings is returned unchanged."""
        html = "<p class='note'>Text</p>"
        assert HTMLUtils._strip_angular_bindings(html) == html


class TestStripNoteHtml:
    """Tests for the _strip_note_html function."""

    def test_strips_backlink_pipe_and_wrapping_p(self):
        """Test that the backlink anchor, pipe separator and wrapping <p> are removed."""
        note = (
            "<p id='note-1'>"
            "<a class='note-backlink' href='#note-ref-1'>Link text</a> | "
            "Note text."
            "</p>"
        )
        assert HTMLUtils._strip_note_html(note) == "Note text."

    def test_strips_backlink_and_pipe_without_p(self):
        """Test that the backlink anchor and pipe separator without a wrapping <p> are removed."""
        note = "<a class='note-backlink' href='#note-ref-1'>Link text</a> | Note text."
        assert HTMLUtils._strip_note_html(note) == "Note text."

    def test_strips_wrapping_p_tag(self):
        """Test that the outer <p> wrapper is stripped."""
        assert HTMLUtils._strip_note_html("<p>Inner content.</p>") == "Inner content."

    def test_strips_wrapping_p_tag_with_attributes(self):
        """Test that the outer <p> wrapper with attributes is stripped."""
        assert (
            HTMLUtils._strip_note_html("<p id='note-3'>Inner content.</p>")
            == "Inner content."
        )

    def test_plain_content_unchanged(self):
        """Test that content without a <p> wrapper or backlink is returned as-is."""
        assert HTMLUtils._strip_note_html("Plain text.") == "Plain text."
