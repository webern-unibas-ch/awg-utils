"""Utility functions for text replacement and formatting."""

import re


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
        """
        Adds report fragment links to bold formatted characters in a given text.

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
        """
        Escapes curly brackets in a given text.

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
    def replace_glyphs(text: str) -> str:
        """
        Replaces glyph strings in a given text.

        Args:
            text (str): The given text.

        Returns:
            str: The replaced text.
        """
        glyphs = [
            "a",
            "b",
            "bb",
            "#",
            "x",
            "f",
            "ff",
            "fff",
            "ffff",
            "mf",
            "mp",
            "p",
            "pp",
            "ppp",
            "pppp",
            "ped",
            "sf",
            "sfz",
            "sp",
            "Achtelnote",
            "Ganze Note",
            "Halbe Note",
            "Punktierte Halbe Note",
            "Sechzehntelnote",
            "Viertelnote",
        ]
        glyph_pattern = "|".join(re.escape(glyph) for glyph in glyphs)

        # Match pattern for glyphs in square brackets, but not followed by a hyphen
        match_pattern = rf"\[({glyph_pattern})\](?!-)"

        accid_glyphs = {"a", "b", "bb", "#", "x"}
        note_glyphs = {
            "Achtelnote",
            "Ganze Note",
            "Halbe Note",
            "Punktierte Halbe Note",
            "Sechzehntelnote",
            "Viertelnote",
        }

        def replace_glyph(match):
            glyph = match.group(1)
            css_class = (
                "glyph accid"
                if glyph in accid_glyphs
                else "glyph note"
                if glyph in note_glyphs
                else "glyph"
            )
            return f"<span class='{css_class}'>{{{{ref.getGlyph('{glyph}')}}}}</span>"

        return re.sub(match_pattern, replace_glyph, text)
