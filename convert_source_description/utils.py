"""Utility functions for the conversion of source descriptions from Word to JSON.

This module should not be run directly. Instead, run the `convert_source_description.py` module.
"""

import copy
import json
import os
import re
from typing import Dict, List, NotRequired, Optional, Tuple, TypedDict

import mammoth
from bs4 import BeautifulSoup, Tag


############################################
# Helper variables: Typed Classes
############################################
class Row(TypedDict):
    """A typed dictionary that represents a row of a system."""
    rowType: str
    rowBase: str
    rowNumber: str


class System(TypedDict):
    """A typed dictionary that represents a system."""
    system: str
    measure: str
    linkTo: str
    row: NotRequired[Row]


class Folio(TypedDict):
    """A typed dictionary that represents a folio."""
    folio: str
    folioLinkTo: str
    folioDescription: str
    systemGroups: List[List[System]]


class ContentItem(TypedDict):
    """A typed dictionary that represents a content item."""
    item: str
    itemLinkTo: str
    itemDescription: str
    folios: List[Folio]


class WritingInstruments(TypedDict):
    """A typed dictionary that represents a set of writing instruments."""
    main: str
    secondary: List[str]


class Description(TypedDict):
    """A typed dictionary that represents a description of a source description."""
    desc: List[str]
    writingMaterialString: str
    writingInstruments: WritingInstruments
    title: str
    date: str
    pagination: str
    measureNumbers: str
    instrumentation: str
    annotations: str
    content: List[ContentItem]


class SourceDescription(TypedDict):
    """A typed dictionary that represents a source description."""
    id: str
    siglum: str
    siglumAddendum: str
    type: str
    location: str
    description: Description


class SourceList(TypedDict):
    """A typed dictionary that represents a list of source descriptions."""
    sources: List[SourceDescription]


class LinkBox(TypedDict):
    """A typed dictionary that represents a link box."""
    svgGroupId: str
    linkTo: str


class TextcriticalComment(TypedDict):
    """A typed dictionary that represents a textcritical comment."""
    svgGroupId: str
    measure: str
    system: str
    position: str
    comment: str


class TextCritics(TypedDict):
    """A typed dictionary that represents a textcritics object."""
    id: str
    label: str
    description: List
    rowTable: bool
    comments: List[TextcriticalComment]
    linkBoxes: List[LinkBox]


class TextcriticsList(TypedDict):
    """A typed dictionary that represents a list of textcritics objects."""
    textcritics: List[TextCritics]

############################################
# Helper variables: Strings & Objects
############################################


SYSTEM_STR = 'System'
MEASURE_STR = 'T.'
FOLIO_STR = 'Bl.'
PAGE_STR = 'S.'

########
emptySourceList: SourceList = {
    "sources": []
}

emptySourceDescription: SourceDescription = {
    "id": "",
    "siglum": "",
    "siglumAddendum": "",
    "type": "",
    "location": "",
    "description": {}
}

emptyDescription: Description = {
    "desc": [],
    "writingMaterialString": "",
    "writingInstruments": {
        "main": "",
        "secondary": []
    },
    "title": "",
    "date": "",
    "pagination": "",
    "measureNumbers": "",
    "instrumentation": "",
    "annotations": "",
    "content": []
}

emptyContentItem: ContentItem = {
    "item": "",
    "itemLinkTo": "",
    "itemDescription": "",
    "folios": []
}

emptyFolio: Folio = {
    "folio": "",
    "folioLinkTo": "",
    "folioDescription": "",
    "systemGroups": []
}

emptySystem: System = {
    "system": "",
    "measure": "",
    "linkTo": ""
}

emptyRow: Row = {
    "rowType": "",
    "rowBase": "",
    "rowNumber": ""
}

emptyTextcriticsList: TextcriticsList = {
    "textcritics": []
}

emptyTextcritics: TextCritics = {
    "id": "",
    "label": "",
    "description": [],
    # "rowTable": False,
    "comments": [],
    "linkBoxes": []
}

emptyTextcriticalComment: TextcriticalComment = {
    "svgGroupId": "TODO",
    "measure": "",
    "system": "",
    "position": "",
    "comment": ""
}

