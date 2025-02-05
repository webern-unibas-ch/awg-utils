"""
Auxiliary functions supporting the conversion process from Word source descriptions to JSON format.

This module should not be run directly. Instead, run the `convert_source_description.py` module.
"""

import copy
import re
from typing import List, Optional, Tuple

from bs4 import Tag

from typed_classes import (
    System,
    Folio,
    ContentItem,
    TextCritics,
    TextcriticsList,
    WritingInstruments,
    Description,
    SourceDescription,
    TextcriticalComment
)
from default_objects import (
    defaultSourceDescription,
    defaultDescription,
    defaultContentItem,
    defaultFolio,
    defaultSystem,
    defaultRow,
    defaultTextcritics,
    defaultTextcriticalComment,
    defaultTextcriticalCommentBlock,
)


############################################
# Helper constants
############################################
FOLIO_STR = "Bl."
M_SIGLE = "M "
M_STAR_SIGLE = "M* "
MEASURE_STR = "T."
PAGE_STR = "S."
ROWTABLE_SHEET_ID = "SkRT"
STAR_STR = "star"
SYSTEM_STR = "System"

COLON = ":"
COMMA = ","
DOT = "."
PARENTHESIS = "("
SEMICOLON = ";"
SLASH = "/"
STAR = "*"
UNDERSCORE = "_"

P_TAG = "p"
STRONG_TAG = "strong"
SUP_TAG = "sup"


