"""Tests for utils/tei_renderer.py"""

import xml.etree.ElementTree as ET
from unittest.mock import patch

from utils.tei_renderer import (
    _INLINE_WRAP,
    _render_blockquote,
    _render_cell,
    _render_cross_ref,
    _render_footnote_ref,
    _render_inline_node,
    _render_list_block,
    _render_node,
    _render_ref,
    _render_row,
    _render_table,
    _tei,
    _xml,
)
from utils.nodes import (
    Bold,
    Blockquote,
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


class TestRenderNode:
    """Tests for the _render_node dispatch function."""

    def test_text_delegates_to_append_text(self):
        """Text node calls _append_text."""
        parent = ET.Element("root")
        with patch("utils.tei_renderer._append_text") as mock:
            _render_node(Text(value="hi"), parent, {})
        mock.assert_called_once_with(parent, "hi")

    def test_footnote_ref_delegates_to_render_footnote_ref(self):
        """FootnoteRef node calls _render_footnote_ref."""
        parent = ET.Element("root")
        node = FootnoteRef(n=1)
        with patch("utils.tei_renderer._render_footnote_ref") as mock:
            _render_node(node, parent, {})
        mock.assert_called_once_with(node, parent, {})

    def test_cross_ref_delegates_to_render_cross_ref(self):
        """CrossRef node calls _render_cross_ref."""
        parent = ET.Element("root")
        node = CrossRef(n=2)
        with patch("utils.tei_renderer._render_cross_ref") as mock:
            _render_node(node, parent, {})
        mock.assert_called_once_with(node, parent)

    def test_ref_delegates_to_render_ref(self):
        """Ref node calls _render_ref."""
        parent = ET.Element("root")
        node = Ref(target="https://example.com")
        with patch("utils.tei_renderer._render_ref") as mock:
            _render_node(node, parent, {})
        mock.assert_called_once_with(node, parent, {})

    def test_inline_wrap_type_delegates_to_render_inline_node(self):
        """Every type in _INLINE_WRAP calls _render_inline_node."""
        for node_type in _INLINE_WRAP:
            parent = ET.Element("root")
            node = node_type(children=[])
            with patch("utils.tei_renderer._render_inline_node") as mock:
                _render_node(node, parent, {})
            mock.assert_called_once_with(node, parent, {})

    def test_blockquote_delegates_to_render_blockquote(self):
        """Blockquote node calls _render_blockquote."""
        parent = ET.Element("root")
        node = Blockquote()
        with patch("utils.tei_renderer._render_blockquote") as mock:
            _render_node(node, parent, {})
        mock.assert_called_once_with(node, parent, {})

    def test_list_block_delegates_to_render_list_block(self):
        """ListBlock node calls _render_list_block."""
        parent = ET.Element("root")
        node = ListBlock()
        with patch("utils.tei_renderer._render_list_block") as mock:
            _render_node(node, parent, {})
        mock.assert_called_once_with(node, parent, {})

    def test_table_delegates_to_render_table(self):
        """Table node calls _render_table."""
        parent = ET.Element("root")
        node = Table()
        with patch("utils.tei_renderer._render_table") as mock:
            _render_node(node, parent, {})
        mock.assert_called_once_with(node, parent, {})


class TestRenderInlineNode:
    """Tests for the _render_inline_node function."""

    def setup_method(self):
        """Set up a fresh parent element for each test."""
        self.parent = ET.Element("root")  # pylint: disable=attribute-defined-outside-init

    def test_italic_creates_hi_with_rend_italic(self):
        """Italic → <hi rend="italic">."""
        _render_inline_node(Italic(children=[]), self.parent, {})
        el = list(self.parent)[0]
        assert el.tag == _tei("hi")
        assert el.get("rend") == "italic"

    def test_bold_creates_hi_with_rend_bold(self):
        """Bold → <hi rend="bold">."""
        _render_inline_node(Bold(children=[]), self.parent, {})
        el = list(self.parent)[0]
        assert el.tag == _tei("hi")
        assert el.get("rend") == "bold"

    def test_underline_creates_hi_with_rend_underline(self):
        """Underline → <hi rend="underline">."""
        _render_inline_node(Underline(children=[]), self.parent, {})
        el = list(self.parent)[0]
        assert el.tag == _tei("hi")
        assert el.get("rend") == "underline"

    def test_superscript_creates_hi_with_rend_sup(self):
        """Superscript → <hi rend="sup">."""
        _render_inline_node(Superscript(children=[]), self.parent, {})
        el = list(self.parent)[0]
        assert el.tag == _tei("hi")
        assert el.get("rend") == "sup"

    def test_strikethrough_creates_del_without_rend(self):
        """Strikethrough → <del> with no rend attribute."""
        _render_inline_node(Strikethrough(children=[]), self.parent, {})
        el = list(self.parent)[0]
        assert el.tag == _tei("del")
        assert el.get("rend") is None

    def test_paragraph_creates_p_without_rend(self):
        """Paragraph → <p> with no rend attribute."""
        _render_inline_node(Paragraph(children=[]), self.parent, {})
        el = list(self.parent)[0]
        assert el.tag == _tei("p")
        assert el.get("rend") is None

    def test_all_inline_wrap_types_covered(self):
        """Every type in _INLINE_WRAP is exercised without error."""
        instances = [
            Italic(children=[]),
            Bold(children=[]),
            Strikethrough(children=[]),
            Underline(children=[]),
            Superscript(children=[]),
            Paragraph(children=[]),
        ]
        assert len(instances) == len(_INLINE_WRAP)
        for node in instances:
            _render_inline_node(node, self.parent, {})  # must not raise

    def test_delegates_children_to_render_node(self):
        """Calls _render_node once per child."""
        children = [Text(value="a"), Text(value="b")]
        with patch("utils.tei_renderer._render_node") as mock_render:
            _render_inline_node(Italic(children=children), self.parent, {})
        assert mock_render.call_count == 2

    def test_passes_created_element_to_render_node(self):
        """Passes the new element (not the parent) to _render_node."""
        child = Text(value="x")
        with patch("utils.tei_renderer._render_node") as mock_render:
            _render_inline_node(Bold(children=[child]), self.parent, {})
        created_el = list(self.parent)[0]
        mock_render.assert_called_once_with(child, created_el, {})


class TestRenderBlockquote:
    """Tests for the _render_blockquote function."""

    def setup_method(self):
        """Set up a fresh parent element for each test."""
        self.parent = ET.Element("root")  # pylint: disable=attribute-defined-outside-init

    def test_creates_quote_element(self):
        """Creates a <quote> child on the parent."""
        _render_blockquote(Blockquote(paragraphs=[]), self.parent, {})
        children = list(self.parent)
        assert len(children) == 1
        assert children[0].tag == _tei("quote")

    def test_creates_l_element_per_paragraph(self):
        """Creates one <l> child per paragraph inside the <quote>."""
        node = Blockquote(paragraphs=[Paragraph(), Paragraph(), Paragraph()])
        _render_blockquote(node, self.parent, {})
        quote_el = list(self.parent)[0]
        l_els = list(quote_el)
        assert len(l_els) == 3
        assert all(el.tag == _tei("l") for el in l_els)

    def test_delegates_para_children_to_render_node(self):
        """Calls _render_node once per child across all paragraphs."""
        children = [Text(value="a"), Text(value="b")]
        node = Blockquote(paragraphs=[Paragraph(children=children)])
        with patch("utils.tei_renderer._render_node") as mock_render:
            _render_blockquote(node, self.parent, {})
        assert mock_render.call_count == 2

    def test_passes_l_element_to_render_node(self):
        """Passes the <l> element (not the parent) to _render_node."""
        child = Text(value="text")
        node = Blockquote(paragraphs=[Paragraph(children=[child])])
        with patch("utils.tei_renderer._render_node") as mock_render:
            _render_blockquote(node, self.parent, {})
        l_el = list(list(self.parent)[0])[0]
        mock_render.assert_called_once_with(child, l_el, {})

    def test_empty_paragraphs(self):
        """Renders a <quote> with no paragraphs without error."""
        _render_blockquote(Blockquote(paragraphs=[]), self.parent, {})  # must not raise
        assert not list(list(self.parent)[0])


class TestRenderCrossRef:
    """Tests for the _render_cross_ref function."""

    def setup_method(self):
        """Set up a fresh parent element for each test."""
        self.parent = ET.Element("root")  # pylint: disable=attribute-defined-outside-init

    def test_creates_ref_element(self):
        """Creates a <ref> child on the parent."""
        _render_cross_ref(CrossRef(n=1), self.parent)
        children = list(self.parent)
        assert len(children) == 1
        assert children[0].tag == _tei("ref")

    def test_sets_target_to_note_fragment(self):
        """Sets target to '#note-N'."""
        _render_cross_ref(CrossRef(n=4), self.parent)
        assert list(self.parent)[0].get("target") == "#note-4"

    def test_sets_text_to_n_as_string(self):
        """Sets element text to the string form of node.n."""
        _render_cross_ref(CrossRef(n=7), self.parent)
        assert list(self.parent)[0].text == "7"

    def test_no_extra_attributes(self):
        """Sets only the target attribute, no others."""
        _render_cross_ref(CrossRef(n=1), self.parent)
        assert list(list(self.parent)[0].attrib.keys()) == ["target"]


class TestRenderFootnoteRef:
    """Tests for the _render_footnote_ref function."""

    def setup_method(self):
        """Set up a fresh parent element for each test."""
        self.parent = ET.Element("root")  # pylint: disable=attribute-defined-outside-init

    def test_creates_note_element(self):
        """Creates a <note> child on the parent."""
        _render_footnote_ref(FootnoteRef(n=1), self.parent, {})
        children = list(self.parent)
        assert len(children) == 1
        assert children[0].tag == _tei("note")

    def test_sets_place_end(self):
        """Sets place="end" on the <note> element."""
        _render_footnote_ref(FootnoteRef(n=1), self.parent, {})
        assert list(self.parent)[0].get("place") == "end"

    def test_sets_n_attribute(self):
        """Sets n to the string form of node.n."""
        _render_footnote_ref(FootnoteRef(n=3), self.parent, {})
        assert list(self.parent)[0].get("n") == "3"

    def test_sets_xml_id_attribute(self):
        """Sets xml:id to 'note-N'."""
        _render_footnote_ref(FootnoteRef(n=5), self.parent, {})
        assert list(self.parent)[0].get(_xml("id")) == "note-5"

    def test_no_children_when_note_absent_from_lookup(self):
        """Produces an empty <note> when n is not in lookup."""
        _render_footnote_ref(FootnoteRef(n=1), self.parent, {})
        assert not list(list(self.parent)[0])

    def test_delegates_note_children_to_render_node(self):
        """Calls _render_node once per child of the looked-up Note."""
        child = Text(value="body")
        note = Note(id="note-2", children=[child])
        lookup = {2: note}
        with patch("utils.tei_renderer._render_node") as mock_render:
            _render_footnote_ref(FootnoteRef(n=2), self.parent, lookup)
        assert mock_render.call_count == 1

    def test_passes_note_element_to_render_node(self):
        """Passes the <note> element (not the parent) to _render_node."""
        child = Text(value="body")
        note = Note(id="note-7", children=[child])
        lookup = {7: note}
        with patch("utils.tei_renderer._render_node") as mock_render:
            _render_footnote_ref(FootnoteRef(n=7), self.parent, lookup)
        note_el = list(self.parent)[0]
        mock_render.assert_called_once_with(child, note_el, lookup)


class TestRenderListBlock:
    """Tests for the _render_list_block function."""

    def test_creates_list_element(self):
        """Creates a <list> child on the parent."""
        parent = ET.Element("root")
        node = ListBlock(items=[])
        _render_list_block(node, parent, {})
        children = list(parent)
        assert len(children) == 1
        assert children[0].tag == _tei("list")

    def test_unordered_list_has_no_rend_attribute(self):
        """Does not set rend when ordered=False."""
        parent = ET.Element("root")
        node = ListBlock(items=[], ordered=False)
        _render_list_block(node, parent, {})
        assert list(parent)[0].get("rend") is None

    def test_ordered_list_sets_rend_ordered(self):
        """Sets rend="ordered" when ordered=True."""
        parent = ET.Element("root")
        node = ListBlock(items=[], ordered=True)
        _render_list_block(node, parent, {})
        assert list(parent)[0].get("rend") == "ordered"

    def test_creates_item_element_per_list_item(self):
        """Creates one <item> child per entry in node.items."""
        parent = ET.Element("root")
        node = ListBlock(items=[ListItem(), ListItem(), ListItem()])
        _render_list_block(node, parent, {})
        list_el = list(parent)[0]
        item_els = list(list_el)
        assert len(item_els) == 3
        assert all(el.tag == _tei("item") for el in item_els)

    def test_delegates_item_children_to_render_node(self):
        """Calls _render_node once per child across all items."""
        parent = ET.Element("root")
        children = [Text(value="a"), Text(value="b")]
        node = ListBlock(items=[ListItem(children=children)])
        with patch("utils.tei_renderer._render_node") as mock_render:
            _render_list_block(node, parent, {})
        assert mock_render.call_count == 2

    def test_passes_item_element_to_render_node(self):
        """Passes the <item> element (not the parent) to _render_node."""
        parent = ET.Element("root")
        child = Text(value="text")
        node = ListBlock(items=[ListItem(children=[child])])
        with patch("utils.tei_renderer._render_node") as mock_render:
            _render_list_block(node, parent, {})
        item_el = list(list(parent)[0])[0]
        mock_render.assert_called_once_with(child, item_el, {})


class TestRenderRef:
    """Tests for the _render_ref function."""

    def test_creates_ref_element(self):
        """Creates a <ref> child on the parent."""
        parent = ET.Element("root")
        node = Ref(target="https://example.com", children=[])
        _render_ref(node, parent, {})
        children = list(parent)
        assert len(children) == 1
        assert children[0].tag == _tei("ref")

    def test_sets_target_attribute(self):
        """Sets the target attribute from node.target."""
        parent = ET.Element("root")
        node = Ref(target="https://example.com", children=[])
        _render_ref(node, parent, {})
        assert list(parent)[0].get("target") == "https://example.com"

    def test_no_extra_attributes(self):
        """Sets only the target attribute, no others."""
        parent = ET.Element("root")
        node = Ref(target="https://example.com", children=[])
        _render_ref(node, parent, {})
        assert list(list(parent)[0].attrib.keys()) == ["target"]

    def test_delegates_children_to_render_node(self):
        """Calls _render_node once per child."""
        parent = ET.Element("root")
        children = [Text(value="click"), Text(value=" here")]
        node = Ref(target="https://example.com", children=children)
        with patch("utils.tei_renderer._render_node") as mock_render:
            _render_ref(node, parent, {})
        assert mock_render.call_count == 2

    def test_passes_ref_element_to_render_node(self):
        """Passes the <ref> element (not the parent) to _render_node."""
        parent = ET.Element("root")
        child = Text(value="link")
        node = Ref(target="https://example.com", children=[child])
        with patch("utils.tei_renderer._render_node") as mock_render:
            _render_ref(node, parent, {})
        ref_el = list(parent)[0]
        mock_render.assert_called_once_with(child, ref_el, {})

    def test_empty_children(self):
        """Renders a <ref> with no children without error."""
        parent = ET.Element("root")
        node = Ref(target="https://example.com", children=[])
        _render_ref(node, parent, {})  # must not raise
        assert list(parent)[0].tag == _tei("ref")


class TestRenderTable:
    """Tests for the _render_table function."""

    def _make_table(self, n: int = 1) -> Table:
        return Table(rows=[Row(cells=[]) for _ in range(n)])

    def test_creates_table_child_element(self):
        """Test that a ``<table>`` element is appended to the parent."""
        parent = ET.Element("div")
        with patch("utils.tei_renderer._render_row"):
            _render_table(self._make_table(), parent, {})
        assert len(list(parent)) == 1
        assert list(parent)[0].tag == _tei("table")

    def test_delegates_each_row_to_render_row(self):
        """Test that _render_row is called once for each row."""
        parent = ET.Element("div")
        with patch("utils.tei_renderer._render_row") as mock:
            _render_table(self._make_table(n=3), parent, {})
        assert mock.call_count == 3

    def test_empty_table_delegates_no_calls(self):
        """Test that a table with no rows makes no _render_row calls."""
        parent = ET.Element("div")
        with patch("utils.tei_renderer._render_row") as mock:
            _render_table(Table(rows=[]), parent, {})
        mock.assert_not_called()

    def test_returns_none(self):
        """Test that _render_table returns None."""
        parent = ET.Element("div")
        with patch("utils.tei_renderer._render_row"):
            assert _render_table(self._make_table(), parent, {}) is None


class TestRenderRow:
    """Tests for the _render_row function."""

    def _make_row(self, n: int = 1, is_header: bool = False) -> Row:
        return Row(cells=[Cell(children=[]) for _ in range(n)], is_header=is_header)

    def test_creates_row_child_element(self):
        """Test that a ``<row>`` element is appended to the parent."""
        parent = ET.Element("table")
        with patch("utils.tei_renderer._render_cell"):
            _render_row(self._make_row(), parent, {})
        assert len(list(parent)) == 1
        assert list(parent)[0].tag == _tei("row")

    def test_non_header_row_has_no_role_attribute(self):
        """Test that a non-header row does not receive a ``role`` attribute."""
        parent = ET.Element("table")
        with patch("utils.tei_renderer._render_cell"):
            _render_row(self._make_row(is_header=False), parent, {})
        assert "role" not in list(parent)[0].attrib

    def test_header_row_sets_role_label(self):
        """Test that a header row receives ``role="label"``."""
        parent = ET.Element("table")
        with patch("utils.tei_renderer._render_cell"):
            _render_row(self._make_row(is_header=True), parent, {})
        assert list(parent)[0].get("role") == "label"

    def test_delegates_each_cell_to_render_cell(self):
        """Test that _render_cell is called once for each cell."""
        parent = ET.Element("table")
        with patch("utils.tei_renderer._render_cell") as mock:
            _render_row(self._make_row(n=3), parent, {})
        assert mock.call_count == 3

    def test_empty_row_delegates_no_calls(self):
        """Test that a row with no cells makes no _render_cell calls."""
        parent = ET.Element("table")
        with patch("utils.tei_renderer._render_cell") as mock:
            _render_row(Row(cells=[]), parent, {})
        mock.assert_not_called()

    def test_returns_none(self):
        """Test that _render_row returns None."""
        parent = ET.Element("table")
        with patch("utils.tei_renderer._render_cell"):
            assert _render_row(self._make_row(), parent, {}) is None


class TestRenderCell:
    """Tests for the _render_cell function."""

    def _make_cell(self, n: int = 1, colspan: int | None = None) -> Cell:
        return Cell(children=[Text(value="x") for _ in range(n)], colspan=colspan)

    def test_creates_cell_child_element(self):
        """Test that a ``<cell>`` element is appended to the parent."""
        parent = ET.Element("row")
        with patch("utils.tei_renderer._render_node"):
            _render_cell(self._make_cell(), parent, {})
        assert len(list(parent)) == 1
        assert list(parent)[0].tag == _tei("cell")

    def test_no_colspan_sets_no_cols_attribute(self):
        """Test that colspan=None produces no ``cols`` attribute."""
        parent = ET.Element("row")
        with patch("utils.tei_renderer._render_node"):
            _render_cell(self._make_cell(colspan=None), parent, {})
        assert "cols" not in list(parent)[0].attrib

    def test_colspan_sets_cols_attribute(self):
        """Test that a numeric colspan is serialised as the ``cols`` attribute."""
        parent = ET.Element("row")
        with patch("utils.tei_renderer._render_node"):
            _render_cell(self._make_cell(colspan=3), parent, {})
        assert list(parent)[0].get("cols") == "3"

    def test_delegates_each_child_to_render_node(self):
        """Test that _render_node is called once for each child."""
        parent = ET.Element("row")
        with patch("utils.tei_renderer._render_node") as mock:
            _render_cell(self._make_cell(n=2), parent, {})
        assert mock.call_count == 2

    def test_empty_children_delegates_no_calls(self):
        """Test that a cell with no children makes no _render_node calls."""
        parent = ET.Element("row")
        with patch("utils.tei_renderer._render_node") as mock:
            _render_cell(Cell(children=[]), parent, {})
        mock.assert_not_called()

    def test_returns_none(self):
        """Test that _render_cell returns None."""
        parent = ET.Element("row")
        with patch("utils.tei_renderer._render_node"):
            assert _render_cell(self._make_cell(), parent, {}) is None
