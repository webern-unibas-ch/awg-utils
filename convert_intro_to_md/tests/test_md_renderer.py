"""Tests for utils/md_renderer.py"""

from unittest.mock import patch

from utils.md_renderer import (
    _collect_note,
    render,
    _render_block,
    _render_blockquote,
    _render_cell_content,
    _render_inline,
    _render_inline_children,
    _render_list,
    _render_notes,
    _render_table,
    _render_table_row,
)
from utils.nodes import (
    Block,
    Blockquote,
    Bold,
    Cell,
    CrossRef,
    FootnoteRef,
    Italic,
    ListBlock,
    ListItem,
    Note,
    Paragraph,
    Ref,
    Row,
    Strikethrough,
    Superscript,
    Table,
    Text,
    Underline,
)


class TestRender:
    """Tests for the render function."""

    def _make_block(
        self,
        heading: list | None = None,
        content: list | None = None,
        notes: list | None = None,
    ) -> Block:
        return Block(
            id="block-1",
            heading=heading,
            content=content or [],
            notes=notes or [],
        )

    def test_empty_blocks_returns_only_newline(self):
        """Test that an empty block list returns a single newline."""
        assert render([], "de") == "\n"

    def test_output_ends_with_newline(self):
        """Test that the output always ends with a newline."""
        block = self._make_block(content=[Paragraph(children=[Text(value="x")])])
        assert render([block], "de").endswith("\n")

    def test_heading_renders_as_h2(self):
        """Test that a block heading is rendered as a level-2 Markdown heading."""
        block = self._make_block(heading=[Text(value="Title")])
        assert "## Title" in render([block], "de")

    def test_block_without_heading_has_no_h2(self):
        """Test that a block with no heading produces no ``##`` line."""
        block = self._make_block(content=[Paragraph(children=[Text(value="text")])])
        assert "## " not in render([block], "de")

    def test_content_node_appears_in_output(self):
        """Test that rendered block content appears in the output."""
        block = self._make_block(content=[Paragraph(children=[Text(value="hello")])])
        assert "hello" in render([block], "de")

    def test_empty_rendered_block_not_included(self):
        """Test that a block node rendering to an empty string is excluded from output."""
        block = self._make_block(content=[Paragraph(children=[])])
        with patch("utils.md_renderer._render_block", return_value="") as mock:
            result = render([block], "de")
        mock.assert_called_once()
        assert result == "\n"

    def test_notes_rendered_in_output(self):
        """Test that block notes appear as footnote definitions in the output."""
        note = Note(id="note-1", children=[Text(value="A footnote.")])
        block = self._make_block(notes=[note])
        assert "[^1]: | A footnote." in render([block], "de")

    def test_locale_passed_to_render_notes(self):
        """Test that the locale is forwarded to _render_notes."""
        with patch("utils.md_renderer._render_notes", return_value=[]) as mock:
            render([], "en")
        mock.assert_called_once_with({}, "en")

    def test_normalize_whitespace_is_called(self):
        """Test that ReplacementUtils.normalize_whitespace is applied to the joined lines."""
        with patch(
            "utils.md_renderer.ReplacementUtils.normalize_whitespace",
            return_value="",
        ) as mock:
            render([], "de")
        mock.assert_called_once()

    def test_separate_adjacent_tables_is_called(self):
        """Test that ReplacementUtils.separate_adjacent_tables is applied after normalization."""
        with patch(
            "utils.md_renderer.ReplacementUtils.separate_adjacent_tables",
            return_value="",
        ) as mock:
            render([], "de")
        mock.assert_called_once()


