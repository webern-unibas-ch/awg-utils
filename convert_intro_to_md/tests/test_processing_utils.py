"""Tests for utils/processing_utils.py"""

from unittest.mock import call, patch

from utils.html_utils import HTMLUtils
from utils.processing_utils import ProcessingUtils


class TestAssembleMarkdown:
    """Tests for the assemble_markdown function."""

    def test_joins_lines_with_newline(self):
        """Test that lines are joined with newline separators."""
        result = ProcessingUtils.assemble_markdown(["# Title", "", "Paragraph."])
        assert result.startswith("# Title\n\nParagraph.")

    def test_appends_trailing_newline(self):
        """Test that the result always ends with a newline."""
        assert ProcessingUtils.assemble_markdown(["line"]).endswith("\n")

    def test_collapses_excess_newlines(self):
        """Test that three or more consecutive newlines are collapsed to two."""
        result = ProcessingUtils.assemble_markdown(["a", "", "", "", "b"])
        assert "\n\n\n" not in result

    def test_empty_list_returns_newline(self):
        """Test that an empty line list produces a single newline."""
        assert ProcessingUtils.assemble_markdown([]) == "\n"


class TestProcessBlockContent:
    """Tests for the process_block_content function."""

    def test_returns_empty_list_for_empty_input(self):
        """Test that an empty input list produces an empty output list."""
        assert not ProcessingUtils.process_block_content([])

    def test_delegates_to_group_block_content(self):
        """Test that HTML items are routed through HTMLUtils.group_block_content."""
        items = ["<p>Hello</p>"]
        with patch.object(HTMLUtils, "group_block_content", return_value=items) as mock:
            with patch.object(HTMLUtils, "html_to_md", return_value="Hello"):
                ProcessingUtils.process_block_content(items)
        mock.assert_called_once_with(items)

    def test_delegates_each_item_to_html_to_md(self):
        """Test that each grouped item is converted via HTMLUtils.html_to_md."""
        items = ["<p>A</p>", "<p>B</p>"]
        with patch.object(HTMLUtils, "group_block_content", return_value=items):
            with patch.object(HTMLUtils, "html_to_md", return_value="x") as mock_md:
                ProcessingUtils.process_block_content(items)
        mock_md.assert_has_calls([call(items[0]), call(items[1])])

    def test_blank_line_after_each_entry(self):
        """Test that each converted entry is followed by a blank line."""
        items = ["<p>A</p>", "<p>B</p>", "<p>C</p>"]
        with patch.object(HTMLUtils, "group_block_content", return_value=items):
            with patch.object(HTMLUtils, "html_to_md", side_effect=["A", "B", "C"]):
                result = ProcessingUtils.process_block_content(items)
        assert result == ["A", "", "B", "", "C", ""]

    def test_skips_empty_html_to_md_results(self):
        """Test that items converting to an empty string are omitted from output."""
        items = ["<p>A</p>", "<p></p>", "<p>C</p>"]
        with patch.object(HTMLUtils, "group_block_content", return_value=items):
            with patch.object(HTMLUtils, "html_to_md", side_effect=["A", "", "C"]):
                result = ProcessingUtils.process_block_content(items)
        assert result == ["A", "", "C", ""]


