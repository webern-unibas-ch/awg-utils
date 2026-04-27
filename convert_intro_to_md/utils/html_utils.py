"""Utility functions for handling HTML content in intro processing."""

import re
from typing import List

from markdownify import markdownify as md

from utils.replacement_utils import ReplacementUtils


class HTMLUtils:
    """A class that contains utility functions for handling HTML content in intro processing."""

    @staticmethod
    def group_block_content(block_content: List[str]) -> List[str]:
        """Group block content items, combining consecutive small paragraphs into one blockquote.

        Args:
            block_content (List[str]): The list of HTML fragment strings to group.

        Returns:
            List[str]: A new list where runs of small paragraphs are replaced by a
            single blockquote HTML string.
        """
        result = []
        i = 0
        while i < len(block_content):
            if HTMLUtils._is_small_para(block_content[i]):
                group = [block_content[i]]
                while i + 1 < len(block_content) and HTMLUtils._is_small_para(
                    block_content[i + 1]
                ):
                    i += 1
                    group.append(block_content[i])
                result.append(HTMLUtils._combine_small_paras(group))
            else:
                result.append(block_content[i])
            i += 1
        return result

    @staticmethod
    def html_to_md(html: str) -> str:
        """Convert an HTML string to Markdown.

        Args:
            html (str): The HTML string to convert.

        Returns:
            str: The converted Markdown string, or an empty string if the input is
            empty or not a string.
        """
        if not html or not isinstance(html, str):
            return ""

        # Tokenize footnote references, cross-references, and pipes before stripping bindings
        html = ReplacementUtils.tokenize(html)

        # Convert HTML to Markdown and detokenize
        return ReplacementUtils.detokenize(
            md(HTMLUtils._strip_angular_bindings(html), heading_style="atx").strip()
        )

    @staticmethod
    def parse_block_note(note_html: str) -> tuple[str, str] | None:
        """Parse a blockNote HTML string into its note number and stripped HTML content.

        Args:
            note_html (str): The raw blockNote HTML string.

        Returns:
            tuple[str, str] | None: A (note_number, stripped_html) pair if a note id is found,
            or None if no note number could be extracted.
        """
        num = HTMLUtils._extract_note_number(note_html)
        return (num, HTMLUtils._strip_note_html(note_html)) if num else None

    @staticmethod
    def _combine_small_paras(block_content: List[str]) -> str:
        """Wrap a list of small-paragraph HTML strings in a single blockquote element.

        Strips the outer <p> tags from each item, then wraps all inner contents
        in plain <p> tags inside a <blockquote>.

        Args:
            block_content (List[str]): A list of small-paragraph HTML strings to combine.

        Returns:
            str: A single <blockquote> HTML string containing all inner paragraphs.
        """
        parts = []
        for line_content in block_content:
            inner = re.sub(r"^<p\b[^>]*>", "", line_content, flags=re.IGNORECASE)
            inner = re.sub(r"</p>\s*$", "", inner, flags=re.IGNORECASE)
            parts.append(f"<p>{inner.strip()}</p>")
        return f"<blockquote>{''.join(parts)}</blockquote>"

    @staticmethod
    def _extract_note_number(note_html: str) -> str | None:
        """Extract the note number from a blockNote HTML string.

        Args:
            note_html (str): The raw blockNote HTML string.

        Returns:
            str | None: The note number as a string if an id matching note-N is found,
            or None if no match is found.
        """
        id_match = re.search(r"\bid=(['\"])note-(\d+)\1", note_html, re.IGNORECASE)
        return id_match.group(2) if id_match else None

    @staticmethod
    def _is_small_para(line_content: str) -> bool:
        """Check whether an HTML string is a small paragraph.

        Args:
            line_content (str): The HTML fragment string to test.

        Returns:
            bool: True if the fragment is a small (non-list) paragraph, False otherwise.
        """
        return bool(
            re.match(
                r"<p\b(?=[^>]*\bsmall\b)(?![^>]*\blist\b)[^>]*>",
                line_content.lstrip(),
                re.IGNORECASE,
            )
        )

    @staticmethod
    def _strip_angular_bindings(html: str) -> str:
        """Strip Angular event bindings of the form ``(eventName)="..."`` or ``(eventName)='...'``.

        Args:
            html (str): The HTML string to strip.

        Returns:
            str: The HTML string with all Angular event binding attributes removed.
        """
        html = re.sub(r'\s\(\w+\)="[^"]*"', "", html)
        html = re.sub(r"\s\(\w+\)='[^']*'", "", html)
        return html

    @staticmethod
    def _strip_note_html(note_html: str) -> str:
        """Strip the backlink anchor, pipe separator, and wrapping <p> tags from a note HTML string.

        Args:
            note_html (str): The raw note HTML string.

        Returns:
            str: The stripped inner HTML content of the note.
        """
        inner = re.sub(
            r"<a\b[^>]*class=(['\"])[^'\"]*note-backlink[^'\"]*\1[^>]*>[\s\S]*?</a>\s*\|\s*",
            "",
            note_html,
            flags=re.IGNORECASE,
        )
        inner = re.sub(r"^<p\b[^>]*>", "", inner, flags=re.IGNORECASE)
        inner = re.sub(r"</p>\s*$", "", inner, flags=re.IGNORECASE)
        return inner.strip()