emptyLinkBox: LinkBox = {
    "svgGroupId": "",
    "linkTo": ""
}

############################################
# Public class: ConversionUtils
############################################


class ConversionUtils:
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
        source_list = copy.deepcopy(emptySourceList)
        sources = source_list['sources']

        # Find all p tags in soup
        paras = soup.find_all('p')

        # Find all siglum indices
        siglum_indices = _find_siglum_indices(paras)

        # Iterate over siglum ranges and create source descriptions
        for i, current_siglum_index in enumerate(siglum_indices):
            next_siglum_index = next(
                (siglum_indices[i + 1] for i in range(i, len(siglum_indices) - 1)), len(paras))

            if current_siglum_index < next_siglum_index:
                filtered_paras = paras[current_siglum_index:next_siglum_index]

                source_description = _create_source_description(filtered_paras)
                source_id = source_description['id']

                try:
                    next(
                        source for source in sources if source['id'] == source_id)
                    print(
                        f"Duplication: Source description for {source_id} included."
                        f"Please check the source file.")
                except StopIteration:
                    print(
                        f"Appending source description for {source_id}...")
                    sources.append(source_description)

        return source_list

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
        textcritics_list = copy.deepcopy(emptyTextcriticsList)

        # Find all table tags in soup
        tables = soup.find_all('table')

        # Iterate over tables and create textcritics
        for table_index, table in enumerate(tables):
            textcritics = copy.deepcopy(emptyTextcritics)

            table_rows = table.find_all('tr')
            for row in table_rows[1:]:
                comment = copy.deepcopy(emptyTextcriticalComment)
                table_cols = row.find_all('td')
                comment['measure'] = _strip_tag(
                    _strip_tag(table_cols[0], 'td'), 'p')
                comment['system'] = _strip_tag(
                    _strip_tag(table_cols[1], 'td'), 'p')
                comment['position'] = _strip_tag(
                    _strip_tag(table_cols[2], 'td'), 'p')
                comment['comment'] = _strip_tag(
                    _strip_tag(table_cols[3], 'td'), 'p')

                textcritics['comments'].append(comment)

            print(
                f"Appending textcritics for table {table_index + 1}...")
            textcritics_list['textcritics'].append(textcritics)

        return textcritics_list

    ############################################
    # Public class function: pprint
    ############################################

    def pprint(self, output: Dict) -> None:
        """
        Pretty prints a dictionary as JSON object to the console with indentation of 2.

        Args:
            output (Dict): The dictionary to be pretty printed.

        Returns:
            None
        """
        print(json.dumps(output, indent=2))

    ############################################
    # Public class function: read_html_from_word_file
    ############################################

    def read_html_from_word_file(self, file_path: str) -> str:
        """
        Reads a Word file in .docx format and returns its content as an HTML string.

        Args:
            filePath (str): The name of the Word file to be read, without the .docx extension.

        Returns:
            str: The content of the Word file as an HTML string.
        """
        source_file_name = file_path + ".docx"
        if not os.path.exists(source_file_name):
            raise FileNotFoundError("File not found: " + file_path + ".docx")

        with open(source_file_name, "rb") as source_file:
            try:
                result = mammoth.convert_to_html(source_file)
                return result.value  # The generated HTML
            except ValueError as error:
                raise ValueError('Error converting file: ' +
                                 str(error)) from error

    ############################################
    # Public class function: write_json
    ############################################
    def write_json(self, data: Dict, file_path: str) -> None:
        """
        Serializes a data dictionary as a JSON formatted string and writes it to a file.

        Args:
            data (Dict): The data dictionary to be serialized and written.
            file_path (str): The path to the file to be written, without the .json extension.

        Returns:
            None
        """
        # Serializing json
        json_object = json.dumps(data, indent=4, ensure_ascii=False).encode(
            'utf8').decode('utf8')

        # Writing to target file
        target_file_name = file_path + ".json"
        try:
            with open(target_file_name, "w", encoding='utf-8') as target_file:
                target_file.write(json_object)
            print(f"Data written to {target_file_name} successfully.")
        except IOError:
            print(f"Error writing data to {target_file_name}.")


