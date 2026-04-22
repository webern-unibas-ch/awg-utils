"""
Utility functions for finding paragraph indices in source description conversion.

This module should not be run directly. Instead, run the `convert_source_description.py` module.
"""

import re
from typing import List, Tuple

from bs4 import Tag

from utils.paragraph_utils import ParagraphUtils


############################################
# Public class: IndexUtils
############################################
class IndexUtils:
    """A class that contains utility functions for finding paragraph indices
    in source description conversion."""

    # Pattern for a bold-formatted siglum paragraph.
    # Group 1: siglum letter with optional opening bracket, e.g. '[A' or 'A'
    # Group 3: superscript addendum text, e.g. 'c', 'H', 'F1', 'F1–2' (optional)
    # Group 5: optional closing bracket ']'
    # Matches: A, [A], Ac, [Ac], AH, [AH], AF1–2, [AF1–2], etc.
    SIGLUM_PATTERN = re.compile(
        r"^<p>\s*<strong>\s*(\[?[A-Z])(<sup>([a-zA-Z][0-9]?(–[0-9])?)?</sup>)?(\]?)\s*</strong>\s*</p>$"
    )

    ############################################
    # Public class function: find_siglum_indices
    ############################################

    @staticmethod
    def find_siglum_indices(paras: List[Tag]) -> List[int]:
        """
        Finds the indices of paragraphs in a list of BeautifulSoup `Tag` objects
            that contain a single bold siglum.

        Args:
            paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing paragraphs.

        Returns:
            A list of integers representing the indices of the paragraphs
                that contain a single bold siglum.
        """
        return [
            i
            for i, para in enumerate(paras)
            if IndexUtils.SIGLUM_PATTERN.match(str(para))
        ]

    ############################################
    # Public class function: find_contents_indices
    ############################################

    @staticmethod
    def find_contents_indices(paras: List[Tag]) -> Tuple[int, int]:
        """
        Finds the indices of the contents and comments paragraphs in a list of
        BeautifulSoup `Tag` objects.

        Args:
            paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing paragraphs.

        Returns:
            Tuple[int, int]: A tuple of (contents_start_index, contents_end_index).
                contents_start_index is -1 if 'Inhalt:' is not found.
                contents_end_index is len(paras) - 1 if no comments label is found.
        """
        contents_start_index = ParagraphUtils.get_paragraph_index_by_label(
            "Inhalt:", paras
        )

        comments_labels = ["Textkritischer Kommentar:", "Textkritische Anmerkungen:"]
        contents_end_index = next(
            (
                ParagraphUtils.get_paragraph_index_by_label(label, paras)
                for label in comments_labels
                if ParagraphUtils.get_paragraph_index_by_label(label, paras) != -1
            ),
            len(paras),
        )

        # Ensure contents_end_index is within valid range
        if contents_end_index >= len(paras):
            contents_end_index = len(paras) - 1

        return contents_start_index, contents_end_index
