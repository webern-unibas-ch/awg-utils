# pylint: disable=protected-access
"""Tests for utils/replacement_utils.py"""

import re

from utils.replacement_utils import ReplacementUtils


class TestNormalizeWhitespace:
    """Tests for the normalize_whitespace function."""

    def test_replaces_non_breaking_space(self):
        """Test that non-breaking spaces are replaced with regular spaces."""
        assert ReplacementUtils.normalize_whitespace("a\xa0b") == "a b"

    def test_collapses_triple_newlines(self):
        """Test that three or more consecutive newlines are collapsed to two."""
        assert ReplacementUtils.normalize_whitespace("a\n\n\nb") == "a\n\nb"

    def test_collapses_many_newlines(self):
        """Test that a long run of newlines is collapsed to two."""
        assert ReplacementUtils.normalize_whitespace("a\n\n\n\n\nb") == "a\n\nb"

    def test_preserves_double_newlines(self):
        """Test that exactly two consecutive newlines are left unchanged."""
        assert ReplacementUtils.normalize_whitespace("a\n\nb") == "a\n\nb"

    def test_strips_leading_and_trailing_whitespace(self):
        """Test that leading and trailing whitespace is stripped."""
        assert ReplacementUtils.normalize_whitespace("  hello  ") == "hello"

    def test_plain_text_unchanged(self):
        """Test that plain text with no special whitespace is returned unchanged."""
        assert ReplacementUtils.normalize_whitespace("plain text") == "plain text"


class TestDetokenize:
    """Tests for the detokenize function."""

    def test_restores_all_token_types(self):
        """Test that all token types including escaped brackets are restored in a single call."""
        text = r"@@FNREF_1@@ see @@FNCROSSREF_3@@ and @@PIPE@@ and \[b]"
        result = ReplacementUtils.detokenize(text)
        assert result == r"[^1] see [3](#fn3) and \| and [b]"

    def test_detokenizes_fnref(self):
        """Test that an FNREF token is detokenized to a Markdown footnote reference."""
        assert ReplacementUtils.detokenize("@@FNREF_7@@") == "[^7]"

    def test_detokenizes_fncrossref(self):
        """Test that an FNCROSSREF token is detokenized to an inline link."""
        assert ReplacementUtils.detokenize("@@FNCROSSREF_5@@") == "[5](#fn5)"

    def test_detokenizes_pipe(self):
        """Test that a PIPE token is detokenized to an escaped Markdown pipe."""
        assert ReplacementUtils.detokenize("a @@PIPE@@ b") == r"a \| b"

    def test_detokenizes_brackets(self):
        """Test that markdownify-escaped brackets are unescaped."""
        assert ReplacementUtils.detokenize(r"\[b]") == "[b]"

    def test_roundtrip_pipe(self):
        """Test that tokenize followed by detokenize produces the escaped pipe form."""
        original = "a | b"
        tokenized = ReplacementUtils.tokenize(original)
        assert ReplacementUtils.detokenize(tokenized) == r"a \| b"

    def test_plain_text_unchanged(self):
        """Test that plain text with no tokenizable content is returned unchanged."""
        assert ReplacementUtils.detokenize("plain text") == "plain text"

    def test_empty_string(self):
        """Test that an empty string is returned unchanged."""
        assert ReplacementUtils.detokenize("") == ""


class TestTokenize:
    """Tests for the tokenize function."""

    def test_tokenizes_footnote_ref_and_pipe(self):
        """Test that all tokenizations are applied in a single call."""
        html = (
            "<sup><a id='note-ref-1'>1</a></sup> see "
            "<a (click)=\"ref.navigateToIntroFragment({fragmentId: 'note-3'})\">3</a> and |"
        )
        result = ReplacementUtils.tokenize(html)
        assert result == "@@FNREF_1@@ see @@FNCROSSREF_3@@ and @@PIPE@@"

    def test_tokenizes_crossref(self):
        """Test that a cross-reference anchor is tokenized to an FNCROSSREF token."""
        html = (
            "<a (click)=\"ref.navigateToIntroFragment({fragmentId: 'note-5'})\">5</a>"
        )
        assert ReplacementUtils.tokenize(html) == "@@FNCROSSREF_5@@"

    def test_tokenizes_footnote_ref(self):
        """Test that a footnote anchor is tokenized to an FNREF token."""
        html = "<sup><a id='note-ref-7'>7</a></sup>"
        assert ReplacementUtils.tokenize(html) == "@@FNREF_7@@"

    def test_tokenizes_pipe(self):
        """Test that a pipe character is tokenized to a PIPE token."""
        assert ReplacementUtils.tokenize("a | b") == "a @@PIPE@@ b"

    def test_plain_text_unchanged(self):
        """Test that plain text with no tokenizable content is returned unchanged."""
        assert ReplacementUtils.tokenize("plain text") == "plain text"

    def test_empty_string(self):
        """Test that an empty string is returned unchanged."""
        assert ReplacementUtils.tokenize("") == ""