#############################################
# Helper function: _create_source_description
#############################################
def _create_source_description(paras: List[Tag]) -> SourceDescription:
    """Create a source description dictionary from a list of BeautifulSoup `Tag` objects.

    Args:
        paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing paragraphs.

    Returns:
        SourceDescription: A dictionary representing the source description.
    """
    source_description = copy.deepcopy(emptySourceDescription)

    # Get siglum
    siglum, siglum_addendum = _get_siglum(paras)

    # Check if siglum is enclosed in square brackets and remove them; set missing flag on the way
    if siglum.startswith('[') and siglum.endswith(']'):
        siglum = siglum[1:-1]
        items = list(source_description.items())
        items.insert(3, ('missing', True))
        source_description = dict(items)

    siglum_string = siglum + siglum_addendum
    source_id = 'source_' + siglum_string if siglum_string else ''

    # Update source description
    source_description['id'] = source_id
    source_description['siglum'] = siglum
    source_description['siglumAddendum'] = siglum_addendum
    source_description['type'] = _strip_tag(paras[1], 'p') or ''
    source_description['location'] = _strip_tag(paras[2], 'p') or ''
    source_description['description'] = _get_description(paras, source_id)

    return source_description


############################################
# Helper function: _get_siglum
############################################
def _get_siglum(paras: List[Tag]) -> Tuple[str, str]:
    """
    Extracts the siglum from a list of BeautifulSoup `Tag` objects representing paragraphs.

    Args:
        paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing paragraphs.

    Returns:
        Tuple[str, str]: A tuple containing the siglum and the siglum addendum.
    """
    siglum_sup_tag = paras[0].find('sup') or ''
    siglum_addendum = siglum_sup_tag.get_text(
        strip=True) if siglum_sup_tag else ''
    if siglum_sup_tag:
        siglum_sup_tag.extract()
    siglum = paras[0].get_text(strip=True)
    return siglum, siglum_addendum


############################################
# Helper function: _get_description
############################################
def _get_description(paras: List[Tag], source_id: str) -> Description:
    """
    Extracts the description of a source description from a list of BeautifulSoup `Tag` objects.

    Args:
        paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing paragraphs.
        source_id (str): The ID of the source description.

    Returns:
        Description: A dictionary representing the description of the source description.
    """
    description = copy.deepcopy(emptyDescription)
    desc = _strip_tag(paras[3], 'p') or ''
    description['desc'].append(desc)

    # Define labels and corresponding keys in the description dictionary
    description_labels_keys = [
        ('Beschreibstoff:', 'writingMaterialString'),
        ('Schreibstoff:', 'writingInstruments'),
        ('Titel:', 'title'),
        ('Datierung:', 'date'),
        ('Paginierung:', 'pagination'),
        ('Taktzahlen:', 'measureNumbers'),
        ('Besetzung:', 'instrumentation'),
        ('Eintragungen:', 'annotations')
    ]

    # Get content for each label and assign it to the corresponding key
    for label, key in description_labels_keys:
        content = _get_paragraph_content_by_label(label, paras)
        if key == 'writingInstruments':
            content = _extract_writing_instruments(content)
        description[key] = content

    # Get content items
    description['content'] = _get_content_items(paras, source_id)

    return description


############################################
# Helper function: _get_content_items
############################################
def _get_content_items(paras: List[Tag], source_id: str) -> List[str]:
    """
    Extracts the content items from a list of BeautifulSoup `Tag` objects representing paragraphs.

    Args:
        paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing paragraphs.
        source_id (str): The ID of the source description.

    Returns:
        List[str]: A list of content items extracted from the paragraphs.
    """
    # Get indices of content and comments
    content_index = _get_paragraph_index_by_label('Inhalt:', paras)
    comments_index = _get_paragraph_index_by_label(
        'Textkritischer Kommentar:', paras)
    if comments_index == -1:
        comments_index = len(paras) - 1

    if content_index == -1:
        print('No content found for', source_id)
        return []

    return _get_items(paras[(content_index + 1):comments_index])

############################################
# Helper function: _extract_writing_instruments
############################################