class TestCollectNote:
    """Tests for the _collect_note function."""

    def _make_note(self, note_id: str) -> Note:
        return Note(id=note_id, children=[Text(value="content")])

    def test_valid_id_inserts_note_into_dict(self):
        """Test that a note with a valid id is inserted under its parsed number."""
        notes: dict = {}
        note = self._make_note("note-3")
        _collect_note(note, notes)
        assert notes == {3: note}

    def test_multiple_notes_are_all_inserted(self):
        """Test that several distinct notes are each inserted under their own number."""
        notes: dict = {}
        note1, note2 = self._make_note("note-1"), self._make_note("note-2")
        _collect_note(note1, notes)
        _collect_note(note2, notes)
        assert notes == {1: note1, 2: note2}

    def test_duplicate_id_keeps_first_and_prints_warning(self, capsys):
        """Test that a duplicate note number keeps the first note and prints a warning."""
        notes: dict = {}
        first = Note(id="note-5", children=[Text(value="first content")])
        second = Note(id="note-5", children=[Text(value="second content")])
        _collect_note(first, notes)
        _collect_note(second, notes)
        assert notes[5] is first
        assert "Duplicate" in capsys.readouterr().err

    def test_unparseable_id_skips_note_and_prints_warning(self, capsys):
        """Test that a note whose id cannot be parsed is skipped with a warning."""
        notes: dict = {}
        _collect_note(self._make_note("note-abc"), notes)
        assert not notes
        assert "Could not parse" in capsys.readouterr().err

    def test_id_with_no_dash_skips_note_and_prints_warning(self, capsys):
        """Test that a note id with no ``-`` separator is skipped with a warning."""
        notes: dict = {}
        _collect_note(self._make_note("nonote"), notes)
        assert not notes
        assert "Could not parse" in capsys.readouterr().err

    def test_returns_none(self):
        """Test that _collect_note returns None on a successful insert."""
        assert _collect_note(self._make_note("note-1"), {}) is None


class TestRenderNotes:
    """Tests for the _render_notes function."""

    def _make_note(self, n: int, text: str) -> tuple[int, Note]:
        return n, Note(id=f"note-{n}", children=[Text(value=text)])

    def test_empty_notes_returns_empty_list(self):
        """Test that an empty notes dict returns an empty list."""
        assert not _render_notes({}, "de")

    def test_german_locale_uses_anmerkungen_header(self):
        """Test that a German locale produces a ``## Anmerkungen`` section header."""
        notes = dict([self._make_note(1, "Erste Anmerkung.")])
        lines = _render_notes(notes, "de")
        assert "## Anmerkungen" in lines

    def test_english_locale_uses_notes_header(self):
        """Test that a non-German locale produces a ``## Notes`` section header."""
        notes = dict([self._make_note(1, "First note.")])
        lines = _render_notes(notes, "en")
        assert "## Notes" in lines

    def test_starts_with_horizontal_rule(self):
        """Test that the section always starts with a ``---`` separator."""
        notes = dict([self._make_note(1, "Note text.")])
        assert _render_notes(notes, "de")[0] == "---"

    def test_note_content_rendered_via_render_inline_children(self):
        """Test that note children are passed to _render_inline_children."""
        notes = dict([self._make_note(1, "Note text.")])
        with patch(
            "utils.md_renderer._render_inline_children", return_value="Note text."
        ) as mock:
            _render_notes(notes, "de")
        mock.assert_called_once_with(notes[1].children)

    def test_note_is_formatted_as_footnote_definition(self):
        """Test that each note appears as a ``[^N]: | content`` line."""
        notes = dict([self._make_note(3, "Third note.")])
        lines = _render_notes(notes, "de")
        assert "[^3]: | Third note." in lines

    def test_notes_are_sorted_by_number(self):
        """Test that notes appear in ascending numeric order regardless of insertion order."""
        notes = dict(
            [
                self._make_note(3, "Third."),
                self._make_note(1, "First."),
                self._make_note(2, "Second."),
            ]
        )
        lines = _render_notes(notes, "de")
        note_lines = [line for line in lines if line.startswith("[^")]
        assert note_lines == ["[^1]: | First.", "[^2]: | Second.", "[^3]: | Third."]

    def test_each_note_is_followed_by_blank_line(self):
        """Test that a blank line follows each footnote definition."""
        notes = dict([self._make_note(1, "A."), self._make_note(2, "B.")])
        lines = _render_notes(notes, "de")
        for i, line in enumerate(lines):
            if line.startswith("[^"):
                assert lines[i + 1] == ""