class TestProcessBlockNotes:
    """Tests for the process_block_notes function."""

    def test_empty_block_notes_leaves_dict_unchanged(self):
        """Test that an empty input list does not modify the notes dict."""
        notes = {}
        ProcessingUtils.process_block_notes([], notes)
        assert not notes

    def test_delegates_to_parse_block_note(self):
        """Test that each note string is parsed via HTMLUtils.parse_block_note."""
        block_notes = ["<p id='note-1'>Note one</p>"]
        with patch.object(HTMLUtils, "parse_block_note", return_value=None) as mock:
            ProcessingUtils.process_block_notes(block_notes, {})
        mock.assert_called_once_with("<p id='note-1'>Note one</p>")

    def test_populates_notes_dict_from_parsed_result(self):
        """Test that a successfully parsed note is added to the notes dict."""
        notes = {}
        with patch.object(
            HTMLUtils, "parse_block_note", return_value=("1", "Note one")
        ):
            ProcessingUtils.process_block_notes(["<p id='note-1'>Note one</p>"], notes)
        assert notes == {"1": "Note one"}

    def test_processes_multiple_notes(self):
        """Test that multiple block notes are all parsed and added to the dict."""
        notes = {}
        side_effects = [("1", "First"), ("2", "Second")]
        with patch.object(HTMLUtils, "parse_block_note", side_effect=side_effects):
            ProcessingUtils.process_block_notes(
                ["<p id='note-1'>First</p>", "<p id='note-2'>Second</p>"], notes
            )
        assert notes == {"1": "First", "2": "Second"}

    def test_skips_unparseable_notes(self):
        """Test that notes for which parse_block_note returns None are ignored."""
        notes = {}
        with patch.object(HTMLUtils, "parse_block_note", return_value=None):
            ProcessingUtils.process_block_notes(["<p>No id here</p>"], notes)
        assert not notes

    def test_does_not_overwrite_existing_note(self):
        """Test that a duplicate note number preserves the first value."""
        notes = {"1": "original"}
        with patch.object(
            HTMLUtils, "parse_block_note", return_value=("1", "duplicate")
        ):
            ProcessingUtils.process_block_notes(["<p id='note-1'>Duplicate</p>"], notes)
        assert notes["1"] == "original"

    def test_warns_on_duplicate_note_number(self, capsys):
        """Test that a message is printed to stderr when a duplicate note number is encountered."""
        notes = {"1": "original"}
        with patch.object(
            HTMLUtils, "parse_block_note", return_value=("1", "duplicate")
        ):
            ProcessingUtils.process_block_notes(["<p id='note-1'>Duplicate</p>"], notes)
        assert "Duplicate note number" in capsys.readouterr().err


class TestProcessEndNotes:
    """Tests for the process_end_notes function."""

    def test_returns_empty_list_for_empty_notes(self):
        """Test that an empty notes dict produces no output."""
        assert not ProcessingUtils.process_end_notes({}, "en")

    def test_english_locale_uses_notes_header(self):
        """Test that the English locale produces a 'Notes' section header."""
        result = ProcessingUtils.process_end_notes({"1": "<p>Text</p>"}, "en")
        assert "## Notes" in result

    def test_german_locale_uses_anmerkungen_header(self):
        """Test that a non-English locale produces an 'Anmerkungen' section header."""
        result = ProcessingUtils.process_end_notes({"1": "<p>Text</p>"}, "de")
        assert "## Anmerkungen" in result

    def test_includes_separator_line(self):
        """Test that the section starts with a horizontal rule."""
        result = ProcessingUtils.process_end_notes({"1": "<p>Text</p>"}, "en")
        assert result[0] == "---"

    def test_delegates_to_html_to_md(self):
        """Test that each note's HTML content is converted via HTMLUtils.html_to_md."""
        notes = {"1": "<p>Note one</p>"}
        with patch.object(HTMLUtils, "html_to_md", return_value="Note one") as mock:
            ProcessingUtils.process_end_notes(notes, "en")
        mock.assert_called_once_with("<p>Note one</p>")

    def test_note_line_uses_colon_pipe_format(self):
        """Test that each note line is formatted as [^N]: | <content>."""
        with patch.object(HTMLUtils, "html_to_md", return_value="Note text"):
            result = ProcessingUtils.process_end_notes({"3": "<p>Note</p>"}, "en")
        note_line = next(line for line in result if line.startswith("[^"))
        assert note_line == "[^3]: | Note text"

    def test_notes_sorted_numerically(self):
        """Test that notes are output in ascending numeric order."""
        notes = {"10": "<p>Ten</p>", "2": "<p>Two</p>", "1": "<p>One</p>"}
        result = ProcessingUtils.process_end_notes(notes, "en")
        note_lines = [line for line in result if line.startswith("[^")]
        assert note_lines[0].startswith("[^1]:")
        assert note_lines[1].startswith("[^2]:")
        assert note_lines[2].startswith("[^10]:")

    def test_each_note_followed_by_blank_line(self):
        """Test that each note entry is followed by a blank line."""
        result = ProcessingUtils.process_end_notes(
            {"1": "<p>A</p>", "2": "<p>B</p>"}, "en"
        )
        note_indices = [i for i, line in enumerate(result) if line.startswith("[^")]
        for idx in note_indices:
            assert result[idx + 1] == ""
