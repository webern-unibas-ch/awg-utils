"""Utility functions for handling Textcritics-specific content."""

import copy
from typing import List

from bs4 import BeautifulSoup, Tag

from utils.default_objects import (
    DEFAULT_TEXTCRITICAL_COMMENT,
    DEFAULT_TEXTCRITICAL_COMMENT_BLOCK,
    DEFAULT_TEXTCRITICS,
    DEFAULT_TEXTCRITICS_LIST,
)
from utils.stripping_utils import StrippingUtils
from utils.typed_classes import TextCritics, TextcriticalComment, TextcriticsList
from utils.replacement_utils import ReplacementUtils


class TextcriticsUtils:  # pylint: disable=too-few-public-methods
    """A class that contains utility functions for the conversion
    of textcritics content from Word to JSON."""

    ############################################
    # Public class function: create_textcritics
    ############################################
    def create_textcritics(self, soup: BeautifulSoup) -> TextCritics:
        """
        Creates a list of textcritics based on the given soup elements.

        Args:
            soup (BeautifulSoup): A BeautifulSoup object representing the document.

        Returns:
            A SourceList object containing a list of SourceDescription objects.
        """
        textcritics_list = copy.deepcopy(DEFAULT_TEXTCRITICS_LIST)

        # Find all table tags in soup
        tables = soup.find_all("table")

        # Iterate over tables and create textcritics/corrections lists
        for table_index, table in enumerate(tables):
            self._process_table(textcritics_list, table, table_index)

        # Remove empty lists
        for key in ("textcritics", "corrections"):
            if not textcritics_list[key]:
                textcritics_list.pop(key)

        return textcritics_list

    ############################################
    # Private method: _process_table
    ############################################
    def _process_table(
        self, textcritics_list: TextcriticsList, table: Tag, table_index: int
    ) -> TextcriticsList:
        """
        Processes a table and extracts textcritical comments from it.

        Args:
            table (Tag): A BeautifulSoup `Tag` object representing a table.
            table_index (int): The index of the table in the list of tables.
        """
        textcritics = copy.deepcopy(DEFAULT_TEXTCRITICS)
        textcritics["commentary"]["comments"] = []

        rows_in_table = table.find_all("tr")
        block_index = -1

        # Create a default comment block with an empty blockHeader
        default_comment_block = copy.deepcopy(DEFAULT_TEXTCRITICAL_COMMENT_BLOCK)
        default_comment_block["blockHeader"] = ""
        textcritics["commentary"]["comments"].append(default_comment_block)
        block_index += 1

        textcritics = self._process_table_rows(textcritics, rows_in_table, block_index)

        print(f"Appending textcritics for table {table_index + 1}...")

        # Determine if the table is for corrections based on the presence of "Korrektur"
        is_corrections = "Korrektur" in rows_in_table[0].find_all("td")[-1].get_text(
            strip=True
        )

        # Adjust textcritics output based on the presence of corrections
        if is_corrections:
            self._process_corrections(textcritics)
            textcritics_list["corrections"].append(textcritics)
        else:
            textcritics_list["textcritics"].append(textcritics)

        return textcritics_list

    ############################################
    # Helper function: _process_corrections
    ############################################

    def _process_corrections(self, textcritics: TextCritics) -> None:
        """
        Strips corrections-specific fields from a textcritics object in place.

        Args:
            textcritics (dict): The textcritics object to mutate.
        """
        textcritics.pop("linkBoxes", None)  # Remove linkBoxes property if it exists

        # Remove svgGroupId property from textcritical comments
        for comment_block in textcritics["commentary"]["comments"]:
            for comment in comment_block["blockComments"]:
                comment.pop(
                    "svgGroupId", None
                )  # Remove svgGroupId property if it exists

    ############################################
    # Helper function: _process_table_rows
    ############################################
    def _process_table_rows(self, textcritics, rows_in_table, block_index):
        """
        Processes the rows in a table and extracts textcritical comments from them.

        Args:
            textcritics: A dictionary representing the textcritical comments.
            rows_in_table: A list of BeautifulSoup `Tag` objects representing rows in a table.
            block_index: The index of the current comment block.

        Returns:
            A dictionary representing the textcritical comments.
        """
        comment_id = 1

        for row in rows_in_table[1:]:
            columns_in_row = row.find_all("td")

            # Check if the first td has a colspan attribute
            if "colspan" in columns_in_row[0].attrs:
                # If the default comment block is empty, remove it
                if not textcritics["commentary"]["comments"][0]["blockComments"]:
                    textcritics["commentary"]["comments"].pop(0)
                    block_index -= 1

                comment_block = copy.deepcopy(DEFAULT_TEXTCRITICAL_COMMENT_BLOCK)
                comment_block["blockHeader"] = StrippingUtils.strip_tag_and_clean(
                    columns_in_row[0], "td"
                )
                textcritics["commentary"]["comments"].append(comment_block)
                block_index += 1

                continue

            if block_index >= 0:
                comment = self._process_comment(columns_in_row)
                comment["svgGroupId"] = f"g-tkk-{comment_id}"
                textcritics["commentary"]["comments"][block_index][
                    "blockComments"
                ].append(comment)
                comment_id += 1

        return textcritics

    ############################################
    # Helper function: _process_comment
    ############################################

    def _process_comment(self, columns_in_row: List[Tag]) -> TextcriticalComment:
        """
        Processes a textcritical comment object from a list of BeautifulSoup `Tag` objects.

        Args:
            columns_in_row (List[Tag]): A list of BeautifulSoup `Tag` objects
                representing columns in a row.

        Returns:
            TextcriticalComment: A dictionary representing the textcritical comment.
        """
        comment = copy.deepcopy(DEFAULT_TEXTCRITICAL_COMMENT)

        comment["measure"] = StrippingUtils.strip_tag_and_clean(columns_in_row[0], "td")
        comment["system"] = StrippingUtils.strip_tag_and_clean(columns_in_row[1], "td")
        comment["position"] = StrippingUtils.strip_tag_and_clean(
            columns_in_row[2], "td"
        )

        comment_text = StrippingUtils.strip_tag_and_clean(columns_in_row[3], "td")
        comment_text = ReplacementUtils.escape_curly_brackets(comment_text)
        comment_text = ReplacementUtils.add_report_fragment_links(comment_text)
        comment_text = ReplacementUtils.replace_glyphs(comment_text)
        comment["comment"] = comment_text

        return comment