class TestRenderBlock:
    """Tests for the _render_block function."""

    def test_paragraph_delegates_to_render_inline_children(self):
        """Test that a Paragraph node delegates to _render_inline_children."""
        node = Paragraph(children=[Text(value="")])
        with patch(
            "utils.md_renderer._render_inline_children",
            return_value="Some paragraph text.",
        ) as mock:
            result = _render_block(node)
        mock.assert_called_once_with(node.children)
        assert result == "Some paragraph text."

    def test_blockquote_delegates_to_render_blockquote(self):
        """Test that a Blockquote node delegates to _render_blockquote."""
        node = Blockquote(paragraphs=[])
        with patch(
            "utils.md_renderer._render_blockquote", return_value="> Quoted text."
        ) as mock:
            result = _render_block(node)
        mock.assert_called_once_with(node)
        assert result == "> Quoted text."

    def test_list_block_delegates_to_render_list(self):
        """Test that a ListBlock node delegates to _render_list."""
        node = ListBlock(items=[], ordered=False)
        with patch(
            "utils.md_renderer._render_list", return_value="- item one\n- item two"
        ) as mock:
            result = _render_block(node)
        mock.assert_called_once_with(node)
        assert result == "- item one\n- item two"

    def test_table_delegates_to_render_table(self):
        """Test that a Table node delegates to _render_table."""
        node = Table(rows=[])
        with patch(
            "utils.md_renderer._render_table", return_value="| H |\n| --- |\n| D |"
        ) as mock:
            result = _render_block(node)
        mock.assert_called_once_with(node)
        assert result == "| H |\n| --- |\n| D |"

    def test_unknown_node_delegates_to_render_inline(self):
        """Test that an unrecognised node falls back to _render_inline."""
        node = Text(value="x")
        with patch(
            "utils.md_renderer._render_inline", return_value="inline text"
        ) as mock:
            result = _render_block(node)
        mock.assert_called_once_with(node)
        assert result == "inline text"


