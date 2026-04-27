"""Utility functions for replacing or detokenizing special tokens in text,
such as footnote references and pipes."""

import re


class ReplacementUtils:
    """A class that contains utility functions for replacing or detokenizing special tokens in text,
    such as footnote references and pipes."""

    _TOKEN_PIPE = "@@PIPE@@"
    _TOKEN_FNREF = "@@FNREF"
    _TOKEN_FNCROSSREF = "@@FNCROSSREF"
    _TOKEN_SUFFIX = "@@"

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace in the final Markdown string.

        Replaces non-breaking spaces (``\\xa0``) with regular spaces, collapses
        runs of three or more newlines to two, and strips leading/trailing whitespace.

        Args:
            text (str): The string to normalize.

        Returns:
            str: The normalized string.
        """
        text = text.replace("\xa0", " ")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def detokenize(text: str) -> str:
        """Restore all tokens in Markdown text after HTML-to-Markdown conversion.

        Applies detokenization for footnote references, cross-references, pipes,
        and markdownify-escaped brackets.

        Args:
            text (str): The Markdown string containing tokens to restore.

        Returns:
            str: The string with all tokens replaced by their Markdown equivalents.
        """
        text = ReplacementUtils._detokenize_footnote_refs(text)
        text = ReplacementUtils._detokenize_footnote_crossrefs(text)
        text = ReplacementUtils._detokenize_pipes(text)
        text = ReplacementUtils._unescape_brackets(text)
        return text

    @staticmethod
    def tokenize(html: str) -> str:
        """Replace special HTML constructs with placeholder tokens before Markdown conversion.

        Tokenizes footnote reference anchors, internal cross-reference anchors,
        and literal pipe characters so they survive HTML-to-Markdown conversion intact.

        Args:
            html (str): The HTML string to tokenize.

        Returns:
            str: The HTML string with special constructs replaced by tokens.
        """
        html = ReplacementUtils._tokenize_footnote_refs(html)
        html = ReplacementUtils._tokenize_footnote_crossrefs(html)
        html = ReplacementUtils._tokenize_pipes(html)
        return html

    @staticmethod
    def _detokenize_footnote_refs(text: str) -> str:
        """Replace ``@@FNREF_N@@`` tokens with Markdown footnote references ``[^N]``.

        Args:
            text (str): The string containing FNREF tokens.

        Returns:
            str: The string with FNREF tokens replaced.
        """
        return re.sub(
            ReplacementUtils._make_token_pattern(ReplacementUtils._TOKEN_FNREF),
            r"[^\1]",
            text,
        )

    @staticmethod
    def _detokenize_footnote_crossrefs(text: str) -> str:
        """Replace ``@@FNCROSSREF_N@@`` tokens with inline links ``[N](#fnN)``.

        Args:
            text (str): The string containing FNCROSSREF tokens.

        Returns:
            str: The string with FNCROSSREF tokens replaced.
        """
        return re.sub(
            ReplacementUtils._make_token_pattern(ReplacementUtils._TOKEN_FNCROSSREF),
            lambda m: f"[{m.group(1)}](#fn{m.group(1)})",
            text,
        )

    @staticmethod
    def _detokenize_pipes(text: str) -> str:
        """Replace ``@@PIPE@@`` tokens with escaped Markdown pipes ``\\|``.

        Args:
            text (str): The string containing PIPE tokens.

        Returns:
            str: The string with PIPE tokens replaced.
        """
        return text.replace(ReplacementUtils._TOKEN_PIPE, r"\|")

    @staticmethod
    def _tokenize_footnote_crossrefs(html: str) -> str:
        """Replace internal cross-reference anchors with ``@@FNCROSSREF_N@@`` tokens.

        Matches anchors like::

            <a (click)="ref.navigateToIntroFragment({..., fragmentId: 'note-18'})">18</a>

        Args:
            html (str): The HTML string to tokenize.

        Returns:
            str: The HTML string with cross-reference anchors replaced by tokens.
        """
        return re.sub(
            r"<a\b[^>]*fragmentId:\s*'note-(\d+)'[^>]*>\s*\d+\s*</a>",
            lambda m: ReplacementUtils._make_token(
                ReplacementUtils._TOKEN_FNCROSSREF, m.group(1)
            ),
            html,
            flags=re.IGNORECASE,
        )

    @staticmethod
    def _tokenize_footnote_refs(html: str) -> str:
        """Replace footnote ``<sup><a id='note-ref-N'>`` anchors with ``@@FNREF_N@@`` tokens.

        Args:
            html (str): The HTML string to tokenize.

        Returns:
            str: The HTML string with footnote ref anchors replaced by tokens.
        """
        return re.sub(
            r"<sup>\s*<a\b[^>]*\bid=(['\"])note-ref-(\d+)\1[^>]*>[\s\S]*?</a>\s*</sup>",
            lambda m: ReplacementUtils._make_token(
                ReplacementUtils._TOKEN_FNREF, m.group(2)
            ),
            html,
            flags=re.IGNORECASE,
        )

    @staticmethod
    def _tokenize_pipes(html: str) -> str:
        """Replace literal pipe characters in text content with ``@@PIPE@@`` tokens.

        Uses a negative lookahead to skip pipes inside HTML tag attributes.
        Tokens are restored as ``\\|`` after Markdown conversion to prevent
        them from being interpreted as Markdown table cell separators.

        Args:
            html (str): The HTML string to tokenize.

        Returns:
            str: The HTML string with bare pipe characters replaced by tokens.
        """
        return re.sub(r"\|(?![^<>]*>)", ReplacementUtils._TOKEN_PIPE, html)

    @staticmethod
    def _unescape_brackets(text: str) -> str:
        """Unescape ``\\[`` and ``\\]`` that markdownify over-escapes in body text.

        Args:
            text (str): The string to unescape.

        Returns:
            str: The string with escaped brackets replaced by literal brackets.
        """
        return text.replace(r"\[", "[").replace(r"\]", "]")

    @staticmethod
    def _make_token(prefix: str, number: str) -> str:
        """Build a numbered token string, e.g. ``@@FNREF_5@@``.

        Args:
            prefix (str): The token prefix constant (e.g. ``@@FNREF``).
            number (str): The note number as a string.

        Returns:
            str: The assembled token string.
        """
        return f"{prefix}_{number}{ReplacementUtils._TOKEN_SUFFIX}"

    @staticmethod
    def _make_token_pattern(prefix: str) -> str:
        """Build a regex pattern that matches a numbered token for the given prefix.

        Tolerates markdownify-escaped underscores (``\\_``) between the prefix
        and the digit group.

        Args:
            prefix (str): The token prefix constant (e.g. ``@@FNREF``).

        Returns:
            str: A regex pattern string with one capturing group for the note number.
        """
        return prefix + r"\\?_(\d+)" + ReplacementUtils._TOKEN_SUFFIX