############################################
# Public class: ConversionHelperUtils
############################################
class ConversionUtilsHelper:
    """A class that contains utility helper functions for the conversion of source descriptions
    from Word to JSON."""

    #############################################
    # Public method: create_source_description
    #############################################
    def create_source_description(self, paras: List[Tag]) -> SourceDescription:
        """Create a source description dictionary from a list of BeautifulSoup `Tag` objects.

        Args:
            paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing paragraphs.

        Returns:
            SourceDescription: A dictionary representing the source description.
        """
        source_description = copy.deepcopy(defaultSourceDescription)

        # Get siglum
        siglum, siglum_addendum = self._get_siglum(paras)

        # If existing, remove square brackets from siglum and set missing flag.
        if siglum.startswith("[") and siglum.endswith("]"):
            siglum = siglum[1:-1]
            items = list(source_description.items())
            items.insert(3, ("missing", True))
            source_description = dict(items)

        siglum_string = siglum + siglum_addendum
        source_id = "source_" + siglum_string if siglum_string else ""

        # Update source description
        source_description["id"] = source_id
        source_description["siglum"] = siglum
        source_description["siglumAddendum"] = siglum_addendum
        source_description["type"] = self._strip_tag(paras[1], P_TAG) or ""
        source_description["location"] = self._strip_tag(paras[2], P_TAG) or ""
        source_description["description"] = self._get_description(paras, source_id)

        return source_description

    ############################################
    # Public method: find_siglum_indices
    ############################################

    def find_siglum_indices(self, paras: List[Tag]) -> List[int]:
        """
        Finds the indices of paragraphs in a list of BeautifulSoup `Tag` objects
            that contain a single bold siglum.

        Args:
            paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing paragraphs.

        Returns:
            A list of integers representing the indices of the paragraphs
                that contain a single bold siglum.
        """
        # pattern for bold formatted single siglum with optional addition, like A, B, or G
        siglum_pattern = re.compile(r"^<p>\s*<strong>\s*([A-Z])\s*</strong>\s*</p>$")

        # pattern for bold formatted single siglum with square brackets, like [A], [B], or [G]
        siglum_missing_pattern = re.compile(r"^<p>\s*<strong>\s*\[([A-Z])\]\s*</strong>\s*</p>$")

        # pattern for bold formatted siglum with superscript addition, like Ac, AH, or AF1–2
        siglum_with_addendum_pattern = re.compile(
            r"^<p>\s*<strong>\s*([A-Z])<sup>([a-zA-Z][0-9]?(–[0-9])?)?</sup>\s*</strong>\s*</p>$"
        )

        # pattern for bold formatted siglum with superscript addition and square
        # brackets, like [Ac], [AH], or [AF1–2]
        siglum_with_addendum_missing_pattern = re.compile(
            r"^<p>\s*<strong>\s*\[([A-Z])<sup>([a-zA-Z][0-9]?(–[0-9])?)?</sup>\]</strong>\s*</p>$"
        )

        siglum_indices = []

        for index, para in enumerate(paras):
            # if para contains the pattern for a siglum
            if (
                siglum_pattern.match(str(para))
                or siglum_missing_pattern.match(str(para))
                or siglum_with_addendum_pattern.match(str(para))
                or siglum_with_addendum_missing_pattern.match(str(para))
            ):
                siglum_indices.append(index)

        return siglum_indices

    ############################################
    # Public method: process_table
    ############################################
    def process_table(
            self,
            textcritics_list: TextcriticsList,
            table: Tag,
            table_index: int) -> TextcriticsList:
        """
        Processes a table and extracts textcritical comments from it.

        Args:
            table (Tag): A BeautifulSoup `Tag` object representing a table.
            table_index (int): The index of the table in the list of tables.
        """
        textcritics = copy.deepcopy(defaultTextcritics)
        textcritics['commentary']['comments'] = []

        rows_in_table = table.find_all('tr')
        block_index = -1

        # Create a default comment block with an empty blockHeader
        default_comment_block = copy.deepcopy(defaultTextcriticalCommentBlock)
        default_comment_block['blockHeader'] = ""
        textcritics['commentary']['comments'].append(default_comment_block)
        block_index += 1

        textcritics = self._process_table_rows(textcritics, rows_in_table, block_index)

        print(
            f"Appending textcritics for table {table_index + 1}...")

        # Determine if the table is for corrections based on the presence of "Korrektur"
        is_corrections = "Korrektur" in rows_in_table[0].find_all('td')[-1].get_text(strip=True)

        # Adjust textcritics output based on the presence of corrections
        if is_corrections:
            textcritics_list = self._process_corrections(textcritics_list, textcritics)
        else:
            textcritics_list['textcritics'].append(textcritics)

        return textcritics_list

    ############################################
    # Helpfer funtction: _add_report_fragment_links
    ############################################
    def _add_report_fragment_links(self, text: str) -> str:
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
            text
        )

        return text

    ############################################
    # Helpfer funtction: _escape_curly_brackets
    ############################################
    def _escape_curly_brackets(self, text: str) -> str:
        """
        Escapes curly brackets in a given text.

        Args:
            text (str): The given text.

        Returns:
            str: The escaped text.
        """
        # Replace curly brackets with placeholders to avoid duplicated escaping
        text = text.replace('{', '__LEFT_CURLY_BRACKET__') \
                   .replace('}', '__RIGHT_CURLY_BRACKET__')
        # Escape curly brackets
        text = text.replace('__LEFT_CURLY_BRACKET__', "{{ '{' }}") \
                   .replace('__RIGHT_CURLY_BRACKET__', "{{ '}' }}")
        return text

    ############################################
    # Helper function: _get_comment
    ############################################

    def _get_comment(self, columns_in_row: List[Tag]) -> TextcriticalComment:
        """
        Extracts a textcritical comment object from a list of BeautifulSoup `Tag` objects.

        Args:
            columns_in_row (List[Tag]): A list of BeautifulSoup `Tag` objects
                representing columns in a row.

        Returns:
            TextcriticalComment: A dictionary representing the textcritical comment.
        """
        comment = copy.deepcopy(defaultTextcriticalComment)

        comment['measure'] = self._strip_tag_and_clean(columns_in_row[0], 'td')
        comment['system'] = self._strip_tag_and_clean(columns_in_row[1], 'td')
        comment['position'] = self._strip_tag_and_clean(columns_in_row[2], 'td')

        comment_text = self._strip_tag_and_clean(columns_in_row[3], 'td')
        comment_text = self._escape_curly_brackets(comment_text)
        comment_text = self._add_report_fragment_links(comment_text)
        comment_text = self._replace_glyphs(comment_text)
        comment['comment'] = comment_text

        return comment

    ############################################
    # Helper function: _get_siglum
    ############################################

    def _get_siglum(self, paras: List[Tag]) -> Tuple[str, str]:
        """
        Extracts the siglum from a list of BeautifulSoup `Tag` objects representing paragraphs.

        Args:
            paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing paragraphs.

        Returns:
            Tuple[str, str]: A tuple containing the siglum and the siglum addendum.
        """
        siglum_sup_tag = paras[0].find(SUP_TAG) or ""
        siglum_addendum = siglum_sup_tag.get_text(strip=True) if siglum_sup_tag else ""
        if siglum_sup_tag:
            siglum_sup_tag.extract()
        siglum = paras[0].get_text(strip=True)
        return siglum, siglum_addendum

    ############################################
    # Helper function: _get_description
    ############################################

    def _get_description(self, paras: List[Tag], source_id: str) -> Description:
        """
        Extracts the description of a source description from a list of BeautifulSoup `Tag` objects.

        Args:
            paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing paragraphs.
            source_id (str): The ID of the source description.

        Returns:
            Description: A dictionary representing the description of the source description.
        """
        description = copy.deepcopy(defaultDescription)
        desc = self._strip_tag(paras[3], P_TAG) or ""
        description["desc"].append(desc)

        # Define labels and corresponding keys in the description dictionary
        description_labels_keys = [
            ("Beschreibstoff:", "writingMaterialStrings"),
            ("Schreibstoff:", "writingInstruments"),
            ("Titel:", "titles"),
            ("Datierung:", "dates"),
            ("Paginierung:", "paginations"),
            ("Taktzahlen:", "measureNumbers"),
            ("Besetzung:", "instrumentations"),
            ("Eintragungen:", "annotations"),
        ]

        # Get content for each label and assign it to the corresponding key
        for label, key in description_labels_keys:
            content = self._get_paragraph_content_by_label(label, paras)

            # Writing instruments require special handling
            if key == "writingInstruments":
                content = self._extract_writing_instruments(
                    content[0]) if content else description[key]

            description[key] = content

        # Get content items
        description["contents"] = self._get_content_items(paras, source_id)

        return description

    ############################################
    # Helper function: _get_content_items
    ############################################

    def _get_content_items(self, paras: List[Tag], source_id: str) -> List[str]:
        """
        Extracts the content items from a list of BeautifulSoup `Tag` objects
        representing paragraphs.

        Args:
            paras (List[Tag]): A list of BeautifulSoup `Tag` objects
            representing paragraphs.
            source_id (str): The ID of the source description.

        Returns:
            List[str]: A list of content items extracted from the paragraphs.
        """
        # Get indices of content
        content_index = self._get_paragraph_index_by_label("Inhalt:", paras)
        if content_index == -1:
            print("No content found for", source_id)
            return []

        # Get indices of comments by checking for possible labels
        # If no comments labels are found, set the index to the last paragraph
        comments_labels = ["Textkritischer Kommentar:", "Textkritische Anmerkungen:"]
        comments_index = next(
            (self._get_paragraph_index_by_label(
                label, paras) for label in comments_labels if self._get_paragraph_index_by_label(
                label, paras) != -1), len(paras) - 1)

        return self._get_items(paras[(content_index + 1): comments_index])

    ############################################
    # Helper function: _extract_writing_instruments
    ############################################

    def _extract_writing_instruments(self, writing_instruments_text: str) -> WritingInstruments:
        """
        Extracts the main and secondary writing instruments from the given text.

        Args:
            writingInstrumentsText (str): The text to extract writing instruments from.

        Returns:
            A dictionary of type WritingInstruments that represents the set of writing instruments
                extracted from the text string.
                If no writing instruments are found in the input text,
                the default value of an empty main writing instrument and
                an empty list of secondary writing instruments is returned.
        """
        # Default value for empty writing instruments
        writing_instruments = {"main": "", "secondary": []}
        if writing_instruments_text is not None:
            stripped_writing_instruments = self._strip_by_delimiter(
                writing_instruments_text, SEMICOLON)

            # Strip . from last main and secondary writing instruments
            main = stripped_writing_instruments[0].strip().rstrip(DOT)
            if len(stripped_writing_instruments) > 1:
                secondary = [
                    instr.strip().rstrip(DOT)
                    for instr in self._strip_by_delimiter(stripped_writing_instruments[1], COMMA)
                ]
            else:
                secondary = []
            writing_instruments = {"main": main, "secondary": secondary}
        return writing_instruments

    ############################################
    # Helper function: _find_siblings
    ############################################

    def _find_siblings(self, sibling_para: Tag, paras: List[Tag]) -> List[Tag]:
        """
        Recursively finds all sibling paragraphs in a given list of paragraphs
        and finishes the recursion if the paragraph contains a <strong> tag or ends with a period.

        Args:
            sibling_para (BeautifulSoup.Tag): The first sibling paragraph to start the search from.
            paras (List[Tag]): A list of paragraphs to append to.

        Returns:
            List[BeautifulSoup.Tag]: A list of all sibling paragraphs.
        """
        # Check if the current paragraph contains a <strong> tag
        if sibling_para.find(STRONG_TAG):
            return paras
        # Check if the current paragraph ends with a period
        if sibling_para.text.endswith(DOT):
            paras.append(sibling_para)
            return paras
        # If the current paragraph does not meet the criteria, recursively search the next sibling
        paras.append(sibling_para)
        return self._find_siblings(sibling_para.next_sibling, paras)

    ############################################
    # Helper function: _find_tag_with_label_in_soup
    ############################################

    def _find_tag_with_label_in_soup(self, label: str, paras: List[Tag]) -> Optional[Tag]:
        """
        Searches for a specific label in a list of BeautifulSoup tags.

        Args:
        label (str): The label to search for.
        paras (List[Tag]): The list of BeautifulSoup tags to search within.

        Returns:
        The BeautifulSoup.Tag with the specified label, or None if not found.
        """
        if not label:
            return None
        for para in paras:
            if para.find(string=re.compile(label)):
                return para
        return None

    ############################################
    # Helper function: _get_folio_label
    ############################################

    def _get_folio_label(self, stripped_para_text: str) -> str:
        """
        Extracts the folio label from a paragraph of text containing a folio number.

        Args:
            stripped_para_text (str): The text of the paragraph with whitespace removed.
            folio_str (str): The string indicating the folio or page marker, such as 'Bl.' or 'S.'.

        Returns:
            str: The extracted folio label (if found), otherwise an empty string.
        """

        def process_text(text, string):
            text = text.lstrip("\t")
            text = text.replace(string + "\xa0", "").strip()
            text = text.replace(string, "").strip()
            return text

        folio_label = ""

        if FOLIO_STR in stripped_para_text:
            folio_label = process_text(stripped_para_text, FOLIO_STR)

        if PAGE_STR in stripped_para_text:
            folio_label = process_text(stripped_para_text, PAGE_STR)

        return folio_label

    ############################################
    # Helper function: _get_folios
    ############################################

    def _get_folios(self, sibling_paras: List[Tag]) -> List[Folio]:
        """
        Parses a list of sibling paragraphs to extract folios and their system groups.

        Args:
            sibling_paras (List[Tag]): A list of BeautifulSoup Tags representing sibling paragraphs.

        Returns:
            List[Folio]: A list of dictionaries representing folios and their system groups.
        """
        folios = []

        for para in sibling_paras:
            stripped_para_text = self._strip_by_delimiter(para.text, " \t")
            if len(stripped_para_text) != 2:
                stripped_para_text = self._strip_by_delimiter(para.text, "\t")

            # Check sibling paragraph for folioStr or pageStr to create a new folio entry
            folio_found = re.search(FOLIO_STR, para.text) is not None
            page_found = re.search(r"S\.", para.text) is not None
            has_folio_str = folio_found or page_found

            if has_folio_str:
                # Create folio object
                folio = copy.deepcopy(defaultFolio)

                # Extract folio label
                if stripped_para_text:
                    if FOLIO_STR in stripped_para_text[0] or PAGE_STR in stripped_para_text[0]:
                        folio["folio"] = self._get_folio_label(stripped_para_text[0].strip())
                    elif len(stripped_para_text) > 2 and (
                        FOLIO_STR in stripped_para_text[1] or PAGE_STR in stripped_para_text[1]
                    ):
                        folio["folio"] = self._get_folio_label(stripped_para_text[1].strip())

                # Check if the paragraph contains a page marker
                if page_found:
                    items = list(folio.items())
                    items.insert(1, ("isPage", True))
                    folio = dict(items)

                # Check if the paragraph contains no systemStr, then add folioDescription
                if not para.find(string=re.compile(SYSTEM_STR)):
                    folio["folioDescription"] = stripped_para_text[1].strip()
                else:
                    folio["systemGroups"] = [self._get_system_group(stripped_para_text)]

                # Add folio to folios
                folios.append(folio)

            # If there is no folioStr, but a systemStr,
            # add a new systemGroup to the folio's systemGroups
            elif not has_folio_str and para.find(string=re.compile(SYSTEM_STR)):
                folio["systemGroups"].append(self._get_system_group(stripped_para_text))

        return folios

    ############################################
    # Helper function: _get_item
    ############################################

    def _get_item(self, para: Tag) -> ContentItem:
        """
        Extracts a source description item from a given paragraph tag.

        Args:
            para (BeautifulSoup.Tag): The paragraph tag to extract the item information from.

        Returns:
            ContentItem: A dictionary containing the extracted content item information.
        """
        # Initialize variables
        item_label = ""
        item_link_to = {}
        item_description = ""

        # Get content of para with inner tags
        para_content = self._strip_tag(para, P_TAG)

        # Check if the paragraph starts with a strong formatted sketch sigle
        if para_content.find(STRONG_TAG) and (
            para.text.startswith(M_SIGLE) or para.text.startswith(M_STAR_SIGLE)
        ):
            # Extract itemLabel
            # (Get first part of the text content of para, split by "(" )
            item_label = self._strip_by_delimiter(para.text, PARENTHESIS)[0].strip()

            # Create itemLinkTo dictionary
            sheet_id = item_label.replace(
                " ",
                UNDERSCORE).replace(
                DOT,
                UNDERSCORE).replace(
                STAR,
                STAR_STR)
            complex_id = "".join(sheet_id.split(UNDERSCORE)[0:2]).lower()

            item_link_to = {"complexId": complex_id, "sheetId": sheet_id}

            # When there is a slash in the item label,
            # it means that we probably have multiple sketch items for a row table.
            # In that case, link to 'SkRT'
            if item_label.find(SLASH) != -1:
                item_link_to["sheetId"] = ROWTABLE_SHEET_ID

            # Extract itemDescription
            # (re-add delimiter that gets removed in the stripping action
            # and remove trailing colon)
            item_description = PARENTHESIS + \
                self._strip_by_delimiter(para_content, PARENTHESIS)[1].strip().rstrip(COLON)
        elif para_content.find(STRONG_TAG):
            print("--- Potential error? Strong tag found in para:", para_content)
        else:
            item_description = para_content.strip().rstrip(COLON)

        # Create item object
        item = copy.deepcopy(defaultContentItem)
        item["item"] = item_label
        item["itemLinkTo"] = item_link_to
        item["itemDescription"] = item_description

        return item

    ############################################
    # Helper function: _get_items
    ############################################

    def _get_items(self, paras: List[Tag]) -> List[ContentItem]:
        """
        Given a list of BeautifulSoup Tag objects representing paragraphs,
        extracts the items and their associated folios from the paragraphs
        and returns a list of content item dictionaries.

        Parameters:
        - paras (List[Tag]): A list of BeautifulSoup Tag objects representing paragraphs.

        Returns:
        - List[ContentItem]: A list of dictionaries, where each dictionary represents a content item
                            and its associated folios.
        """
        items = []

        for para in paras:

            if (
                not para.text.startswith("\t")
                and not para.text.startswith(PAGE_STR)
                and not para.text.startswith(FOLIO_STR)
            ):
                # Find item
                item = self._get_item(para)

                # Find all paragraphs that belong to an item
                sibling_paras = []
                sibling_paras = self._find_siblings(para.next_sibling, sibling_paras)

                # Find folios of all paragraphs of an item
                folios = self._get_folios(sibling_paras)

                item["folios"] = folios
                items.append(item)

        return items

    ############################################
    # Helper function: _get_paragraph_content_by_label
    ############################################

    def _get_paragraph_content_by_label(self, label: str, paras: List[Tag]) -> str:
        """
        Returns the content of the paragraph containing the specified label
        within the BeautifulSoup object. If the label is not found, an empty string is returned.

        Args:
            label (str): The label to search for within the BeautifulSoup object.
            paras (List[Tag]): The list of BeautifulSoup tags to search within.

        Returns:
            str: The content of the BeautifulSoup `p` tag containing the label,
                with leading and trailing whitespace removed.
        """
        content_paragraph = self._find_tag_with_label_in_soup(label, paras)
        content_lines = []

        if content_paragraph is None:
            return content_lines

        stripped_content = self._strip_tag(content_paragraph, P_TAG)
        initial_content = self._strip_by_delimiter(stripped_content, label)[1]

        content_lines.append(initial_content.strip().rstrip(DOT).rstrip(SEMICOLON))

        if initial_content.endswith(SEMICOLON):
            # Check for sibling paragraphs that belong to the same content
            # (separated by semicolons)
            sibling = content_paragraph.next_sibling

            while sibling is not None and sibling.name == P_TAG:
                sibling_content = self._strip_tag(sibling, P_TAG)
                if sibling_content.endswith(DOT) or sibling_content.endswith(SEMICOLON):
                    content_lines.append(sibling_content.strip().rstrip(DOT).rstrip(SEMICOLON))
                    if sibling_content.endswith(DOT):
                        break
                else:
                    break

                sibling = sibling.next_sibling

        return content_lines

    ############################################
    # Helper function: _get_paragraph_index_by_label
    ############################################

    def _get_paragraph_index_by_label(self, label: str, paras: List[Tag]) -> int:
        """
        Gets the index of the first BeautifulSoup `p` element containing the specified label.

        Args:
            label (str): The label to search for.
            paras (List[Tag]): The list of BeautifulSoup tags to search within.

        Returns:
            Index of p tag with given label in BeautifulSoup, or -1 if absent.
        """
        tag_with_label = self._find_tag_with_label_in_soup(label, paras)
        try:
            return paras.index(tag_with_label)
        except ValueError:
            return -1

    ############################################
    # Helper function: _get_system_group
    ############################################

    def _get_system_group(self, stripped_para_text: List[str]) -> List[System]:
        """
        Extracts a system group from a list of stripped paragraph texts.

        Args:
            stripped_para_text (List[str]): The stripped paragraph text containing system groups.

        Returns:
            List[System]: A list of system objects.
        """
        if not stripped_para_text:
            return []

        system_group = []

        for _, para in enumerate(stripped_para_text):
            # Skip folio label
            if FOLIO_STR in para:
                continue

            if PAGE_STR in para:
                continue

            # Create system object
            system = copy.deepcopy(defaultSystem)

            # Extract system label
            if SYSTEM_STR in para:
                stripped_system_text = self._strip_by_delimiter(para, COLON)
                system_label = stripped_system_text[0].replace(SYSTEM_STR, "").strip()

                system["system"] = system_label

                # Extract measure label
                if len(stripped_system_text) == 1:
                    continue

                if MEASURE_STR in stripped_system_text[1]:
                    # Remove leading measure string and trailing dot or semicolon.
                    measure_label = (
                        stripped_system_text[1].lstrip(MEASURE_STR).rstrip(".;").strip()
                    )
                    system["measure"] = measure_label
                else:
                    # Extract row label
                    # pattern matches, e.g., "Gg (1)", "KUgis (38)",
                    # or "Gg (I)", "KUgis (XXXVIII)",
                    # but also "Gg", "KUgis"
                    pattern = r"([A-Z]{1,2})([a-z]{1,3})(\s[(](\d{1,2}|[I,V,X,L]{1,7})[)])?"

                    if re.search(pattern, stripped_system_text[1]):
                        row_text = re.findall(pattern, stripped_system_text[1])[0]

                        row = copy.deepcopy(defaultRow)
                        row["rowType"] = row_text[0]
                        row["rowBase"] = row_text[1]
                        if len(row_text) > 3:
                            row["rowNumber"] = row_text[3]

                        system["row"] = row

                system_group.append(system)

        return system_group

    ############################################
    # Helper function: _process_corrections
    ############################################

    def _process_corrections(self, textcritics_list: TextcriticsList,
                             textcritics: TextCritics) -> TextcriticsList:
        """
        Processes textcritics as corrections and appends to the corrections list.

        Args:
            textcritics (dict): The textcritics object to process.
            textcritics_list (dict): The dictionary containing textcritics and corrections lists.
        """
        textcritics_list['corrections'].append(textcritics)
        textcritics.pop("linkBoxes", None)  # Remove linkBoxes property if it exists

        # Remove svgGroupId property from textcritical comments
        for comment_block in textcritics['commentary']['comments']:
            for comment in comment_block['blockComments']:
                comment.pop("svgGroupId", None)  # Remove svgGroupId property if it exists

        return textcritics_list

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
        for row in rows_in_table[1:]:
            columns_in_row = row.find_all('td')

            # Check if the first td has a colspan attribute
            if 'colspan' in columns_in_row[0].attrs:
                # If the default comment block is empty, remove it
                if not textcritics['commentary']['comments'][0]['blockComments']:
                    textcritics['commentary']['comments'].pop(0)
                    block_index -= 1

                comment_block = copy.deepcopy(defaultTextcriticalCommentBlock)
                comment_block['blockHeader'] = self._strip_tag_and_clean(
                    columns_in_row[0], 'td')
                textcritics['commentary']['comments'].append(comment_block)
                block_index += 1

                continue

            if block_index >= 0:
                comment = self._get_comment(columns_in_row)
                textcritics['commentary']['comments'][block_index]['blockComments'].append(comment)

        return textcritics

    ############################################
    # Helper function: _replace_glyphs
    ############################################
    def _replace_glyphs(self, text: str) -> str:
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
            "Sechzehntelnote",
            "Viertelnote"
        ]
        glyph_pattern = '|'.join(re.escape(glyph) for glyph in glyphs)

        # Match pattern for glyphs in square brackets, but not followed by a hyphen
        match_pattern = rf'\[({glyph_pattern})\](?!-)'

        return re.sub(
            match_pattern,
            lambda match: f"<span class='glyph'>{{{{ref.getGlyph('{match.group(0)}')}}}}</span>",
            text
        )

    ############################################
    # Helper function: _strip_by_delimiter
    ############################################

    def _strip_by_delimiter(self, input_str: str, delimiter: str) -> List[str]:
        """
        Splits a string by a delimiter and returns a list of stripped substrings.

        Args:
            input_str (str): The input string to split and strip.
            delimiter (str): The delimiter to split the string by.

        Returns:
            List[str]: A list of stripped substrings.
        """
        stripped_substring_list: List[str] = [s.strip() for s in input_str.split(delimiter)]
        return stripped_substring_list

    ############################################
    # Helper function: _strip_tag_and_clean
    ############################################

    def _strip_tag_and_clean(self, content, tag) -> str:
        """
        Strips opening and closing tags from an HTML string and strips surrounding paragraph tags.

        Args:
        content (str): The input string.
        tag (str): The name of the tag to strip.

        Returns:
        str: The content within the specified tags, with leading and trailing whitespace removed.
        """
        stripped_content = self._strip_tag(self._strip_tag(content, tag), P_TAG)
        return stripped_content.replace('</p><p>', ' <br /> ')

    ############################################
    # Helper function: _strip_tag
    ############################################

    def _strip_tag(self, tag: Tag, tag_str: str) -> str:
        """
        Strips opening and closing tags from an HTML/XML string and returns the
        content within the tags as a string.

        Args:
        tag (Tag): The input BeautifulSoup tag.
        tagStr (str): The name of the tag to strip.

        Returns:
        str: The content within the specified tags, with leading and trailing whitespace removed.
        """
        stripped_str = str(tag) if tag is not None else ""

        # Strip opening and closing tags from input (incl. attributes in opening tag)
        opening_tag_start_index = stripped_str.find('<' + tag_str)
        opening_tag_end_index = stripped_str.find('>', opening_tag_start_index) + 1
        closing_tag = "</" + tag_str + ">"

        stripped_str = stripped_str[opening_tag_end_index:]
        stripped_str = stripped_str.removesuffix(closing_tag)

        # Strip trailing white space
        stripped_str = stripped_str.strip()

        return stripped_str
