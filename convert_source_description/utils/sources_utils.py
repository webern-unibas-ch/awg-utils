"""
Utility functions for the conversion of source descriptions from Word to JSON.

This module should not be run directly. Instead, run the `convert_source_description.py` module.
"""

import copy
import re
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup, Tag

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
    SYSTEM_STR,
    UNDERSCORE,
)
from utils.default_objects import (
    DEFAULT_CONTENT_ITEM,
    DEFAULT_FOLIO,
    DEFAULT_PHYS_DESC,
    DEFAULT_ROW,
    DEFAULT_SOURCE_DESCRIPTION,
    DEFAULT_SOURCE_LIST,
    DEFAULT_SYSTEM,
)
from utils.index_utils import IndexUtils
from utils.paragraph_utils import ParagraphUtils
from utils.stripping_utils import StrippingUtils
from utils.typed_classes import (
    ContentItem,
    Folio,
    PhysDesc,
    Row,
    SourceDescription,
    SourceList,
    System,
    WritingInstruments,
)


############################################
# Public class: SourcesUtils
############################################
class SourcesUtils:  # pylint: disable=too-few-public-methods
    """A class that contains utility functions for the conversion of source descriptions
    from Word to JSON."""

    ############################################
    # Public class function: create_source_list
    ############################################
    def create_source_list(self, soup: BeautifulSoup) -> SourceList:
        """
        Creates a list of source descriptions based on the given soup elements.

        Args:
            soup (BeautifulSoup): A BeautifulSoup object representing the document.

        Returns:
            A SourceList object containing a list of SourceDescription objects.
        """
        source_list = copy.deepcopy(DEFAULT_SOURCE_LIST)
        sources = source_list["sources"]

        # Find all p tags in soup
        paras = soup.find_all("p")

        # Find all siglum indices
        siglum_indices = IndexUtils.find_siglum_indices(paras)

        # Iterate over siglum ranges and create source descriptions
        for i, current_siglum_index in enumerate(siglum_indices):
            next_siglum_index = (
                siglum_indices[i + 1] if i + 1 < len(siglum_indices) else len(paras)
            )
            filtered_paras = paras[current_siglum_index:next_siglum_index]

            source_description = self._process_source_description(filtered_paras)
            source_id = source_description["id"]

            if any(source["id"] == source_id for source in sources):
                print(
                    f"Duplication: Source description for {source_id} included. "
                    f"Please check the source file."
                )
            else:
                print(f"Appending source description for {source_id}...")
                sources.append(source_description)

        return source_list

    #############################################
    # Private method: _process_source_description
    #############################################
    def _process_source_description(self, paras: List[Tag]) -> SourceDescription:
        """Processes a source description dictionary from a list of BeautifulSoup `Tag` objects.

        Args:
            paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing paragraphs.

        Returns:
            SourceDescription: A dictionary representing the source description.
        """
        source_description = copy.deepcopy(DEFAULT_SOURCE_DESCRIPTION)

        # Process siglum and determine if the source is missing
        siglum, siglum_addendum, is_missing = self._process_siglum(paras)

        # Create source ID
        source_id = f"source_{siglum}{siglum_addendum}" if siglum else ""

        # Insert the missing flag into the source description, if source is missing
        if is_missing:
            items = list(source_description.items())
            items.insert(3, ("missing", True))
            source_description = dict(items)

        # Update source description
        source_description["id"] = source_id
        source_description["siglum"] = siglum
        source_description["siglumAddendum"] = siglum_addendum
        source_description["type"] = StrippingUtils.strip_tag(paras[1], P_TAG) or ""
        source_description["location"] = StrippingUtils.strip_tag(paras[2], P_TAG) or ""
        source_description["physDesc"] = self._process_phys_desc(paras, source_id)

        return source_description

    ############################################
    # Helper function: _process_siglum
    ############################################

    def _process_siglum(self, paras: List[Tag]) -> Tuple[str, str, bool]:
        """
        Processes the siglum from a list of BeautifulSoup `Tag` objects representing paragraphs.

        Args:
            paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing paragraphs.

        Returns:
            Tuple[str, str, bool]: A tuple containing the siglum (without brackets),
                the siglum addendum, and a flag indicating whether the siglum is missing.
        """
        m = IndexUtils.SIGLUM_PATTERN.match(str(paras[0]))
        if not m:
            return paras[0].get_text(strip=True), "", False
        is_missing = m.group(1).startswith("[")
        siglum = m.group(1).lstrip("[")
        addendum = m.group(3) or ""
        return siglum, addendum, is_missing

    ############################################
    # Helper function: _process_phys_desc
    ############################################

    def _process_phys_desc(self, paras: List[Tag], source_id: str) -> PhysDesc:
        """
        Processes the physDesc of a source description from a list of BeautifulSoup `Tag` objects.

        Args:
            paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing paragraphs.
            source_id (str): The ID of the source description.

        Returns:
            PhysDesc: A dictionary representing the physical description of the source description.
        """
        phys_desc = copy.deepcopy(DEFAULT_PHYS_DESC)
        phys_desc["conditions"].append(StrippingUtils.strip_tag(paras[3], P_TAG) or "")

        # Define labels and corresponding keys in the physical description dictionary
        phys_desc_labels_keys = [
            ("Beschreibstoff:", "writingMaterialStrings"),
            ("Titel:", "titles"),
            ("Datierung:", "dates"),
            ("Paginierung:", "paginations"),
            ("Taktzahlen:", "measureNumbers"),
            ("Besetzung:", "instrumentations"),
            ("Eintragungen:", "annotations"),
        ]

        # Get content for each label and assign it to the corresponding key
        for label, key in phys_desc_labels_keys:
            phys_desc[key] = ParagraphUtils.get_paragraph_content_by_label(label, paras)

        # Writing instruments require special handling
        wi_content = ParagraphUtils.get_paragraph_content_by_label(
            "Schreibstoff:", paras
        )
        if wi_content:
            phys_desc["writingInstruments"] = self._process_writing_instruments(
                wi_content[0]
            )

        # Process content items
        phys_desc["contents"] = self._process_contents(paras, source_id)

        return phys_desc

    ############################################
    # Helper function: _process_writing_instruments
    ############################################

    def _process_writing_instruments(
        self, writing_instruments_text: str
    ) -> WritingInstruments:
        """
        Processes the main and secondary writing instruments from the given text.

        Args:
            writingInstrumentsText (str): The text to process writing instruments from.

        Returns:
            A dictionary of type WritingInstruments that represents the set of writing instruments
                processed from the text string.
                If no writing instruments are found in the input text,
                the default value of an empty main writing instrument and
                an empty list of secondary writing instruments is returned.
        """
        if writing_instruments_text is None:
            return {"main": "", "secondary": []}

        main, *secondaries = StrippingUtils.strip_by_delimiter(
            writing_instruments_text, SEMICOLON
        )
        secondary = (
            [
                instr.strip().rstrip(FULL_STOP)
                for instr in StrippingUtils.strip_by_delimiter(secondaries[0], COMMA)
            ]
            if secondaries
            else []
        )
        return {"main": main.strip().rstrip(FULL_STOP), "secondary": secondary}

    ############################################
    # Helper function: _process_contents
    ############################################

    def _process_contents(self, paras: List[Tag], source_id: str) -> List[ContentItem]:
        """
        Processes the contents from a list of BeautifulSoup `Tag` objects
        representing paragraphs.

        Args:
            paras (List[Tag]): A list of BeautifulSoup `Tag` objects
            representing paragraphs.
            source_id (str): The ID of the source description.

        Returns:
            List[ContentItem]: A list of content items extracted from the paragraphs.
        """
        contents_start_index, contents_end_index = IndexUtils.find_contents_indices(
            paras
        )
        if contents_start_index == -1:
            print("No content found for", source_id)
            return []

        return self._process_items(
            paras[(contents_start_index + 1) : contents_end_index]
        )

    ############################################
    # Helper function: _process_items
    ############################################

    def _process_items(self, paras: List[Tag]) -> List[ContentItem]:
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
                item = self._process_item(para)

                # Find all paragraphs that belong to an item
                sibling_paras = []
                sibling_paras = self._find_siblings(para.next_sibling, sibling_paras)

                # Find folios of all paragraphs of an item
                folios = self._process_folios(sibling_paras)

                item["folios"] = folios
                items.append(item)

        return items

    ############################################
    # Helper function: _process_item
    ############################################

    def _process_item(self, para: Tag) -> ContentItem:
        """
        Extracts a source description item from a given paragraph tag.

        Args:
            para (BeautifulSoup.Tag): The paragraph tag to extract the item information from.

        Returns:
            ContentItem: A dictionary containing the extracted content item information.
        """
        para_content = StrippingUtils.strip_tag(para, P_TAG)
        item = copy.deepcopy(DEFAULT_CONTENT_ITEM)

        if STRONG_TAG in para_content and (
            para.text.startswith(M_SIGLE) or para.text.startswith(MX_SIGLE)
        ):
            item_label = StrippingUtils.strip_by_delimiter(para.text, PARENTHESIS)[
                0
            ].strip()

            item["item"] = item_label
            item["itemLinkTo"] = self._process_item_link_to(item_label)
            item["itemDescription"] = PARENTHESIS + StrippingUtils.strip_by_delimiter(
                para_content, PARENTHESIS
            )[1].strip().rstrip(COLON)
        elif STRONG_TAG in para_content:
            print("--- Potential error? Strong tag found in para:", para_content)
        else:
            item["itemDescription"] = para_content.strip().rstrip(COLON)

        return item

    ############################################
    # Helper function: _process_item_link_to
    ############################################

    def _process_item_link_to(self, item_label: str) -> dict:
        """
        Builds the itemLinkTo dictionary from a sketch item label.

        Args:
            item_label (str): The item label string, e.g. 'M 34 Sk1' or 'M* 414 Sk1'.

        Returns:
            dict: A dictionary with 'complexId' and 'sheetId' keys.
        """
        sheet_id = (
            item_label.replace(" ", UNDERSCORE)
            .replace(UNDERSCORE, "", 1)  # Remove first underscore (Mx_414 -> Mx414)
            .replace(FULL_STOP, UNDERSCORE)
            .replace(STAR, STAR_STR)
        )
        complex_id = sheet_id.split(UNDERSCORE)[0].lower()
        return {
            "complexId": complex_id,
            "sheetId": ROWTABLE_SHEET_ID if SLASH in item_label else sheet_id,
        }

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
        # Skip NavigableStrings (whitespace/newlines) and advance to the next real sibling
        while sibling_para is not None and not isinstance(sibling_para, Tag):
            sibling_para = sibling_para.next_sibling

        # Stop if no real <p> sibling exists or it contains a <strong> tag
        if (
            sibling_para is None
            or sibling_para.name != P_TAG
            or sibling_para.find(STRONG_TAG)
        ):
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
    # Helper function: _process_folios
    ############################################

    def _process_folios(self, sibling_paras: List[Tag]) -> List[Folio]:
        """
        Parses a list of sibling paragraphs to extract folios and their system groups.

        Args:
            sibling_paras (List[Tag]): A list of BeautifulSoup Tags representing sibling paragraphs.

        Returns:
            List[Folio]: A list of dictionaries representing folios and their system groups.
        """
        folios = []
        folio: Optional[Folio] = None

        for para in sibling_paras:
            stripped_para_text = StrippingUtils.strip_by_delimiter(para.text, " \t")
            if len(stripped_para_text) != 2:
                stripped_para_text = StrippingUtils.strip_by_delimiter(para.text, "\t")
            if len(stripped_para_text) < 2:
                print(
                    f"--- Potential error? Paragraph has fewer than 2 parts, skipped: "
                    f"{para.text.strip()!r}"
                )
                continue

            folio_found = FOLIO_STR in para.text
            page_found = PAGE_STR in para.text
            system_found = SYSTEM_STR in para.text

            if folio_found or page_found:
                folio = self._process_folio(para, stripped_para_text, page_found)
                folios.append(folio)
            elif system_found and folio is not None:
                folio["systemGroups"].append(  # pylint: disable=unsubscriptable-object
                    self._process_system_group(stripped_para_text)
                )
            else:
                print(
                    f"--- Potential error? Unexpected paragraph in folios: "
                    f"{para.text.strip()!r}"
                )

        return folios

    ############################################
    # Helper function: _process_folio
    ############################################

    def _process_folio(
        self, para: Tag, stripped_para_text: List[str], page_found: bool
    ) -> Folio:
        """
        Processes a folio dictionary from a paragraph tag and its stripped text parts.

        Args:
            para (Tag): The paragraph tag to extract folio information from.
            stripped_para_text (List[str]): The paragraph text split by delimiter.
            page_found (bool): Whether the paragraph contains a page marker.

        Returns:
            Folio: A dictionary representing the folio.
        """
        folio = copy.deepcopy(DEFAULT_FOLIO)

        # Extract folio label
        if stripped_para_text:
            folio_part = next(
                (p for p in stripped_para_text if FOLIO_STR in p or PAGE_STR in p),
                None,
            )
            if folio_part:
                folio["folio"] = self._process_folio_label(folio_part.strip())

        # Insert isPage flag at position 1 if this is a page paragraph
        if page_found:
            items = list(folio.items())
            items.insert(1, ("isPage", True))
            folio = dict(items)

        # Set folioDescription or systemGroups
        if SYSTEM_STR not in para.text:
            folio["folioDescription"] = stripped_para_text[1].strip()
        else:
            folio["systemGroups"] = [self._process_system_group(stripped_para_text)]

        return folio

    ############################################
    # Helper function: _process_folio_label
    ############################################

    def _process_folio_label(self, stripped_para_text: str) -> str:
        """
        Processes the folio label from a paragraph of text containing a folio number.

        Args:
            stripped_para_text (str): The text of the paragraph with whitespace removed.
            folio_str (str): The string indicating the folio or page marker, such as 'Bl.' or 'S.'.

        Returns:
            str: The processed folio label (if found), otherwise an empty string.
        """
        if FOLIO_STR in stripped_para_text:
            return StrippingUtils.strip_label_from_text(stripped_para_text, FOLIO_STR)
        if PAGE_STR in stripped_para_text:
            return StrippingUtils.strip_label_from_text(stripped_para_text, PAGE_STR)

        return ""

    ############################################
    # Helper function: _process_system_group
    ############################################

    def _process_system_group(self, stripped_para_text: List[str]) -> List[System]:
        """
        Processes a system group in a list of stripped paragraph texts.

        Args:
            stripped_para_text (List[str]): The stripped paragraph text containing system groups.

        Returns:
            List[System]: A list of system objects.
        """
        if not stripped_para_text:
            return []

        system_group = []

        for para_text in stripped_para_text:
            # Skip folio or page label
            if FOLIO_STR in para_text or PAGE_STR in para_text:
                continue

            # Process system object
            system = self._process_system(para_text)
            if system:
                system_group.append(system)

        return system_group

    ############################################
    # Helper function: _process_system
    ############################################
    def _process_system(self, para_text: str) -> Optional[System]:
        """Processes a system in a given paragraph text.

        Args:
            para_text (str): The paragraph text containing the system information.

        Returns:
            Optional[System]: A dictionary representing the system information,
            or None if the paragraph does not contain valid system information.
        """
        if SYSTEM_STR not in para_text:
            return None

        system = copy.deepcopy(DEFAULT_SYSTEM)

        system_label, *system_content = StrippingUtils.strip_by_delimiter(
            para_text, COLON
        )
        system["system"] = system_label.replace(SYSTEM_STR, "").strip()

        if not system_content:
            return system

        if len(system_content) > 1:
            print(
                f"--- Potential error? Unexpected colon in system content: {para_text!r}"
            )

        content = system_content[0]
        if MEASURE_STR in content:
            system["measure"] = self._process_measure(content)
        else:
            row = self._process_row(content)
            if row:
                system["row"] = row

        return system

    ############################################
    # Helper function: _process_measure
    ############################################
    def _process_measure(self, text: str) -> str:
        """Processes a measure label from a given text string.

        Args:
            text (str): The text to extract the measure label from.

        Returns:
            str: The extracted measure label.
        """
        return text.lstrip(MEASURE_STR).rstrip(".;").strip()

    ############################################
    # Helper function: _process_row
    ############################################
    def _process_row(self, text: str) -> Optional[Row]:
        """Processes a row label from a given text string.

        Args:
            text (str): The text to extract the row label from.

        Returns:
            Optional[Row]: A dictionary representing the row label,
            or None if the text does not match the expected pattern.
        """
        # Pattern matches, e.g., "Gg (1)", "KUgis (38)" (integers),
        # or "Gg (I)", "KUgis (XXXVIII)" (roman numerals),
        # but also "Gg", "KUgis" (without row number in parentheses)
        pattern = r"([A-Z]{1,2})([a-z]{1,3})(\s[(](\d{1,2}|[I,V,X,L]{1,7})[)])?"

        if not re.search(pattern, text):
            return None

        row_text = re.findall(pattern, text)[0]
        row = copy.deepcopy(DEFAULT_ROW)
        row["rowType"] = row_text[0]
        row["rowBase"] = row_text[1]
        if len(row_text) > 3:
            row["rowNumber"] = row_text[3]
        return row