class TestTokenizeFootnoteRefs:
    """Tests for the _tokenize_footnote_refs function."""

    def test_replaces_sup_anchor(self):
        """Test that a single-quoted footnote anchor is replaced with the correct FNREF token."""
        html = "<sup><a id='note-ref-3' href='#note-3'>3</a></sup>"
        assert ReplacementUtils._tokenize_footnote_refs(html) == "@@FNREF_3@@"

    def test_replaces_double_quoted_id(self):
        """Test that a double-quoted footnote anchor is replaced with the correct FNREF token."""
        html = '<sup><a id="note-ref-12" href="#note-12">12</a></sup>'
        assert ReplacementUtils._tokenize_footnote_refs(html) == "@@FNREF_12@@"

    def test_replaces_multiple_refs(self):
        """Test that every footnote anchor in the input is replaced."""
        html = (
            "text<sup><a id='note-ref-1'>1</a></sup>"
            " more<sup><a id='note-ref-2'>2</a></sup>"
        )
        result = ReplacementUtils._tokenize_footnote_refs(html)
        assert result == "text@@FNREF_1@@ more@@FNREF_2@@"

    def test_no_match_leaves_text_unchanged(self):
        """Test that the input is returned unchanged when no footnote anchors are present."""
        html = "<p>No footnotes here.</p>"
        assert ReplacementUtils._tokenize_footnote_refs(html) == html


class TestTokenizeFootnoteCrossrefs:
    """Tests for the _tokenize_footnote_crossrefs function."""

    def test_replaces_crossref_anchor(self):
        """Test that a cross-reference anchor is replaced with the correct FNCROSSREF token."""
        html = (
            '<a (click)="ref.navigateToIntroFragment('
            "{complexId: 'foo', fragmentId: 'note-18'})\">18</a>"
        )
        assert (
            ReplacementUtils._tokenize_footnote_crossrefs(html) == "@@FNCROSSREF_18@@"
        )

    def test_replaces_multiple_crossrefs(self):
        """Test that every cross-reference anchor in the input is replaced."""
        html = (
            "see <a (click)=\"ref.navigateToIntroFragment({fragmentId: 'note-3'})\">3</a>"
            " and <a (click)=\"ref.navigateToIntroFragment({fragmentId: 'note-7'})\">7</a>"
        )
        result = ReplacementUtils._tokenize_footnote_crossrefs(html)
        assert result == "see @@FNCROSSREF_3@@ and @@FNCROSSREF_7@@"

    def test_no_match_leaves_text_unchanged(self):
        """Test that the input is returned unchanged when no cross-reference anchors are present."""
        html = "<a href='#other'>link</a>"
        assert ReplacementUtils._tokenize_footnote_crossrefs(html) == html


class TestTokenizePipes:
    """Tests for the _tokenize_pipes function."""

    def test_replaces_pipe_in_text(self):
        """Test that a pipe character in plain text is replaced with the PIPE token."""
        assert ReplacementUtils._tokenize_pipes("a | b") == "a @@PIPE@@ b"

    def test_replaces_multiple_pipes(self):
        """Test that every pipe character in plain text is replaced."""
        assert (
            ReplacementUtils._tokenize_pipes("a | b | c") == "a @@PIPE@@ b @@PIPE@@ c"
        )

    def test_does_not_replace_pipe_inside_tag(self):
        """Test that a pipe inside an HTML tag attribute (e.g. a title) is left untouched."""
        html = "<a title='Vgl. A | B'>text</a>"
        assert ReplacementUtils._tokenize_pipes(html) == html

    def test_no_pipe_leaves_text_unchanged(self):
        """Test that the input is returned unchanged when no pipes are present."""
        assert ReplacementUtils._tokenize_pipes("no pipes here") == "no pipes here"


class TestDetokenizeFootnoteRefs:
    """Tests for the _detokenize_footnote_refs function."""

    def test_restores_token(self):
        """Test that an FNREF token is converted to the correct Markdown footnote reference."""
        assert ReplacementUtils._detokenize_footnote_refs("@@FNREF_3@@") == "[^3]"

    def test_restores_escaped_underscore_token(self):
        """Test that tokens with a markdownify-escaped underscore are handled correctly."""
        assert ReplacementUtils._detokenize_footnote_refs(r"@@FNREF\_5@@") == "[^5]"

    def test_restores_multiple_tokens(self):
        """Test that every FNREF token in the input is restored."""
        result = ReplacementUtils._detokenize_footnote_refs(
            "@@FNREF_1@@ and @@FNREF_2@@"
        )
        assert result == "[^1] and [^2]"

    def test_no_token_leaves_text_unchanged(self):
        """Test that the input is returned unchanged when no FNREF tokens are present."""
        assert ReplacementUtils._detokenize_footnote_refs("plain text") == "plain text"


