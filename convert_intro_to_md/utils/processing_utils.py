"""Utility functions for processing intro content and notes."""

import sys
from typing import Dict, List

from utils.html_utils import HTMLUtils
from utils.replacement_utils import ReplacementUtils


class ProcessingUtils:
    """A class that contains utility functions for processing intro content and notes."""

    @staticmethod
    def assemble_markdown(md_lines: List[str]) -> str:
        """Join Markdown lines, normalize whitespace, and append a trailing newline.

        Args:
            md_lines (List[str]): The list of Markdown lines to assemble.

        Returns:
            str: The fully normalized Markdown string with a trailing newline.
        """
        return ReplacementUtils.normalize_whitespace("\n".join(md_lines)) + "\n"

    @staticmethod
    def process_block_content(block_content: List[str]) -> List[str]:
        """Convert a list of HTML fragment strings to Markdown lines.

        Args:
            block_content (List[str]): The list of HTML fragment strings to convert.

        Returns:
            List[str]: A flat list of Markdown lines with blank lines between entries.
        """
        lines: List[str] = []
        for html in HTMLUtils.group_block_content(block_content):
            result = HTMLUtils.html_to_md(html)
            if result:
                lines.append(result)
                lines.append("")
        return lines

    @staticmethod
    def process_block_notes(block_notes: List[str], notes: Dict[str, str]) -> None:
        """Parse blockNotes HTML strings and populate the notes dictionary.

        Args:
            block_notes (List[str]): The list of raw blockNote HTML strings to parse.
            notes (Dict[str, str]): The dictionary to populate, mapping note number
                strings to stripped note HTML content.
        """
        for block_note in block_notes:
            if parsed := HTMLUtils.parse_block_note(block_note):
                num, content = parsed
                if num in notes:
                    print(
                        f"Duplicate note number {num!r} encountered; keeping first.",
                        file=sys.stderr,
                    )
                else:
                    notes[num] = content

    @staticmethod
    def process_end_notes(notes: Dict[str, str], locale: str) -> List[str]:
        """Build the footnotes section lines from a note number to HTML dictionary.

        Args:
            notes (Dict[str, str]): A mapping of note number strings to note HTML content.
            locale (str): The locale string (e.g. ``'en'`` or ``'de'``) used to select
                the section header.

        Returns:
            List[str]: A list of Markdown lines forming the footnotes section,
            or an empty list if notes is empty.
        """
        if not notes:
            return []
        header = "Notes" if locale == "en" else "Anmerkungen"
        lines = ["---", "", f"## {header}", ""]
        for num in sorted(notes.keys(), key=int):
            lines.append(f"[^{num}]: | {HTMLUtils.html_to_md(notes[num])}")
            lines.append("")
        return lines