def _extract_writing_instruments(writing_instruments_text: str) -> WritingInstruments:
    """
    Extracts the main and secondary writing instruments from the given text.

    Args:
        writingInstrumentsText (str): The text to extract writing instruments from.

    Returns:
        A dictionary of type WritingInstruments that represents the set of writing instruments
            extracted from the text string. If no writing instruments are found in the input text, 
            the default value of an empty main writing instrument and
            an empty list of secondary writing instruments is returned.
    """
    # Default value for empty writing instruments
    writing_instruments = {'main': '', 'secondary': []}
    if writing_instruments_text is not None:
        stripped_writing_instruments = _strip_by_delimiter(
            writing_instruments_text, ';')

        # Strip . from last main and secondary writing instruments
        main = stripped_writing_instruments[0].strip().rstrip('.')
        if len(stripped_writing_instruments) > 1:
            secondary = [instr.strip().rstrip('.')
                         for instr in _strip_by_delimiter(stripped_writing_instruments[1], ',')]
        else:
            secondary = []
        writing_instruments = {'main': main, 'secondary': secondary}
    return writing_instruments


############################################
# Helper function: _find_siblings
############################################
def _find_siblings(sibling_para: Tag, paras: List[Tag]) -> List[Tag]:
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
    if sibling_para.find('strong'):
        return paras
    # Check if the current paragraph ends with a period
    if sibling_para.text.endswith('.'):
        paras.append(sibling_para)
        return paras
    # If the current paragraph does not meet the criteria, recursively search the next sibling
    paras.append(sibling_para)
    return _find_siblings(sibling_para.next_sibling, paras)


############################################
# Helper function: _find_siglum_indices
############################################
def _find_siglum_indices(paras: List[Tag]) -> List[int]:
    """
    Finds the indices of paragraphs in a list of BeautifulSoup `Tag` objects 
        that contain a single bold siglum.

    Args:
        paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing paragraphs.

    Returns:
        A list of integers representing the indices of the paragraphs
            that contain a single bold siglum.
    """
    # pattern for bold formatted single siglum with optional addition, like A or Ac
    siglum_pattern = re.compile(
        r'^<p><strong>([A-Z])</strong></p>$')

    siglum_missing_pattern = re.compile(
        r'^<p><strong>\[([A-Z])\]</strong></p>$')

    siglum_with_addendum_pattern = re.compile(
        r'^<p><strong>([A-Z])<sup>([a-zA-Z][0-9]?(–[0-9])?)?</sup></strong></p>$')

    siglum_with_addendum_missing_pattern = re.compile(
        r'^<p><strong>\[([A-Z])<sup>([a-zA-Z][0-9]?(–[0-9])?)?</sup>\]</strong></p>$')

    siglum_indices = []

    for index, para in enumerate(paras):
        # if para contains the pattern for a siglum
        if (siglum_pattern.match(str(para)) or
            siglum_missing_pattern.match(str(para)) or
            siglum_with_addendum_pattern.match(str(para)) or
                siglum_with_addendum_missing_pattern.match(str(para))):
            siglum_indices.append(index)

    return siglum_indices


############################################
# Helper function: _find_tag_with_label_in_soup
############################################
def _find_tag_with_label_in_soup(label: str, paras: List[Tag]) -> Optional[Tag]:
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
def _get_folio_label(stripped_para_text: str) -> str:
    """
    Extracts the folio label from a paragraph of text containing a folio number.

    Args:
        stripped_para_text (str): The text of the paragraph with whitespace removed.
        folio_str (str): The string indicating the folio or page marker, such as 'Bl.' or 'S.'.

    Returns:
        str: The extracted folio label if found in the paragraph text, otherwise an empty string.
    """
    def process_text(text, string):
        text = text.lstrip('\t')
        text = text.replace(string + '\xa0', '').strip()
        text = text.replace(string, '').strip()
        return text

    folio_label = ''

    if FOLIO_STR in stripped_para_text:
        folio_label = process_text(stripped_para_text, FOLIO_STR)

    if PAGE_STR in stripped_para_text:
        folio_label = process_text(stripped_para_text, PAGE_STR)

    return folio_label


