"""Paragraph lookup and extraction helpers for conversion utilities."""

import re
from typing import List, Optional

from bs4 import Tag

from utils.constants import FULL_STOP, P_TAG, SEMICOLON
from utils.stripping_utils import StrippingUtils


############################################
# Public class: ParagraphUtils
############################################
class ParagraphUtils:
    """Helpers for finding and extracting labeled paragraph content."""

    ############################################
    # Public class function: get_paragraph_content_by_label
    ############################################
    @staticmethod
    def get_paragraph_content_by_label(label: str, paras: List[Tag]) -> List[str]:
        """Return content lines for the paragraph identified by a leading label."""
        content_paragraph = ParagraphUtils._find_tag_with_label_in_soup(label, paras)
        content_lines = []

        if content_paragraph is None:
            return content_lines

        stripped_content = StrippingUtils.strip_tag(content_paragraph, P_TAG)
        initial_content = StrippingUtils.strip_by_delimiter(stripped_content, label)[1]

        content_lines.append(
            initial_content.strip().rstrip(FULL_STOP).rstrip(SEMICOLON)
        )

        if initial_content.endswith(SEMICOLON):
            sibling = content_paragraph.next_sibling

            while sibling is not None and sibling.name == P_TAG:
                sibling_content = StrippingUtils.strip_tag(sibling, P_TAG)
                if sibling_content.endswith(FULL_STOP) or sibling_content.endswith(
                    SEMICOLON
                ):
                    content_lines.append(
                        sibling_content.strip().rstrip(FULL_STOP).rstrip(SEMICOLON)
                    )
                    if sibling_content.endswith(FULL_STOP):
                        break
                else:
                    break

                sibling = sibling.next_sibling

        return content_lines

    ############################################
    # Public class function: get_paragraph_index_by_label
    ############################################
    @staticmethod
    def get_paragraph_index_by_label(label: str, paras: List[Tag]) -> int:
        """Return the index of the first paragraph containing the given label."""
        tag_with_label = ParagraphUtils._find_tag_with_label_in_soup(label, paras)
        try:
            return paras.index(tag_with_label)
        except ValueError:
            return -1

    ############################################
    # Helper function: _find_tag_with_label_in_soup
    ############################################
    @staticmethod
    def _find_tag_with_label_in_soup(label: str, paras: List[Tag]) -> Optional[Tag]:
        """Search for the first paragraph tag containing the given label."""
        if not label:
            return None
        for para in paras:
            if para.find(string=re.compile(label)):
                return para
        return None