class TestRenderInline:
    """Tests for the _render_inline function."""

    def test_italic_delegates_to_inline_children_and_wraps(self):
        """Test that Italic wraps delegated content in ``*``."""
        node = Italic(children=[Text(value="")])
        with patch(
            "utils.md_renderer._render_inline_children", return_value="x"
        ) as mock:
            result = _render_inline(node)
        mock.assert_called_once_with(node.children)
        assert result == "*x*"

    def test_bold_delegates_to_inline_children_and_wraps(self):
        """Test that Bold wraps delegated content in ``**``."""
        node = Bold(children=[Text(value="")])
        with patch(
            "utils.md_renderer._render_inline_children", return_value="y"
        ) as mock:
            result = _render_inline(node)
        mock.assert_called_once_with(node.children)
        assert result == "**y**"

    def test_strikethrough_wraps_with_tildes(self):
        """Test that Strikethrough wraps delegated content in ``~~``."""
        node = Strikethrough(children=[Text(value="")])
        with patch("utils.md_renderer._render_inline_children", return_value="s"):
            result = _render_inline(node)
        assert result == "~~s~~"

    def test_underline_wraps_with_u_tags(self):
        """Test that Underline wraps delegated content in ``<u>``/``</u>``."""
        node = Underline(children=[Text(value="")])
        with patch("utils.md_renderer._render_inline_children", return_value="u"):
            result = _render_inline(node)
        assert result == "<u>u</u>"

    def test_superscript_wraps_with_sup_tags(self):
        """Test that Superscript wraps delegated content in ``<sup>``/``</sup>``."""
        node = Superscript(children=[Text(value="")])
        with patch("utils.md_renderer._render_inline_children", return_value="s"):
            result = _render_inline(node)
        assert result == "<sup>s</sup>"

    def test_paragraph_delegates_with_empty_wrap(self):
        """Test that a Paragraph node passes through its content without wrapping."""
        node = Paragraph(children=[Text(value="")])
        with patch(
            "utils.md_renderer._render_inline_children", return_value="p"
        ) as mock:
            result = _render_inline(node)
        mock.assert_called_once_with(node.children)
        assert result == "p"

    def test_text_returns_value(self):
        """Test that a Text node returns its plain value."""
        assert _render_inline(Text(value="hello")) == "hello"

    def test_text_replaces_nbsp(self):
        """Test that non-breaking spaces in Text values are replaced with regular spaces."""
        assert _render_inline(Text(value="a\xa0b")) == "a b"

    def test_footnote_ref_renders_as_caret_notation(self):
        """Test that FootnoteRef renders as ``[^N]``."""
        assert _render_inline(FootnoteRef(n=5)) == "[^5]"

    def test_cross_ref_renders_as_anchor_link(self):
        """Test that CrossRef renders as ``[N](#fn:N)``."""
        assert _render_inline(CrossRef(n=3)) == "[3](#fn:3)"

    def test_ref_delegates_children_and_uses_target(self):
        """Test that Ref wraps delegated children text in a Markdown link."""
        node = Ref(target="https://example.com", children=[Text(value="")])
        with patch(
            "utils.md_renderer._render_inline_children", return_value="label"
        ) as mock:
            result = _render_inline(node)
        mock.assert_called_once_with(node.children)
        assert result == "[label](https://example.com)"

    def test_table_inline_returns_empty_string(self):
        """Test that a Table node used inline returns an empty string."""
        assert _render_inline(Table(rows=[])) == ""

    def test_blockquote_inline_joins_paragraphs_with_space(self):
        """Test that a Blockquote used inline joins its paragraphs with a space."""
        node = Blockquote(paragraphs=[Paragraph(children=[]), Paragraph(children=[])])
        with patch(
            "utils.md_renderer._render_inline_children", side_effect=["p1", "p2"]
        ):
            result = _render_inline(node)
        assert result == "p1 p2"

    def test_list_block_inline_joins_items_with_space(self):
        """Test that a ListBlock used inline joins its items with a space."""
        node = ListBlock(
            items=[ListItem(children=[]), ListItem(children=[])], ordered=False
        )
        with patch("utils.md_renderer._render_inline_children", side_effect=["a", "b"]):
            result = _render_inline(node)
        assert result == "a b"


class TestRenderInlineChildren:
    """Tests for the _render_inline_children function."""

    def test_empty_list_returns_empty_string(self):
        """Test that an empty children list returns an empty string."""
        assert _render_inline_children([]) == ""

    def test_delegates_each_node_to_render_inline(self):
        """Test that _render_inline is called once per child node."""
        nodes = [Text(value="a"), Text(value="b")]
        with patch("utils.md_renderer._render_inline", return_value="x") as mock:
            result = _render_inline_children(nodes)
        assert mock.call_count == 2
        assert result == "xx"

    def test_single_node_delegates_once(self):
        """Test that a single child causes exactly one _render_inline call."""
        nodes = [Text(value="x")]
        with patch("utils.md_renderer._render_inline", return_value="y") as mock:
            result = _render_inline_children(nodes)
        mock.assert_called_once_with(nodes[0])
        assert result == "y"

    def test_results_are_concatenated_in_order(self):
        """Test that the return values from _render_inline are joined in order."""
        nodes = [Text(value=""), Text(value=""), Text(value="")]
        with patch(
            "utils.md_renderer._render_inline", side_effect=["first", "second", "third"]
        ):
            result = _render_inline_children(nodes)
        assert result == "firstsecondthird"