class TestDetokenizeFootnoteCrossrefs:
    """Tests for the _detokenize_footnote_crossrefs function."""

    def test_restores_token(self):
        """Test that an FNCROSSREF token is converted to the correct inline link."""
        assert (
            ReplacementUtils._detokenize_footnote_crossrefs("@@FNCROSSREF_18@@")
            == "[18](#fn18)"
        )

    def test_restores_escaped_underscore_token(self):
        """Test that tokens with a markdownify-escaped underscore are handled correctly."""
        assert (
            ReplacementUtils._detokenize_footnote_crossrefs(r"@@FNCROSSREF\_4@@")
            == "[4](#fn4)"
        )

    def test_restores_multiple_tokens(self):
        """Test that every FNCROSSREF token in the input is restored."""
        result = ReplacementUtils._detokenize_footnote_crossrefs(
            "see @@FNCROSSREF_3@@ and @@FNCROSSREF_7@@"
        )
        assert result == "see [3](#fn3) and [7](#fn7)"

    def test_no_token_leaves_text_unchanged(self):
        """Test that the input is returned unchanged when no FNCROSSREF tokens are present."""
        assert (
            ReplacementUtils._detokenize_footnote_crossrefs("plain text")
            == "plain text"
        )


class TestDetokenizePipes:
    """Tests for the _detokenize_pipes function."""

    def test_restores_token(self):
        """Test that a PIPE token is converted to an escaped Markdown pipe."""
        assert ReplacementUtils._detokenize_pipes("a @@PIPE@@ b") == r"a \| b"

    def test_restores_multiple_tokens(self):
        """Test that every PIPE token in the input is restored."""
        assert (
            ReplacementUtils._detokenize_pipes("a @@PIPE@@ b @@PIPE@@ c")
            == r"a \| b \| c"
        )

    def test_no_token_leaves_text_unchanged(self):
        """Test that the input is returned unchanged when no PIPE tokens are present."""
        assert ReplacementUtils._detokenize_pipes("no pipes") == "no pipes"


class TestUnescapeBrackets:
    """Tests for the _unescape_brackets function."""

    def test_unescapes_opening_bracket(self):
        """Test that a markdownify-escaped opening bracket is unescaped."""
        assert ReplacementUtils._unescape_brackets(r"\[b]") == "[b]"

    def test_unescapes_closing_bracket(self):
        """Test that a markdownify-escaped closing bracket is unescaped."""
        assert ReplacementUtils._unescape_brackets(r"[b\]") == "[b]"

    def test_unescapes_both_brackets(self):
        """Test that both escaped brackets in a pair are unescaped."""
        assert ReplacementUtils._unescape_brackets(r"\[b\]") == "[b]"

    def test_unescapes_multiple_occurrences(self):
        """Test that every escaped bracket in the input is unescaped."""
        assert ReplacementUtils._unescape_brackets(r"\[b] and \[r]") == "[b] and [r]"

    def test_plain_text_unchanged(self):
        """Test that text without escaped brackets is returned unchanged."""
        assert ReplacementUtils._unescape_brackets("plain text") == "plain text"


class TestMakeToken:
    """Tests for the _make_token function."""

    def test_builds_fnref_token(self):
        """Test that a correct FNREF token is built from a prefix and number."""
        assert ReplacementUtils._make_token("@@FNREF", "5") == "@@FNREF_5@@"

    def test_builds_fncrossref_token(self):
        """Test that a correct FNCROSSREF token is built from a prefix and number."""
        assert ReplacementUtils._make_token("@@FNCROSSREF", "18") == "@@FNCROSSREF_18@@"

    def test_uses_token_constants(self):
        """Test that it works correctly when called with the class TOKEN constants."""
        result = ReplacementUtils._make_token(ReplacementUtils._TOKEN_FNREF, "3")
        assert result == "@@FNREF_3@@"


class TestMakeTokenPattern:
    """Tests for the _make_token_pattern function."""

    def test_matches_unescaped_token(self):
        """Test that the pattern matches a normally formatted numbered token."""
        pattern = ReplacementUtils._make_token_pattern(ReplacementUtils._TOKEN_FNREF)
        assert re.search(pattern, "@@FNREF_7@@")

    def test_matches_escaped_underscore_token(self):
        """Test that the pattern matches a token where markdownify has escaped the underscore."""
        pattern = ReplacementUtils._make_token_pattern(ReplacementUtils._TOKEN_FNREF)
        assert re.search(pattern, r"@@FNREF\_7@@")

    def test_does_not_match_wrong_prefix(self):
        """Test that the pattern does not match a token with a different prefix."""
        pattern = ReplacementUtils._make_token_pattern(ReplacementUtils._TOKEN_FNREF)
        assert not re.search(pattern, "@@FNCROSSREF_7@@")
