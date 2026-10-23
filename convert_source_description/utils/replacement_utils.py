"""Utility functions for text replacement and formatting."""

import html
import re
from functools import lru_cache


############################################
# Public class: ReplacementUtils
############################################
class ReplacementUtils:
    """A class that contains utility functions for text replacement and formatting."""

    ############################################
    # Public static method: add_report_fragment_links
    ############################################
    @staticmethod
    def add_report_fragment_links(text: str) -> str:
        """Adds report fragment links to bold formatted characters in a given text.

        Args:
            text (str): The given text.

        Returns:
            str: The text with bold characters replaced by report fragment links.
        """
        text = re.sub(
            r"<strong>(.*?)</strong>",
            (
                r'<a (click)="ref.navigateToReportFragment('
                r"{complexId: 'TODO', fragmentId: 'source_\1'}"
                r')"><strong>\1</strong></a>'
            ),
            text,
        )

        return text

    ############################################
    # Public static method: escape_curly_brackets
    ############################################
    @staticmethod
    def escape_curly_brackets(text: str) -> str:
        """Escapes curly brackets in a given text.

        Args:
            text (str): The given text.

        Returns:
            str: The escaped text.
        """
        # Replace curly brackets with placeholders to avoid duplicated escaping
        text = text.replace("{", "__LEFT_CURLY_BRACKET__").replace(
            "}", "__RIGHT_CURLY_BRACKET__"
        )
        # Escape curly brackets
        text = text.replace("__LEFT_CURLY_BRACKET__", "{{ '{' }}").replace(
            "__RIGHT_CURLY_BRACKET__", "{{ '}' }}"
        )
        return text

    ############################################
    # Public static method: replace_glyphs
    ############################################
    @staticmethod
    def replace_glyphs(text: str, glyphs: dict[str, str]) -> str:
        """Replaces glyph strings in a given text.

        The text is HTML-serialized, so glyph names arrive escaped
        (e.g. ``[&gt;]`` for ``[>]``) and are matched in that form.

        Args:
            text (str): The given text.
            glyphs (dict[str, str]): The CSS class for each glyph name in square brackets,
                as read by ``GlyphUtils.read_glyphs``.

        Returns:
            str: The replaced text.
        """
        if not glyphs:
            return text

        def replace_glyph(match):
            glyph = html.unescape(match.group(1))
            return f"<span class='{glyphs[glyph]}'>{{{{ref.getGlyph('{glyph}')}}}}</span>"

        return ReplacementUtils._glyph_pattern(tuple(glyphs)).sub(replace_glyph, text)

    ############################################
    # Private static method: _glyph_pattern
    ############################################
    @staticmethod
    @lru_cache
    def _glyph_pattern(glyph_names: tuple[str, ...]) -> re.Pattern:
        """Compiles the match pattern for the given glyph names, once per name tuple.

        Args:
            glyph_names (tuple[str, ...]): The glyph names in square brackets.

        Returns:
            re.Pattern: The pattern matching the HTML-escaped glyph names,
                but not if followed by a hyphen.
        """
        glyph_pattern = "|".join(
            re.escape(html.escape(glyph, quote=False)) for glyph in glyph_names
        )
        return re.compile(rf"({glyph_pattern})(?!-)")