class TestRenderBlockquote:
    """Tests for the _render_blockquote function."""

    def _make_para(self, *texts: str) -> Paragraph:
        return Paragraph(children=[Text(value=t) for t in texts])

    def test_single_paragraph_is_prefixed_with_gt(self):
        """Test that a single paragraph is rendered with a ``> `` prefix."""
        node = Blockquote(paragraphs=[self._make_para("hello")])
        assert _render_blockquote(node) == "> hello"

    def test_multiple_paragraphs_are_joined_by_blank_gt_line(self):
        """Test that multiple paragraphs are separated by a ``>`` line on its own."""
        node = Blockquote(
            paragraphs=[self._make_para("first"), self._make_para("second")]
        )
        assert _render_blockquote(node) == "> first\n>\n> second"

    def test_each_paragraph_prefixed_independently(self):
        """Test that every paragraph in the blockquote gets its own ``> `` prefix."""
        node = Blockquote(
            paragraphs=[
                self._make_para("a"),
                self._make_para("b"),
                self._make_para("c"),
            ]
        )
        lines = _render_blockquote(node).splitlines()
        content_lines = [line for line in lines if line != ">"]
        assert all(line.startswith("> ") for line in content_lines)

    def test_paragraph_children_are_concatenated(self):
        """Test that multiple children within one paragraph are concatenated."""
        node = Blockquote(paragraphs=[self._make_para("foo", "bar")])
        assert _render_blockquote(node) == "> foobar"

    def test_empty_blockquote_returns_empty_string(self):
        """Test that a blockquote with no paragraphs returns an empty string."""
        node = Blockquote(paragraphs=[])
        assert _render_blockquote(node) == ""


class TestRenderList:
    """Tests for the _render_list function."""

    def test_unordered_list_items_are_prefixed_with_dash(self):
        """Test that each unordered list item is rendered with a '- ' prefix."""
        node = ListBlock(
            items=[
                ListItem(children=[Text(value="a")]),
                ListItem(children=[Text(value="b")]),
            ],
            ordered=False,
        )
        result = _render_list(node)
        assert result == "- a\n- b"

    def test_ordered_list_items_are_prefixed_with_number(self):
        """Test that each ordered list item is rendered with a '1. ', '2. ', ... prefix."""
        node = ListBlock(
            items=[
                ListItem(children=[Text(value="first")]),
                ListItem(children=[Text(value="second")]),
            ],
            ordered=True,
        )
        result = _render_list(node)
        assert result == "1. first\n2. second"

    def test_list_items_are_joined_with_newline(self):
        """Test that list items are joined by newlines with no trailing newline."""
        node = ListBlock(
            items=[
                ListItem(children=[Text(value="x")]),
                ListItem(children=[Text(value="y")]),
                ListItem(children=[Text(value="z")]),
            ],
            ordered=False,
        )
        result = _render_list(node)
        assert result.count("\n") == 2

    def test_list_item_children_rendered_via_render_inline_children(self):
        """Test that each item's children are passed to _render_inline_children."""
        sentinel = "RENDERED"
        node = ListBlock(
            items=[ListItem(children=[Text(value="x")])],
            ordered=False,
        )
        with patch(
            "utils.md_renderer._render_inline_children", return_value=sentinel
        ) as mock:
            result = _render_list(node)
        mock.assert_called_once()
        assert sentinel in result

    def test_empty_unordered_list_returns_empty_string(self):
        """Test that an unordered list with no items returns an empty string."""
        node = ListBlock(items=[], ordered=False)
        assert _render_list(node) == ""

    def test_empty_ordered_list_returns_empty_string(self):
        """Test that an ordered list with no items returns an empty string."""
        node = ListBlock(items=[], ordered=True)
        assert _render_list(node) == ""