############################################
# Helper function: _get_folios
############################################
def _get_folios(sibling_paras: List[Tag]) -> List[Folio]:
    """
    Parses a list of sibling paragraphs to extract folios and their system groups.

    Args:
        sibling_paras (List[Tag]): A list of BeautifulSoup Tags representing sibling paragraphs.

    Returns:
        List[Folio]: A list of dictionaries representing folios and their system groups.
    """
    folios = []

    for para in sibling_paras:
        stripped_para_text = _strip_by_delimiter(para.text, ' \t')
        if len(stripped_para_text) == 1:
            stripped_para_text = _strip_by_delimiter(para.text, '\t')

        # Check sibling paragraph for folioStr or pageStr to create a new folio entry
        folio_found = re.search(FOLIO_STR, para.text) is not None
        page_found = re.search(r'S\.', para.text) is not None
        has_folio_str = folio_found or page_found

        if has_folio_str:
            # Create folio object
            folio = copy.deepcopy(emptyFolio)

            # Extract folio label
            folio['folio'] = _get_folio_label(stripped_para_text[0].strip())

            # Check if the paragraph contains a page marker
            if page_found:
                items = list(folio.items())
                items.insert(1, ('isPage', True))
                folio = dict(items)

            # Check if the paragraph contains no systemStr, then add folioDescription
            if not para.find(string=re.compile(SYSTEM_STR)):
                folio['folioDescription'] = stripped_para_text[1].strip()
            else:
                folio['systemGroups'] = [_get_system_group(stripped_para_text)]

            # Add folio to folios
            folios.append(folio)

        # If there is no folioStr, but a systemStr,
        # add a new systemGroup to the folio's systemGroups
        elif not has_folio_str and para.find(string=re.compile(SYSTEM_STR)):
            folio['systemGroups'].append(_get_system_group(stripped_para_text))

    return folios


############################################
# Helper function: _get_item
############################################
def _get_item(para: Tag) -> ContentItem:
    """
    Extracts a source description item from a given paragraph tag.

    Args:
        para (BeautifulSoup.Tag): The paragraph tag to extract the item information from.

    Returns:
        ContentItem: A dictionary containing the extracted content item information.
    """
    # Initialize variables
    item_label = ''
    item_link_to = ''
    item_description = ''
    delimiter = '('

    # Get content of para with inner tags
    para_content = _strip_tag(para, 'p')
    stripped_para_content = _strip_by_delimiter(para_content, delimiter)

    # Get text content of para without inner tags
    stripped_para_text = _strip_by_delimiter(para.text, delimiter)

    if len(stripped_para_content) > 1:
        if (para_content.find('strong') and
            (stripped_para_text[0].startswith('M ') or
             stripped_para_text[0].startswith('M* '))):
            # Extract itemLabel
            item_label = stripped_para_text[0].strip()

            # When there is a slash in the item label,
            # it means that we probably have multiple sketch items for a row table.
            # In that case, link to 'SkRT'
            if item_label.find('/') != -1:
                item_link_to = 'SkRT'
            # In all other cases, link to the id created from the itemLabel
            else:
                item_link_to = item_label.replace(' ', '_').replace('.', '_').replace('*', 'star')

        # Extract itemDescription
        # (re-add delimiter that was removed in the stripping action above
        # and remove trailing colon)
        item_description = delimiter + \
            stripped_para_content[1].strip().rstrip(':')

    elif len(stripped_para_content) == 1:
        item_description = stripped_para_content[0].strip().rstrip(':')

    # Create item object
    item = copy.deepcopy(emptyContentItem)
    item['item'] = item_label
    item['itemLinkTo'] = item_link_to
    item['itemDescription'] = item_description

    return item

############################################
# Helper function: _getItems
############################################


def _get_items(paras: List[Tag]) -> List[ContentItem]:
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

        if (not para.text.startswith('\t') and
            not para.text.startswith(PAGE_STR) and
                not para.text.startswith(FOLIO_STR)):
            # Find item
            item = _get_item(para)

            # Find all paragraphs that belong to an item
            sibling_paras = []
            sibling_paras = _find_siblings(para.next_sibling, sibling_paras)

            # Find folios of all paragraphs of an item
            folios = _get_folios(sibling_paras)

            item['folios'] = folios
            items.append(item)

    return items


