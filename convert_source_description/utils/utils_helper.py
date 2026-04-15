"""
Auxiliary functions supporting the conversion process from Word source descriptions to JSON format.

This module should not be run directly. Instead, run the `convert_source_description.py` module.
"""

import copy
import re
from typing import List, Tuple

from bs4 import Tag

from utils.constants import (
    COLON,
    COMMA,
    FOLIO_STR,
    FULL_STOP,
    M_SIGLE,
    MX_SIGLE,
    MEASURE_STR,
    PAGE_STR,
    PARENTHESIS,
    P_TAG,
    ROWTABLE_SHEET_ID,
    SEMICOLON,
    SLASH,
    STAR,
    STAR_STR,
    STRONG_TAG,
    SUP_TAG,
    SYSTEM_STR,
    UNDERSCORE,
)
from utils.default_objects import (
    DEFAULT_CONTENT_ITEM,
    DEFAULT_FOLIO,
    DEFAULT_PHYS_DESC,
    DEFAULT_ROW,
    DEFAULT_SOURCE_DESCRIPTION,
    DEFAULT_SYSTEM,
)
from utils.paragraph_utils import ParagraphUtils
from utils.stripping_utils import StrippingUtils
from utils.typed_classes import (
    ContentItem,
    Folio,
    PhysDesc,
    SourceDescription,
    System,
    WritingInstruments,
)


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
        source_description = copy.deepcopy(DEFAULT_SOURCE_DESCRIPTION)

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
        source_description["type"] = StrippingUtils.strip_tag(paras[1], P_TAG) or ""
        source_description["location"] = StrippingUtils.strip_tag(paras[2], P_TAG) or ""
        source_description["physDesc"] = self._get_phys_desc(paras, source_id)

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
        siglum_missing_pattern = re.compile(
            r"^<p>\s*<strong>\s*\[([A-Z])\]\s*</strong>\s*</p>$"
        )

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
    # Helper function: _get_phys_desc
    ############################################

    def _get_phys_desc(self, paras: List[Tag], source_id: str) -> PhysDesc:
        """
        Extracts the physDesc of a source description from a list of BeautifulSoup `Tag` objects.

        Args:
            paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing paragraphs.
            source_id (str): The ID of the source description.

        Returns:
            PhysDesc: A dictionary representing the physical description of the source description.
        """
        phys_desc = copy.deepcopy(DEFAULT_PHYS_DESC)
        conditions = StrippingUtils.strip_tag(paras[3], P_TAG) or ""
        phys_desc["conditions"].append(conditions)

        # Define labels and corresponding keys in the physical description dictionary
        phys_desc_labels_keys = [
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
        for label, key in phys_desc_labels_keys:
            content = ParagraphUtils.get_paragraph_content_by_label(label, paras)

            # Writing instruments require special handling
            if key == "writingInstruments":
                content = (
                    self._extract_writing_instruments(content[0])
                    if content
                    else phys_desc[key]
                )

            phys_desc[key] = content

        # Get content items
        phys_desc["contents"] = self._get_content_items(paras, source_id)

        return phys_desc

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
        content_index = ParagraphUtils.get_paragraph_index_by_label("Inhalt:", paras)
        if content_index == -1:
            print("No content found for", source_id)
            return []

        # Get indices of comments by checking for possible labels
        # If no comments labels are found, set the index to the last paragraph
        comments_labels = ["Textkritischer Kommentar:", "Textkritische Anmerkungen:"]
        comments_index = next(
            (
                ParagraphUtils.get_paragraph_index_by_label(label, paras)
                for label in comments_labels
                if ParagraphUtils.get_paragraph_index_by_label(label, paras) != -1
            ),
            len(paras),
        )

        # Ensure comments_index is within valid range
        if comments_index >= len(paras):
            comments_index = len(paras) - 1

        return self._get_items(paras[(content_index + 1) : comments_index])

    ############################################
    # Helper function: _extract_writing_instruments
    ############################################

    def _extract_writing_instruments(
        self, writing_instruments_text: str
    ) -> WritingInstruments:
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
            stripped_writing_instruments = StrippingUtils.strip_by_delimiter(
                writing_instruments_text, SEMICOLON
            )

            # Strip . from last main and secondary writing instruments
            main = stripped_writing_instruments[0].strip().rstrip(FULL_STOP)
            if len(stripped_writing_instruments) > 1:
                secondary = [
                    instr.strip().rstrip(FULL_STOP)
                    for instr in StrippingUtils.strip_by_delimiter(
                        stripped_writing_instruments[1], COMMA
                    )
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

        # Strip the text of the current paragraph
        stripped_sibling_para_text = sibling_para.text.strip()

        # Check if the current paragraph ends with a period
        if stripped_sibling_para_text.endswith(FULL_STOP):
            paras.append(sibling_para)
            return paras
        # If the current paragraph does not meet the criteria, recursively search the next sibling
        paras.append(sibling_para)
        return self._find_siblings(sibling_para.next_sibling, paras)

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
            stripped_para_text = StrippingUtils.strip_by_delimiter(para.text, " \t")
            if len(stripped_para_text) != 2:
                stripped_para_text = StrippingUtils.strip_by_delimiter(para.text, "\t")

            # Check sibling paragraph for folioStr or pageStr to create a new folio entry
            folio_found = re.search(FOLIO_STR, para.text) is not None
            page_found = re.search(r"S\.", para.text) is not None
            has_folio_str = folio_found or page_found

            if has_folio_str:
                # Create folio object
                folio = copy.deepcopy(DEFAULT_FOLIO)

                # Extract folio label
                if stripped_para_text:
                    if (
                        FOLIO_STR in stripped_para_text[0]
                        or PAGE_STR in stripped_para_text[0]
                    ):
                        folio["folio"] = self._get_folio_label(
                            stripped_para_text[0].strip()
                        )
                    elif len(stripped_para_text) > 2 and (
                        FOLIO_STR in stripped_para_text[1]
                        or PAGE_STR in stripped_para_text[1]
                    ):
                        folio["folio"] = self._get_folio_label(
                            stripped_para_text[1].strip()
                        )

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
        para_content = StrippingUtils.strip_tag(para, P_TAG)

        # Check if the paragraph starts with a strong formatted sketch sigle
        if para_content.find(STRONG_TAG) and (
            para.text.startswith(M_SIGLE) or para.text.startswith(MX_SIGLE)
        ):
            # Extract itemLabel
            # (Get first part of the text content of para, split by "(" )
            item_label = StrippingUtils.strip_by_delimiter(para.text, PARENTHESIS)[
                0
            ].strip()

            # Create itemLinkTo dictionary
            sheet_id = (
                item_label.replace(" ", UNDERSCORE)
                .replace(UNDERSCORE, "", 1)  # Remove first underscore (Mx_414 -> Mx414)
                .replace(FULL_STOP, UNDERSCORE)
                .replace(STAR, STAR_STR)
            )
            complex_id = sheet_id.split(UNDERSCORE)[0].lower()

            item_link_to = {"complexId": complex_id, "sheetId": sheet_id}

            # When there is a slash in the item label,
            # it means that we probably have multiple sketch items for a row table.
            # In that case, link to 'SkRT'
            if item_label.find(SLASH) != -1:
                item_link_to["sheetId"] = ROWTABLE_SHEET_ID

            # Extract itemDescription
            # (re-add delimiter that gets removed in the stripping action
            # and remove trailing colon)
            item_description = PARENTHESIS + StrippingUtils.strip_by_delimiter(
                para_content, PARENTHESIS
            )[1].strip().rstrip(COLON)
        elif para_content.find(STRONG_TAG):
            print("--- Potential error? Strong tag found in para:", para_content)
        else:
            item_description = para_content.strip().rstrip(COLON)

        # Create item object
        item = copy.deepcopy(DEFAULT_CONTENT_ITEM)
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
            system = copy.deepcopy(DEFAULT_SYSTEM)

            # Extract system label
            if SYSTEM_STR in para:
                stripped_system_text = StrippingUtils.strip_by_delimiter(para, COLON)
                system_label = stripped_system_text[0].replace(SYSTEM_STR, "").strip()

                system["system"] = system_label

                # Extract measure label
                if len(stripped_system_text) == 1:
                    continue

                if MEASURE_STR in stripped_system_text[1]:
                    # Remove leading measure string and trailing full stop or semicolon.
                    measure_label = (
                        stripped_system_text[1].lstrip(MEASURE_STR).rstrip(".;").strip()
                    )
                    system["measure"] = measure_label
                else:
                    # Extract row label
                    # pattern matches, e.g., "Gg (1)", "KUgis (38)",
                    # or "Gg (I)", "KUgis (XXXVIII)",
                    # but also "Gg", "KUgis"
                    pattern = (
                        r"([A-Z]{1,2})([a-z]{1,3})(\s[(](\d{1,2}|[I,V,X,L]{1,7})[)])?"
                    )

                    if re.search(pattern, stripped_system_text[1]):
                        row_text = re.findall(pattern, stripped_system_text[1])[0]

                        row = copy.deepcopy(DEFAULT_ROW)
                        row["rowType"] = row_text[0]
                        row["rowBase"] = row_text[1]
                        if len(row_text) > 3:
                            row["rowNumber"] = row_text[3]

                        system["row"] = row

                system_group.append(system)

        return system_group
