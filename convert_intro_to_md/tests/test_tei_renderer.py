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
    _indent_tree,
    _protect_ws_nodes,
    _restore_ws_nodes,
    _tei,
    _WS_SENTINEL,
    _xml,
)
from utils.nodes import (
    Block,
    Note,
    Text,
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
        """Calls _build_tei_body with root, blocks, intro_locale, and lookup."""
        blocks = [Block(id="b1", heading=None)]
        with patch("utils.tei_renderer._build_tei_body") as mock_body:
            render(blocks, "op1", "en")
        assert mock_body.call_count == 1
        _, actual_blocks, intro_locale, _ = mock_body.call_args.args
        assert actual_blocks is blocks
        assert intro_locale == "en"

    def test_delegates_to_indent_tree(self):
        """Calls _indent_tree with the TEI root element."""
        with patch("utils.tei_renderer._indent_tree") as mock:
            render([], "op1", "de")
        mock.assert_called_once()


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

    def test_duplicate_id_keeps_first_and_prints_warning(self, capsys):
        """Keeps the first note for a duplicate key and prints a warning to stderr."""
        first = Note(id="note-3")
        second = Note(id="note-3")
        blocks = [
            Block(id="b1", heading=None, notes=[first]),
            Block(id="b2", heading=None, notes=[second]),
        ]
        result = _build_notes_lookup(blocks)
        assert result == {3: first}
        assert "Duplicate" in capsys.readouterr().err


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
        _build_tei_body(root, blocks or [], intro_locale, {})
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
            _build_tei_body(root, blocks, "de", {})
        assert mock_render.call_count == 2

    def test_content_nodes_delegated_to_render_node(self):
        """Calls _render_node once per content node."""
        content_nodes = [Text(value="x"), Text(value="y"), Text(value="z")]
        blocks = [Block(id="b1", heading=None, content=content_nodes)]
        root = ET.Element("TEI")
        with patch("utils.tei_renderer._render_node") as mock_render:
            _build_tei_body(root, blocks, "de", {})
        assert mock_render.call_count == 3

    def test_returns_none(self):
        """Returns None."""
        root = ET.Element("TEI")
        assert _build_tei_body(root, [], "en", {}) is None


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


class TestIndentTree:
    """Tests for the _indent_tree function."""

    def test_delegates_to_protect_ws_nodes(self):
        """Calls _protect_ws_nodes with the root element."""
        el = ET.Element("div")
        with patch("utils.tei_renderer._protect_ws_nodes") as mock:
            _indent_tree(el)
        mock.assert_called_once_with(el)

    def test_delegates_to_fix_mixed_content_indent(self):
        """Calls _fix_mixed_content_indent with the root element."""
        el = ET.Element("div")
        with patch("utils.tei_renderer._fix_mixed_content_indent") as mock:
            _indent_tree(el)
        mock.assert_called_once_with(el)

    def test_delegates_to_restore_ws_nodes(self):
        """Calls _restore_ws_nodes with the root element."""
        el = ET.Element("div")
        with patch("utils.tei_renderer._restore_ws_nodes") as mock:
            _indent_tree(el)
        mock.assert_called_once_with(el)

    def test_protect_called_before_indent_called_before_fix_called_before_restore(self):
        """Helpers are called in order: protect → indent → fix → restore."""
        el = ET.Element("div")
        call_order = []
        with (
            patch(
                "utils.tei_renderer._protect_ws_nodes",
                side_effect=lambda _: call_order.append("protect"),
            ),
            patch(
                "utils.tei_renderer.ET.indent",
                side_effect=lambda *a, **kw: call_order.append("indent"),
            ),
            patch(
                "utils.tei_renderer._fix_mixed_content_indent",
                side_effect=lambda _: call_order.append("fix"),
            ),
            patch(
                "utils.tei_renderer._restore_ws_nodes",
                side_effect=lambda _: call_order.append("restore"),
            ),
        ):
            _indent_tree(el)
        assert call_order == ["protect", "indent", "fix", "restore"]

    def test_whitespace_only_tail_preserved_as_space(self):
        """A whitespace-only .tail (\\xa0) survives the full indent pipeline as a space."""
        parent = ET.Element("p")
        child = ET.SubElement(parent, "hi")
        child.tail = "\xa0"
        _indent_tree(parent)
        assert child.tail == " "

    def test_returns_none(self):
        """Returns None."""
        el = ET.Element("p")
        assert _indent_tree(el) is None


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


class TestProtectWsNodes:
    """Tests for the _protect_ws_nodes function."""

    def test_whitespace_only_tail_replaced_with_sentinel(self):
        """A whitespace-only .tail on a child element is replaced with the sentinel."""
        parent = ET.Element("p")
        child = ET.SubElement(parent, "hi")
        child.tail = "\xa0"
        _protect_ws_nodes(parent)
        assert child.tail == _WS_SENTINEL

    def test_real_tail_not_replaced(self):
        """A .tail containing non-whitespace is not modified."""
        parent = ET.Element("p")
        child = ET.SubElement(parent, "hi")
        child.tail = "foo bar"
        _protect_ws_nodes(parent)
        assert child.tail == "foo bar"

    def test_none_tail_not_modified(self):
        """A None .tail is left as None."""
        parent = ET.Element("p")
        ET.SubElement(parent, "hi")
        _protect_ws_nodes(parent)
        assert list(parent)[0].tail is None

    def test_whitespace_only_text_on_parent_with_children_replaced(self):
        """A whitespace-only .text on a parent WITH children is replaced with the sentinel."""
        parent = ET.Element("p")
        parent.text = " "
        ET.SubElement(parent, "hi")
        _protect_ws_nodes(parent)
        assert parent.text == _WS_SENTINEL

    def test_whitespace_only_text_on_leaf_not_replaced(self):
        """A whitespace-only .text on a leaf element (no children) is not replaced."""
        leaf = ET.Element("p")
        leaf.text = " "
        _protect_ws_nodes(leaf)
        assert leaf.text == " "

    def test_applies_recursively(self):
        """Sentinel replacement recurses into child elements."""
        parent = ET.Element("p")
        child = ET.SubElement(parent, "hi")
        grandchild = ET.SubElement(child, "ref")
        grandchild.tail = "\xa0"
        _protect_ws_nodes(parent)
        assert grandchild.tail == _WS_SENTINEL

    def test_returns_none(self):
        """Returns None."""
        el = ET.Element("p")
        assert _protect_ws_nodes(el) is None


class TestRestoreWsNodes:
    """Tests for the _restore_ws_nodes function."""

    def test_sentinel_text_replaced_with_space(self):
        """A .text equal to the sentinel is replaced with a regular space."""
        el = ET.Element("p")
        el.text = _WS_SENTINEL
        _restore_ws_nodes(el)
        assert el.text == " "

    def test_sentinel_tail_replaced_with_space(self):
        """A .tail equal to the sentinel is replaced with a regular space."""
        parent = ET.Element("p")
        child = ET.SubElement(parent, "hi")
        child.tail = _WS_SENTINEL
        _restore_ws_nodes(parent)
        assert child.tail == " "

    def test_non_sentinel_text_not_modified(self):
        """A .text that is not the sentinel is left unchanged."""
        el = ET.Element("p")
        el.text = "hello"
        _restore_ws_nodes(el)
        assert el.text == "hello"

    def test_non_sentinel_tail_not_modified(self):
        """A .tail that is not the sentinel is left unchanged."""
        parent = ET.Element("p")
        child = ET.SubElement(parent, "hi")
        child.tail = " foo"
        _restore_ws_nodes(parent)
        assert child.tail == " foo"

    def test_applies_recursively(self):
        """Sentinel restoration recurses into child elements."""
        parent = ET.Element("p")
        child = ET.SubElement(parent, "hi")
        grandchild = ET.SubElement(child, "ref")
        grandchild.tail = _WS_SENTINEL
        _restore_ws_nodes(parent)
        assert grandchild.tail == " "

    def test_returns_none(self):
        """Returns None."""
        el = ET.Element("p")
        assert _restore_ws_nodes(el) is None


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