############################################
# Helper function: _get_paragraph_content_by_label
############################################
def _get_paragraph_content_by_label(label: str, paras: List[Tag]) -> str:
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
    content_paragraph = _find_tag_with_label_in_soup(label, paras)

    if content_paragraph is None:
        return ''

    stripped_content = _strip_tag(content_paragraph, 'p')
    content = _strip_by_delimiter(stripped_content, label)[1]

    if content.endswith(';'):
        # Check for sibling paragraphs that belong to the same content
        # (separated by semicolons)
        sibling = content_paragraph.next_sibling

        while sibling is not None and sibling.name == 'p':
            sibling_content = _strip_tag(sibling, 'p')
            if sibling_content.endswith('.'):
                content += '<br />' + sibling_content
                break
            if sibling_content.endswith(';'):
                content += '<br />' + sibling_content
            else:
                break

            sibling = sibling.next_sibling

    return content.strip()


############################################
# Helper function: _get_paragraph_index_by_label
############################################
def _get_paragraph_index_by_label(label: str, paras: List[Tag]) -> int:
    """
    Gets the index of the first BeautifulSoup `p` element containing the specified label.

    Args:
        label (str): The label to search for.
        paras (List[Tag]): The list of BeautifulSoup tags to search within.

    Returns:
        The index of the BeautifulSoup `p` tag containing the specified label, or -1 if not found.
    """
    tag_with_label = _find_tag_with_label_in_soup(label, paras)
    try:
        return paras.index(tag_with_label)
    except ValueError:
        return -1


############################################
# Helper function: _get_system_group
############################################
def _get_system_group(stripped_para_text: List[str]) -> List[System]:
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
        system = copy.deepcopy(emptySystem)

        # Extract system label
        if SYSTEM_STR in para:
            stripped_system_text = _strip_by_delimiter(para, ':')
            system_label = stripped_system_text[0].replace(
                SYSTEM_STR, '').strip()

            system['system'] = system_label

            # Extract measure label
            if len(stripped_system_text) == 1:
                continue

            if MEASURE_STR in stripped_system_text[1]:
                # Remove leading measure string and trailing colon or dot.
                measure_label = stripped_system_text[1].lstrip(
                    MEASURE_STR).rstrip('.;').strip()
                system['measure'] = measure_label
            else:
                # Extract row label
                # pattern matches, e.g., "Gg (1)", "KUgis (38)",
                # or "Gg (I)", "KUgis (XXXVIII)",
                # but also "Gg", "KUgis"
                pattern = r"([A-Z]{1,2})([a-z]{1,3})(\s[(](\d{1,2}|[I,V,X,L]{1,7})[)])?"

                if re.search(pattern, stripped_system_text[1]):
                    row_text = re.findall(pattern, stripped_system_text[1])[0]

                    row = copy.deepcopy(emptyRow)
                    row['rowType'] = row_text[0]
                    row['rowBase'] = row_text[1]
                    if len(row_text) > 3:
                        row['rowNumber'] = row_text[3]

                    system['row'] = row

            system_group.append(system)

    return system_group


############################################
# Helper function: _strip_by_delimiter
############################################
def _strip_by_delimiter(input_str: str, delimiter: str) -> List[str]:
    """
    Splits a string by a delimiter and returns a list of stripped substrings.

    Args:
        input_str (str): The input string to split and strip.
        delimiter (str): The delimiter to split the string by.

    Returns:
        List[str]: A list of stripped substrings.
    """
    stripped_substring_list: List[str] = [
        s.strip() for s in input_str.split(delimiter)]
    return stripped_substring_list


############################################
# Helper function: _strip_tag
############################################
def _strip_tag(tag: Tag, tag_str: str) -> str:
    """
    Strips opening and closing tags from an HTML/XML string and returns the
    content within the tags as a string.

    Args:
      tag (Tag): The input BeautifulSoup tag.
      tagStr (str): The name of the tag to strip.

    Returns:
      str: The content within the specified tags, with leading and trailing whitespace removed.
    """
    stripped_str = str(tag) if tag is not None else ''

    # Strip opening and closing tags from input
    opening_tag = '<' + tag_str + '>'
    closing_tag = '</' + tag_str + '>'
    stripped_str = stripped_str.removeprefix(opening_tag)
    stripped_str = stripped_str.removesuffix(closing_tag)

    # Strip trailing white space
    stripped_str = stripped_str.strip()

    return stripped_str
