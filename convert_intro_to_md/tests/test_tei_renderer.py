"""Tests for utils/tei_renderer.py"""

import xml.etree.ElementTree as ET
from unittest.mock import patch

from utils.tei_renderer import (
    render,
    _append_text,
    _build_notes_lookup,
    _build_tei_body,
    _build_tei_header,
    _fix_mixed_content_indent,
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
from utils import tei_renderer
from utils.nodes import (
    Block,
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


class TestRender:
    """Tests for the render function."""

    def test_returns_str(self):
        """Returns a str."""
        assert isinstance(render([], "op1", "de"), str)

    def test_output_starts_with_xml_declaration(self):
        """Output begins with an XML declaration."""
        assert render([], "op1", "de").startswith("<?xml")

    def test_output_contains_tei_root(self):
        """Root element is <TEI> in the TEI namespace."""
        root = ET.fromstring(render([], "op1", "de"))
        assert root.tag == _tei("TEI")

    def test_delegates_to_build_notes_lookup(self):
        """Calls _build_notes_lookup with the blocks list."""
        blocks = [Block(id="b1", heading=None)]
        with patch(
            "utils.tei_renderer._build_notes_lookup", return_value={}
        ) as mock_lookup:
            render(blocks, "op1", "de")
        mock_lookup.assert_called_once_with(blocks)

    def test_delegates_to_build_tei_header(self):
        """Calls _build_tei_header with root, intro_id, and intro_locale."""
        with patch("utils.tei_renderer._build_tei_header") as mock_header:
            render([], "my-id", "fr")
        assert mock_header.call_count == 1
        _, intro_id, intro_locale = mock_header.call_args.args
        assert intro_id == "my-id"
        assert intro_locale == "fr"

    def test_delegates_to_build_tei_body(self):
        """Calls _build_tei_body with root, blocks, and intro_locale."""
        blocks = [Block(id="b1", heading=None)]
        with patch("utils.tei_renderer._build_tei_body") as mock_body:
            render(blocks, "op1", "en")
        assert mock_body.call_count == 1
        _, actual_blocks, intro_locale = mock_body.call_args.args
        assert actual_blocks is blocks
        assert intro_locale == "en"

    def test_notes_lookup_cleared_after_render(self):
        """_notes_lookup is reset to {} after render completes."""
        block = Block(id="b1", heading=None, notes=[Note(id="note-1")])
        render([block], "op1", "de")
        assert not vars(tei_renderer)["_notes_lookup"]


class TestBuildNotesLookup:
    """Tests for the _build_notes_lookup function."""

    def test_empty_blocks_returns_empty_dict(self):
        """Returns an empty dict when given no blocks."""
        assert not _build_notes_lookup([])

    def test_indexes_note_by_integer_suffix(self):
        """Maps the integer suffix of note.id to the Note."""
        note = Note(id="note-3")
        block = Block(id="b1", heading=None, notes=[note])
        result = _build_notes_lookup([block])
        assert result == {3: note}

    def test_indexes_notes_across_multiple_blocks(self):
        """Collects notes from every block."""
        note_a = Note(id="note-1")
        note_b = Note(id="note-2")
        blocks = [
            Block(id="b1", heading=None, notes=[note_a]),
            Block(id="b2", heading=None, notes=[note_b]),
        ]
        result = _build_notes_lookup(blocks)
        assert result == {1: note_a, 2: note_b}

    def test_indexes_multiple_notes_in_one_block(self):
        """Handles multiple notes inside a single block."""
        note_a = Note(id="note-5")
        note_b = Note(id="note-6")
        block = Block(id="b1", heading=None, notes=[note_a, note_b])
        result = _build_notes_lookup([block])
        assert result == {5: note_a, 6: note_b}

    def test_skips_note_with_non_integer_suffix(self):
        """Silently skips notes whose id suffix is not an integer."""
        note = Note(id="note-abc")
        block = Block(id="b1", heading=None, notes=[note])
        assert not _build_notes_lookup([block])

    def test_skips_note_with_empty_id(self):
        """Silently skips notes with an empty id string."""
        note = Note(id="")
        block = Block(id="b1", heading=None, notes=[note])
        assert not _build_notes_lookup([block])

    def test_block_without_notes_contributes_nothing(self):
        """A block with no notes does not affect the result."""
        block = Block(id="b1", heading=None, notes=[])
        assert not _build_notes_lookup([block])


class TestBuildTeiHeader:
    """Tests for the _build_tei_header function."""

    @staticmethod
    def _call(intro_id: str = "op42", intro_locale: str = "de") -> ET.Element:
        root = ET.Element("TEI")
        _build_tei_header(root, intro_id, intro_locale)
        return root

    def test_appends_tei_header_to_root(self):
        """Appends exactly one <teiHeader> child to root."""
        root = self._call()
        headers = [child for child in root if child.tag == _tei("teiHeader")]
        assert len(headers) == 1

    def test_title_text_is_intro_id(self):
        """<titleStmt>/<title> text equals intro_id."""
        root = self._call(intro_id="op99")
        title = root.find(
            f"{_tei('teiHeader')}/{_tei('fileDesc')}/{_tei('titleStmt')}/{_tei('title')}"
        )
        assert title is not None
        assert title.text == "op99"

    def test_publication_stmt_text(self):
        """<publicationStmt>/<p> text is 'AWG Online Edition'."""
        root = self._call()
        p = root.find(
            f"{_tei('teiHeader')}/{_tei('fileDesc')}/{_tei('publicationStmt')}/{_tei('p')}"
        )
        assert p is not None
        assert p.text == "AWG Online Edition"

    def test_source_desc_text(self):
        """<sourceDesc>/<p> text is 'Converted from AWG intro JSON'."""
        root = self._call()
        p = root.find(
            f"{_tei('teiHeader')}/{_tei('fileDesc')}/{_tei('sourceDesc')}/{_tei('p')}"
        )
        assert p is not None
        assert p.text == "Converted from AWG intro JSON"

    def test_language_ident_is_intro_locale(self):
        """<profileDesc>/<langUsage>/<language ident> equals intro_locale."""
        root = self._call(intro_locale="fr")
        lang = root.find(
            f"{_tei('teiHeader')}/{_tei('profileDesc')}/{_tei('langUsage')}/{_tei('language')}"
        )
        assert lang is not None
        assert lang.get("ident") == "fr"

    def test_returns_none(self):
        """Returns None."""
        root = ET.Element("TEI")
        assert _build_tei_header(root, "op1", "en") is None


class TestBuildTeiBody:
    """Tests for the _build_tei_body function."""

    @staticmethod
    def _call(
        blocks: list | None = None,
        intro_locale: str = "de",
    ) -> ET.Element:
        root = ET.Element("TEI")
        _build_tei_body(root, blocks or [], intro_locale)
        return root

    def test_appends_text_element_to_root(self):
        """Appends exactly one <text> child to root."""
        root = self._call()
        text_els = [child for child in root if child.tag == _tei("text")]
        assert len(text_els) == 1

    def test_text_element_has_xml_lang(self):
        """Sets xml:lang on <text> to intro_locale."""
        root = self._call(intro_locale="fr")
        text_el = root.find(_tei("text"))
        assert text_el is not None
        assert text_el.get(_xml("lang")) == "fr"

    def test_appends_body_inside_text(self):
        """Appends a <body> child inside <text>."""
        root = self._call()
        body = root.find(f"{_tei('text')}/{_tei('body')}")
        assert body is not None

    def test_creates_div_per_block(self):
        """Creates one <div> per block inside <body>."""
        blocks = [
            Block(id="b1", heading=None),
            Block(id="b2", heading=None),
        ]
        root = self._call(blocks=blocks)
        body = root.find(f"{_tei('text')}/{_tei('body')}")
        assert body is not None
        divs = list(body)
        assert len(divs) == 2
        assert all(div.tag == _tei("div") for div in divs)

    def test_block_id_sets_xml_id_on_div(self):
        """Sets xml:id on <div> when block.id is non-empty."""
        root = self._call(blocks=[Block(id="blk-1", heading=None)])
        div = root.find(f"{_tei('text')}/{_tei('body')}/{_tei('div')}")
        assert div is not None
        assert div.get(_xml("id")) == "blk-1"

    def test_empty_block_id_sets_no_xml_id(self):
        """Does not set xml:id on <div> when block.id is empty string."""
        root = self._call(blocks=[Block(id="", heading=None)])
        div = root.find(f"{_tei('text')}/{_tei('body')}/{_tei('div')}")
        assert div is not None
        assert div.get(_xml("id")) is None

    def test_heading_creates_head_element(self):
        """Creates a <head> child inside the <div> when block.heading is set."""
        root = self._call(blocks=[Block(id="b1", heading=[Text(value="Title")])])
        head = root.find(f"{_tei('text')}/{_tei('body')}/{_tei('div')}/{_tei('head')}")
        assert head is not None

    def test_no_heading_creates_no_head_element(self):
        """Does not create a <head> when block.heading is None."""
        root = self._call(blocks=[Block(id="b1", heading=None)])
        head = root.find(f"{_tei('text')}/{_tei('body')}/{_tei('div')}/{_tei('head')}")
        assert head is None

    def test_heading_nodes_delegated_to_render_node(self):
        """Calls _render_node once per heading node."""
        heading_nodes = [Text(value="A"), Text(value="B")]
        blocks = [Block(id="b1", heading=heading_nodes)]
        root = ET.Element("TEI")
        with patch("utils.tei_renderer._render_node") as mock_render:
            _build_tei_body(root, blocks, "de")
        assert mock_render.call_count == 2

    def test_content_nodes_delegated_to_render_node(self):
        """Calls _render_node once per content node."""
        content_nodes = [Text(value="x"), Text(value="y"), Text(value="z")]
        blocks = [Block(id="b1", heading=None, content=content_nodes)]
        root = ET.Element("TEI")
        with patch("utils.tei_renderer._render_node") as mock_render:
            _build_tei_body(root, blocks, "de")
        assert mock_render.call_count == 3

    def test_returns_none(self):
        """Returns None."""
        root = ET.Element("TEI")
        assert _build_tei_body(root, [], "en") is None


class TestRenderNode:
    """Tests for the _render_node dispatch function."""

    def test_text_delegates_to_append_text(self):
        """Text node calls _append_text."""
        parent = ET.Element("root")
        with patch("utils.tei_renderer._append_text") as mock:
            _render_node(Text(value="hi"), parent)
        mock.assert_called_once_with(parent, "hi")

    def test_footnote_ref_delegates_to_render_footnote_ref(self):
        """FootnoteRef node calls _render_footnote_ref."""
        parent = ET.Element("root")
        node = FootnoteRef(n=1)
        with patch("utils.tei_renderer._render_footnote_ref") as mock:
            _render_node(node, parent)
        mock.assert_called_once_with(node, parent)

    def test_cross_ref_delegates_to_render_cross_ref(self):
        """CrossRef node calls _render_cross_ref."""
        parent = ET.Element("root")
        node = CrossRef(n=2)
        with patch("utils.tei_renderer._render_cross_ref") as mock:
            _render_node(node, parent)
        mock.assert_called_once_with(node, parent)

    def test_ref_delegates_to_render_ref(self):
        """Ref node calls _render_ref."""
        parent = ET.Element("root")
        node = Ref(target="https://example.com")
        with patch("utils.tei_renderer._render_ref") as mock:
            _render_node(node, parent)
        mock.assert_called_once_with(node, parent)

    def test_inline_wrap_type_delegates_to_render_inline_node(self):
        """Every type in _INLINE_WRAP calls _render_inline_node."""
        for node_type in _INLINE_WRAP:
            parent = ET.Element("root")
            node = node_type(children=[])
            with patch("utils.tei_renderer._render_inline_node") as mock:
                _render_node(node, parent)
            mock.assert_called_once_with(node, parent)

    def test_blockquote_delegates_to_render_blockquote(self):
        """Blockquote node calls _render_blockquote."""
        parent = ET.Element("root")
        node = Blockquote()
        with patch("utils.tei_renderer._render_blockquote") as mock:
            _render_node(node, parent)
        mock.assert_called_once_with(node, parent)

    def test_list_block_delegates_to_render_list_block(self):
        """ListBlock node calls _render_list_block."""
        parent = ET.Element("root")
        node = ListBlock()
        with patch("utils.tei_renderer._render_list_block") as mock:
            _render_node(node, parent)
        mock.assert_called_once_with(node, parent)

    def test_table_delegates_to_render_table(self):
        """Table node calls _render_table."""
        parent = ET.Element("root")
        node = Table()
        with patch("utils.tei_renderer._render_table") as mock:
            _render_node(node, parent)
        mock.assert_called_once_with(node, parent)


class TestRenderInlineNode:
    """Tests for the _render_inline_node function."""

    def setup_method(self):
        """Set up a fresh parent element for each test."""
        self.parent = ET.Element("root")  # pylint: disable=attribute-defined-outside-init

    def test_italic_creates_hi_with_rend_italic(self):
        """Italic → <hi rend="italic">."""
        _render_inline_node(Italic(children=[]), self.parent)
        el = list(self.parent)[0]
        assert el.tag == _tei("hi")
        assert el.get("rend") == "italic"

    def test_bold_creates_hi_with_rend_bold(self):
        """Bold → <hi rend="bold">."""
        _render_inline_node(Bold(children=[]), self.parent)
        el = list(self.parent)[0]
        assert el.tag == _tei("hi")
        assert el.get("rend") == "bold"

    def test_underline_creates_hi_with_rend_underline(self):
        """Underline → <hi rend="underline">."""
        _render_inline_node(Underline(children=[]), self.parent)
        el = list(self.parent)[0]
        assert el.tag == _tei("hi")
        assert el.get("rend") == "underline"

    def test_superscript_creates_hi_with_rend_sup(self):
        """Superscript → <hi rend="sup">."""
        _render_inline_node(Superscript(children=[]), self.parent)
        el = list(self.parent)[0]
        assert el.tag == _tei("hi")
        assert el.get("rend") == "sup"

    def test_strikethrough_creates_del_without_rend(self):
        """Strikethrough → <del> with no rend attribute."""
        _render_inline_node(Strikethrough(children=[]), self.parent)
        el = list(self.parent)[0]
        assert el.tag == _tei("del")
        assert el.get("rend") is None

    def test_paragraph_creates_p_without_rend(self):
        """Paragraph → <p> with no rend attribute."""
        _render_inline_node(Paragraph(children=[]), self.parent)
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
            _render_inline_node(node, self.parent)  # must not raise

    def test_delegates_children_to_render_node(self):
        """Calls _render_node once per child."""
        children = [Text(value="a"), Text(value="b")]
        with patch("utils.tei_renderer._render_node") as mock_render:
            _render_inline_node(Italic(children=children), self.parent)
        assert mock_render.call_count == 2

    def test_passes_created_element_to_render_node(self):
        """Passes the new element (not the parent) to _render_node."""
        child = Text(value="x")
        with patch("utils.tei_renderer._render_node") as mock_render:
            _render_inline_node(Bold(children=[child]), self.parent)
        created_el = list(self.parent)[0]
        mock_render.assert_called_once_with(child, created_el)


class TestRenderBlockquote:
    """Tests for the _render_blockquote function."""

    def setup_method(self):
        """Set up a fresh parent element for each test."""
        self.parent = ET.Element("root")  # pylint: disable=attribute-defined-outside-init

    def test_creates_quote_element(self):
        """Creates a <quote> child on the parent."""
        _render_blockquote(Blockquote(paragraphs=[]), self.parent)
        children = list(self.parent)
        assert len(children) == 1
        assert children[0].tag == _tei("quote")

    def test_creates_l_element_per_paragraph(self):
        """Creates one <l> child per paragraph inside the <quote>."""
        node = Blockquote(paragraphs=[Paragraph(), Paragraph(), Paragraph()])
        _render_blockquote(node, self.parent)
        quote_el = list(self.parent)[0]
        l_els = list(quote_el)
        assert len(l_els) == 3
        assert all(el.tag == _tei("l") for el in l_els)

    def test_delegates_para_children_to_render_node(self):
        """Calls _render_node once per child across all paragraphs."""
        children = [Text(value="a"), Text(value="b")]
        node = Blockquote(paragraphs=[Paragraph(children=children)])
        with patch("utils.tei_renderer._render_node") as mock_render:
            _render_blockquote(node, self.parent)
        assert mock_render.call_count == 2

    def test_passes_l_element_to_render_node(self):
        """Passes the <l> element (not the parent) to _render_node."""
        child = Text(value="text")
        node = Blockquote(paragraphs=[Paragraph(children=[child])])
        with patch("utils.tei_renderer._render_node") as mock_render:
            _render_blockquote(node, self.parent)
        l_el = list(list(self.parent)[0])[0]
        mock_render.assert_called_once_with(child, l_el)

    def test_empty_paragraphs(self):
        """Renders a <quote> with no paragraphs without error."""
        _render_blockquote(Blockquote(paragraphs=[]), self.parent)  # must not raise
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
        _render_footnote_ref(FootnoteRef(n=1), self.parent)
        children = list(self.parent)
        assert len(children) == 1
        assert children[0].tag == _tei("note")

    def test_sets_place_end(self):
        """Sets place="end" on the <note> element."""
        _render_footnote_ref(FootnoteRef(n=1), self.parent)
        assert list(self.parent)[0].get("place") == "end"

    def test_sets_n_attribute(self):
        """Sets n to the string form of node.n."""
        _render_footnote_ref(FootnoteRef(n=3), self.parent)
        assert list(self.parent)[0].get("n") == "3"

    def test_sets_xml_id_attribute(self):
        """Sets xml:id to 'note-N'."""
        _render_footnote_ref(FootnoteRef(n=5), self.parent)
        assert list(self.parent)[0].get(_xml("id")) == "note-5"

    def test_no_children_when_note_absent_from_lookup(self):
        """Produces an empty <note> when n is not in _notes_lookup."""
        with patch("utils.tei_renderer._notes_lookup", {}):
            _render_footnote_ref(FootnoteRef(n=1), self.parent)
        assert not list(list(self.parent)[0])

    def test_delegates_note_children_to_render_node(self):
        """Calls _render_node once per child of the looked-up Note."""
        child = Text(value="body")
        note = Note(id="note-2", children=[child])
        with (
            patch("utils.tei_renderer._notes_lookup", {2: note}),
            patch("utils.tei_renderer._render_node") as mock_render,
        ):
            _render_footnote_ref(FootnoteRef(n=2), self.parent)
        assert mock_render.call_count == 1

    def test_passes_note_element_to_render_node(self):
        """Passes the <note> element (not the parent) to _render_node."""
        child = Text(value="body")
        note = Note(id="note-7", children=[child])
        with (
            patch("utils.tei_renderer._notes_lookup", {7: note}),
            patch("utils.tei_renderer._render_node") as mock_render,
        ):
            _render_footnote_ref(FootnoteRef(n=7), self.parent)
        note_el = list(self.parent)[0]
        mock_render.assert_called_once_with(child, note_el)


class TestRenderListBlock:
    """Tests for the _render_list_block function."""

    def test_creates_list_element(self):
        """Creates a <list> child on the parent."""
        parent = ET.Element("root")
        node = ListBlock(items=[])
        _render_list_block(node, parent)
        children = list(parent)
        assert len(children) == 1
        assert children[0].tag == _tei("list")

    def test_unordered_list_has_no_rend_attribute(self):
        """Does not set rend when ordered=False."""
        parent = ET.Element("root")
        node = ListBlock(items=[], ordered=False)
        _render_list_block(node, parent)
        assert list(parent)[0].get("rend") is None

    def test_ordered_list_sets_rend_ordered(self):
        """Sets rend="ordered" when ordered=True."""
        parent = ET.Element("root")
        node = ListBlock(items=[], ordered=True)
        _render_list_block(node, parent)
        assert list(parent)[0].get("rend") == "ordered"

    def test_creates_item_element_per_list_item(self):
        """Creates one <item> child per entry in node.items."""
        parent = ET.Element("root")
        node = ListBlock(items=[ListItem(), ListItem(), ListItem()])
        _render_list_block(node, parent)
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
            _render_list_block(node, parent)
        assert mock_render.call_count == 2

    def test_passes_item_element_to_render_node(self):
        """Passes the <item> element (not the parent) to _render_node."""
        parent = ET.Element("root")
        child = Text(value="text")
        node = ListBlock(items=[ListItem(children=[child])])
        with patch("utils.tei_renderer._render_node") as mock_render:
            _render_list_block(node, parent)
        item_el = list(list(parent)[0])[0]
        mock_render.assert_called_once_with(child, item_el)


class TestRenderRef:
    """Tests for the _render_ref function."""

    def test_creates_ref_element(self):
        """Creates a <ref> child on the parent."""
        parent = ET.Element("root")
        node = Ref(target="https://example.com", children=[])
        _render_ref(node, parent)
        children = list(parent)
        assert len(children) == 1
        assert children[0].tag == _tei("ref")

    def test_sets_target_attribute(self):
        """Sets the target attribute from node.target."""
        parent = ET.Element("root")
        node = Ref(target="https://example.com", children=[])
        _render_ref(node, parent)
        assert list(parent)[0].get("target") == "https://example.com"

    def test_no_extra_attributes(self):
        """Sets only the target attribute, no others."""
        parent = ET.Element("root")
        node = Ref(target="https://example.com", children=[])
        _render_ref(node, parent)
        assert list(list(parent)[0].attrib.keys()) == ["target"]

    def test_delegates_children_to_render_node(self):
        """Calls _render_node once per child."""
        parent = ET.Element("root")
        children = [Text(value="click"), Text(value=" here")]
        node = Ref(target="https://example.com", children=children)
        with patch("utils.tei_renderer._render_node") as mock_render:
            _render_ref(node, parent)
        assert mock_render.call_count == 2

    def test_passes_ref_element_to_render_node(self):
        """Passes the <ref> element (not the parent) to _render_node."""
        parent = ET.Element("root")
        child = Text(value="link")
        node = Ref(target="https://example.com", children=[child])
        with patch("utils.tei_renderer._render_node") as mock_render:
            _render_ref(node, parent)
        ref_el = list(parent)[0]
        mock_render.assert_called_once_with(child, ref_el)

    def test_empty_children(self):
        """Renders a <ref> with no children without error."""
        parent = ET.Element("root")
        node = Ref(target="https://example.com", children=[])
        _render_ref(node, parent)  # must not raise
        assert list(parent)[0].tag == _tei("ref")


class TestRenderTable:
    """Tests for the _render_table function."""

    def _make_table(self, n: int = 1) -> Table:
        return Table(rows=[Row(cells=[]) for _ in range(n)])

    def test_creates_table_child_element(self):
        """Test that a ``<table>`` element is appended to the parent."""
        parent = ET.Element("div")
        with patch("utils.tei_renderer._render_row"):
            _render_table(self._make_table(), parent)
        assert len(list(parent)) == 1
        assert list(parent)[0].tag == _tei("table")

    def test_delegates_each_row_to_render_row(self):
        """Test that _render_row is called once for each row."""
        parent = ET.Element("div")
        with patch("utils.tei_renderer._render_row") as mock:
            _render_table(self._make_table(n=3), parent)
        assert mock.call_count == 3

    def test_empty_table_delegates_no_calls(self):
        """Test that a table with no rows makes no _render_row calls."""
        parent = ET.Element("div")
        with patch("utils.tei_renderer._render_row") as mock:
            _render_table(Table(rows=[]), parent)
        mock.assert_not_called()

    def test_returns_none(self):
        """Test that _render_table returns None."""
        parent = ET.Element("div")
        with patch("utils.tei_renderer._render_row"):
            assert _render_table(self._make_table(), parent) is None


class TestRenderRow:
    """Tests for the _render_row function."""

    def _make_row(self, n: int = 1, is_header: bool = False) -> Row:
        return Row(cells=[Cell(children=[]) for _ in range(n)], is_header=is_header)

    def test_creates_row_child_element(self):
        """Test that a ``<row>`` element is appended to the parent."""
        parent = ET.Element("table")
        with patch("utils.tei_renderer._render_cell"):
            _render_row(self._make_row(), parent)
        assert len(list(parent)) == 1
        assert list(parent)[0].tag == _tei("row")

    def test_non_header_row_has_no_role_attribute(self):
        """Test that a non-header row does not receive a ``role`` attribute."""
        parent = ET.Element("table")
        with patch("utils.tei_renderer._render_cell"):
            _render_row(self._make_row(is_header=False), parent)
        assert "role" not in list(parent)[0].attrib

    def test_header_row_sets_role_label(self):
        """Test that a header row receives ``role="label"``."""
        parent = ET.Element("table")
        with patch("utils.tei_renderer._render_cell"):
            _render_row(self._make_row(is_header=True), parent)
        assert list(parent)[0].get("role") == "label"

    def test_delegates_each_cell_to_render_cell(self):
        """Test that _render_cell is called once for each cell."""
        parent = ET.Element("table")
        with patch("utils.tei_renderer._render_cell") as mock:
            _render_row(self._make_row(n=3), parent)
        assert mock.call_count == 3

    def test_empty_row_delegates_no_calls(self):
        """Test that a row with no cells makes no _render_cell calls."""
        parent = ET.Element("table")
        with patch("utils.tei_renderer._render_cell") as mock:
            _render_row(Row(cells=[]), parent)
        mock.assert_not_called()

    def test_returns_none(self):
        """Test that _render_row returns None."""
        parent = ET.Element("table")
        with patch("utils.tei_renderer._render_cell"):
            assert _render_row(self._make_row(), parent) is None


class TestRenderCell:
    """Tests for the _render_cell function."""

    def _make_cell(self, n: int = 1, colspan: int | None = None) -> Cell:
        return Cell(children=[Text(value="x") for _ in range(n)], colspan=colspan)

    def test_creates_cell_child_element(self):
        """Test that a ``<cell>`` element is appended to the parent."""
        parent = ET.Element("row")
        with patch("utils.tei_renderer._render_node"):
            _render_cell(self._make_cell(), parent)
        assert len(list(parent)) == 1
        assert list(parent)[0].tag == _tei("cell")

    def test_no_colspan_sets_no_cols_attribute(self):
        """Test that colspan=None produces no ``cols`` attribute."""
        parent = ET.Element("row")
        with patch("utils.tei_renderer._render_node"):
            _render_cell(self._make_cell(colspan=None), parent)
        assert "cols" not in list(parent)[0].attrib

    def test_colspan_sets_cols_attribute(self):
        """Test that a numeric colspan is serialised as the ``cols`` attribute."""
        parent = ET.Element("row")
        with patch("utils.tei_renderer._render_node"):
            _render_cell(self._make_cell(colspan=3), parent)
        assert list(parent)[0].get("cols") == "3"

    def test_delegates_each_child_to_render_node(self):
        """Test that _render_node is called once for each child."""
        parent = ET.Element("row")
        with patch("utils.tei_renderer._render_node") as mock:
            _render_cell(self._make_cell(n=2), parent)
        assert mock.call_count == 2

    def test_empty_children_delegates_no_calls(self):
        """Test that a cell with no children makes no _render_node calls."""
        parent = ET.Element("row")
        with patch("utils.tei_renderer._render_node") as mock:
            _render_cell(Cell(children=[]), parent)
        mock.assert_not_called()

    def test_returns_none(self):
        """Test that _render_cell returns None."""
        parent = ET.Element("row")
        with patch("utils.tei_renderer._render_node"):
            assert _render_cell(self._make_cell(), parent) is None


class TestAppendText:
    """Tests for the _append_text function."""

    def test_no_children_sets_parent_text(self):
        """Test that text is assigned to parent.text when the element has no children."""
        el = ET.Element("p")
        _append_text(el, "hello")
        assert el.text == "hello"

    def test_no_children_appends_to_existing_parent_text(self):
        """Test that text is appended to an existing parent.text when there are no children."""
        el = ET.Element("p")
        el.text = "foo"
        _append_text(el, "bar")
        assert el.text == "foobar"

    def test_with_children_sets_last_child_tail(self):
        """Test that text is assigned to the last child's tail when children exist."""
        el = ET.Element("p")
        child = ET.SubElement(el, "hi")
        _append_text(el, "after")
        assert child.tail == "after"

    def test_with_children_appends_to_existing_last_child_tail(self):
        """Test that text is appended to an existing tail on the last child."""
        el = ET.Element("p")
        child = ET.SubElement(el, "hi")
        child.tail = "already"
        _append_text(el, " more")
        assert child.tail == "already more"

    def test_with_children_only_last_child_tail_is_modified(self):
        """Test that only the last child's tail is touched, not earlier siblings."""
        el = ET.Element("p")
        first = ET.SubElement(el, "hi")
        first.tail = "first-tail"
        _last = ET.SubElement(el, "ref")
        _append_text(el, "x")
        assert first.tail == "first-tail"

    def test_returns_none(self):
        """Test that _append_text returns None on a successful append."""
        el = ET.Element("p")
        assert _append_text(el, "text") is None


class TestFixMixedContentIndent:
    """Tests for the _fix_mixed_content_indent function."""

    def test_no_children_no_text_leaves_element_unchanged(self):
        """Test that an element with no text and no children is left as-is."""
        el = ET.Element("p")
        _fix_mixed_content_indent(el)
        assert el.text is None

    def test_whitespace_only_text_with_no_tailed_children_is_preserved(self):
        """Test that whitespace-only text is NOT cleared when no mixed content is detected."""
        el = ET.Element("div")
        el.text = "\n  "
        ET.SubElement(el, "p")
        _fix_mixed_content_indent(el)
        assert el.text == "\n  "

    def test_whitespace_text_cleared_when_child_has_real_tail(self):
        """Test that whitespace-only elem.text is cleared when a child has a real tail."""
        el = ET.Element("p")
        el.text = "\n  "
        child = ET.SubElement(el, "hi")
        child.tail = "after"
        _fix_mixed_content_indent(el)
        assert el.text is None

    def test_real_text_preserved_when_mixed_content_detected(self):
        """Test that real elem.text is not cleared even when mixed content is detected."""
        el = ET.Element("p")
        el.text = "before"
        child = ET.SubElement(el, "hi")
        child.tail = "\n  "
        _fix_mixed_content_indent(el)
        assert el.text == "before"

    def test_whitespace_only_tail_cleared_when_mixed_content_detected(self):
        """Test that a whitespace-only child tail is cleared when mixed content is present."""
        el = ET.Element("p")
        el.text = "before"
        child = ET.SubElement(el, "hi")
        child.tail = "\n  "
        _fix_mixed_content_indent(el)
        assert child.tail is None

    def test_real_tail_preserved_when_mixed_content_detected(self):
        """Test that a real (non-whitespace) child tail is never cleared."""
        el = ET.Element("p")
        el.text = "before"
        child = ET.SubElement(el, "hi")
        child.tail = " after"
        _fix_mixed_content_indent(el)
        assert child.tail == " after"

    def test_only_whitespace_tail_sibling_cleared_not_real_tail_sibling(self):
        """Test that only whitespace tails are cleared; real tails on other siblings are kept."""
        el = ET.Element("p")
        el.text = "start"
        first = ET.SubElement(el, "hi")
        first.tail = "\n  "
        second = ET.SubElement(el, "ref")
        second.tail = " end"
        _fix_mixed_content_indent(el)
        assert first.tail is None
        assert second.tail == " end"

    def test_recursively_fixes_nested_mixed_content(self):
        """Test that mixed content inside a child element is also fixed."""
        outer = ET.Element("div")
        outer.text = (
            "\n  "  # whitespace only, no real tail on child → no trigger at outer
        )
        inner = ET.Element("p")
        inner.text = "text"
        span = ET.SubElement(inner, "hi")
        span.tail = "\n  "
        outer.append(inner)
        _fix_mixed_content_indent(outer)
        assert span.tail is None

    def test_returns_none(self):
        """Test that _fix_mixed_content_indent returns None."""
        el = ET.Element("p")
        assert _fix_mixed_content_indent(el) is None


class TestTei:
    """Tests for the _tei helper function."""

    def test_wraps_tag_in_tei_namespace(self):
        """Test that the tag is wrapped in the TEI Clark-notation namespace."""
        assert _tei("p") == "{http://www.tei-c.org/ns/1.0}p"

    def test_different_tags_produce_different_names(self):
        """Test that distinct tag names produce distinct qualified names."""
        assert _tei("hi") != _tei("ref")

    def test_namespace_prefix_is_constant(self):
        """Test that the namespace portion is identical for any two tags."""
        ns_hi = _tei("hi").split("}", maxsplit=1)[0] + "}"
        ns_ref = _tei("ref").split("}", maxsplit=1)[0] + "}"
        assert ns_hi == ns_ref


class TestXml:
    """Tests for the _xml helper function."""

    def test_wraps_attr_in_xml_namespace(self):
        """Test that the attribute is wrapped in the XML Clark-notation namespace."""
        assert _xml("lang") == "{http://www.w3.org/XML/1998/namespace}lang"

    def test_different_attrs_produce_different_names(self):
        """Test that distinct attribute names produce distinct qualified names."""
        assert _xml("lang") != _xml("id")

    def test_namespace_prefix_is_constant(self):
        """Test that the namespace portion is identical for any two attributes."""
        ns_lang = _xml("lang").split("}", maxsplit=1)[0] + "}"
        ns_id = _xml("id").split("}", maxsplit=1)[0] + "}"
        assert ns_lang == ns_id