class TestRenderTable:
    """Tests for the _render_table function."""

    def _make_row(
        self, *texts: str, is_header: bool = False, gap_before: bool = False
    ) -> Row:
        return Row(
            cells=[Cell(children=[Text(value=t)]) for t in texts],
            is_header=is_header,
            gap_before=gap_before,
        )

    def test_empty_table_returns_empty_string(self):
        """Test that a table with no rows returns an empty string."""
        assert _render_table(Table(rows=[])) == ""

    def test_all_empty_cell_rows_returns_empty_string(self):
        """Test that rows with no cells are filtered out, leaving an empty table."""
        assert _render_table(Table(rows=[Row(cells=[])])) == ""

    def test_delegates_row_rendering_to_render_table_row(self):
        """Test that _render_table calls _render_table_row for each row."""
        table = Table(rows=[self._make_row("A", "B")])
        with patch(
            "utils.md_renderer._render_table_row", return_value="| MOCK |"
        ) as mock:
            _render_table(table)
        mock.assert_called_once()

    def test_header_row_is_followed_by_separator(self):
        """Test that a header row is immediately followed by the ``---`` separator line."""
        table = Table(
            rows=[
                self._make_row("H1", "H2", is_header=True),
                self._make_row("D1", "D2"),
            ]
        )
        lines = _render_table(table).splitlines()
        assert "---" in lines[1]

    def test_non_header_table_gets_blank_header_row(self):
        """Test that a table with no header row gets a blank header row prepended."""
        table = Table(rows=[self._make_row("A", "B")])
        lines = _render_table(table).splitlines()
        # first line is the blank header, second is separator
        assert all(char in (" ", "|") for char in lines[0])
        assert "---" in lines[1]

    def test_gap_before_inserts_empty_row(self):
        """Test that ``gap_before=True`` inserts a blank row before the marked row."""
        table = Table(rows=[self._make_row("A"), self._make_row("B", gap_before=True)])
        lines = _render_table(table).splitlines()
        # lines: blank_header, separator, row-A, empty-gap, row-B
        empty_line = next(
            line
            for line in lines
            if all(char in (" ", "|") for char in line)
            and "A" not in line
            and "B" not in line
            and "---" not in line
        )
        assert empty_line is not None

    def test_separator_has_correct_column_count(self):
        """Test that the separator row contains exactly as many ``---`` segments as columns."""
        table = Table(rows=[self._make_row("A", "B", "C")])
        lines = _render_table(table).splitlines()
        sep = next(line for line in lines if "---" in line)
        assert sep.count("---") == 3

    def test_output_row_count_with_header(self):
        """Test that a header table with N data rows produces N+2 lines (header, sep, data…)."""
        table = Table(
            rows=[
                self._make_row("H", is_header=True),
                self._make_row("R1"),
                self._make_row("R2"),
            ]
        )
        lines = _render_table(table).splitlines()
        assert len(lines) == 4  # header + sep + 2 data rows

    def test_output_row_count_without_header(self):
        """Test that a non-header table with N rows produces N+2 lines (blank_hdr, sep, rows…)."""
        table = Table(rows=[self._make_row("R1"), self._make_row("R2")])
        lines = _render_table(table).splitlines()
        assert len(lines) == 4  # blank_header + sep + 2 rows


class TestRenderTableRow:
    """Tests for the _render_table_row function."""

    def _make_cell(
        self, text: str, colspan: int | None = None, indent: bool = False
    ) -> Cell:
        return Cell(children=[Text(value=text)], colspan=colspan, indent=indent)

    def test_single_cell_fills_all_columns(self):
        """Test that a single cell spanning all columns produces a row of the right width."""
        row = Row(cells=[self._make_cell("A", colspan=3)])
        result = _render_table_row(row, num_cols=3)
        assert result.count("|") == 4  # leading + 3 column separators

    def test_single_full_width_cell_no_text_center_places_content_first(self):
        """Test that without text_center, full-width content appears in the first column."""
        row = Row(cells=[self._make_cell("X", colspan=3)], text_center=False)
        result = _render_table_row(row, num_cols=3)
        assert result == "| X | | |"

    def test_single_full_width_cell_text_center_odd_cols_places_content_in_middle(self):
        """Test that text_center + odd column count centres the content."""
        row = Row(cells=[self._make_cell("C", colspan=3)], text_center=True)
        result = _render_table_row(row, num_cols=3)
        assert result == "| | C | |"

    def test_single_full_width_cell_text_center_even_cols_places_content_first(self):
        """Test that text_center with an even column count falls back to first column."""
        row = Row(cells=[self._make_cell("C", colspan=2)], text_center=True)
        result = _render_table_row(row, num_cols=2)
        assert result == "| C | |"

    def test_multiple_cells_rendered_in_order(self):
        """Test that multiple cells are rendered left-to-right."""
        row = Row(
            cells=[self._make_cell("A"), self._make_cell("B"), self._make_cell("C")]
        )
        result = _render_table_row(row, num_cols=3)
        assert result == "| A | B | C |"

    def test_colspan_expands_to_empty_filler_columns(self):
        """Test that a colspan > 1 inserts blank filler cells."""
        row = Row(cells=[self._make_cell("Wide", colspan=2), self._make_cell("N")])
        result = _render_table_row(row, num_cols=3)
        assert result == "| Wide | | N |"

    def test_short_row_is_padded_to_num_cols(self):
        """Test that rows with fewer cells than num_cols are padded with blank cells."""
        row = Row(cells=[self._make_cell("only")])
        result = _render_table_row(row, num_cols=3)
        assert result == "| only | | |"

    def test_row_starts_and_ends_with_pipe(self):
        """Test that the rendered row always starts and ends with ``|``."""
        row = Row(cells=[self._make_cell("v")])
        result = _render_table_row(row, num_cols=1)
        assert result.startswith("|")
        assert result.endswith("|")


class TestRenderCellContent:
    """Tests for the _render_cell_content function."""

    def test_plain_text_is_returned_unchanged(self):
        """Test that a cell with plain text is returned as-is."""
        cell = Cell(children=[Text(value="hello")])
        assert _render_cell_content(cell) == "hello"

    def test_pipe_character_is_escaped(self):
        r"""Test that a pipe character in the content is escaped as ``\|``."""
        cell = Cell(children=[Text(value="a | b")])
        assert _render_cell_content(cell) == r"a \| b"

    def test_multiple_pipe_characters_are_all_escaped(self):
        """Test that every pipe in the content is escaped."""
        cell = Cell(children=[Text(value="a | b | c")])
        assert _render_cell_content(cell) == r"a \| b \| c"

    def test_indent_true_adds_ensp_prefix(self):
        """Test that ``indent=True`` prepends ``&ensp;&ensp;`` to the content."""
        cell = Cell(children=[Text(value="indented")], indent=True)
        assert _render_cell_content(cell) == "&ensp;&ensp;indented"

    def test_indent_false_adds_no_prefix(self):
        """Test that ``indent=False`` produces no prefix."""
        cell = Cell(children=[Text(value="normal")], indent=False)
        assert _render_cell_content(cell) == "normal"

    def test_indent_with_pipe_escapes_after_prefix(self):
        """Test that pipe escaping is applied after the indent prefix."""
        cell = Cell(children=[Text(value="a | b")], indent=True)
        assert _render_cell_content(cell) == r"&ensp;&ensp;a \| b"

    def test_empty_children_returns_empty_string(self):
        """Test that a cell with no children returns an empty string."""
        cell = Cell(children=[])
        assert _render_cell_content(cell) == ""

    def test_empty_children_with_indent_returns_only_prefix(self):
        """Test that an indented cell with no children returns only the prefix."""
        cell = Cell(children=[], indent=True)
        assert _render_cell_content(cell) == "&ensp;&ensp;"
