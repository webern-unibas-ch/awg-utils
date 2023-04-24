"""Utility functions for the conversion of source descriptions from Word to JSON.

This module should not be run directly. Instead, run the `convert_source_description.py` module.
"""

import copy
import json
import os
import re
from typing import Dict, List, NotRequired, Optional, TypedDict

import mammoth
from bs4 import Tag


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
    writingMaterial: str
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


############################################
# Helper variables: Strings & Objects
############################################

SYSTEM_STR = 'System'
MEASURE_STR = 'T.'
FOLIO_STR = 'Bl.'

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
    "writingMaterial": "",
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

############################################
# Public class: ConversionUtils
############################################


class ConversionUtils:
    """A class that contains utility functions for the conversion of source descriptions 
        from Word to JSON."""

    ############################################
    # Public class function: create_source_list
    ############################################
    def create_source_list(self, paras: List[Tag]) -> SourceList:
        """
        Creates a list of source descriptions based on the given paragraph tags.

        Args:
            paras (List[Tag]): A list of BeautifulSoup `Tag` objects 
                                representing the paragraphs in the document.

        Returns:
            A SourceList object containing a list of SourceDescription objects.
        """
        source_list = copy.deepcopy(emptySourceList)
        sources = source_list['sources']

        # Find all siglum indices
        siglum_indices = _find_siglum_indices(paras)

        # Iterate over siglum ranges and create source descriptions
        for i, current_siglum_index in enumerate(siglum_indices):
            try:
                next_siglum_index = siglum_indices[i + 1]
            except IndexError:
                next_siglum_index = len(paras) - 1

            filtered_paras = paras[current_siglum_index:next_siglum_index]
            source_description = _create_source_description(filtered_paras)
            siglum = source_description['siglum']

            try:
                source = next(
                    source for source in sources if source['siglum'] == siglum)
                print(
                    f"Source description for {siglum} already included. "
                    f"Overwriting with latest changes...")
                source.update(source_description)
            except StopIteration:
                print(
                    f"Appending source description for {siglum}...")
                sources.append(source_description)

        return source_list

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


############################################
# Helper function: _create_source_description
############################################
def _create_source_description(paras: List[Tag]) -> SourceDescription:
    """Create a source description dictionary from a list of BeautifulSoup `Tag` objects.

    Args:
        paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing paragraphs.

    Returns:
        SourceDescription: A dictionary representing the source description.
    """
    # Get siglum, id, type, and location
    siglum = paras[0].text.strip() or ''
    source_id = 'source' + siglum if siglum else ''
    source_type = paras[1].text.strip() or ''
    location = paras[2].text.strip() or ''

    source_description = copy.deepcopy(emptySourceDescription)
    source_description['id'] = source_id
    source_description['siglum'] = siglum
    source_description['type'] = source_type
    source_description['location'] = location

    # Get description
    description = copy.deepcopy(emptyDescription)
    desc = paras[3].text.strip() or ''
    description['desc'].append(desc)

    # Get writing material and instruments
    writing_material = _get_paragraph_content_by_label(
        'Beschreibstoff:', paras)
    writing_instruments_content = _get_paragraph_content_by_label(
        'Schreibstoff:', paras)
    writing_instruments = _extract_writing_instruments(
        writing_instruments_content)

    description['writingMaterial'] = writing_material
    description['writingInstruments'] = writing_instruments

    # Get title, date, measureNumbers, instrumentation, and annotations
    description['title'] = _get_paragraph_content_by_label('Titel:', paras)
    description['date'] = _get_paragraph_content_by_label('Datierung:', paras)
    description['pagination'] = _get_paragraph_content_by_label(
        'Paginierung:', paras)
    description['measureNumbers'] = _get_paragraph_content_by_label(
        'Taktzahlen:', paras)
    description['instrumentation'] = _get_paragraph_content_by_label(
        'Besetzung:', paras)
    description['annotations'] = _get_paragraph_content_by_label(
        'Eintragungen:', paras)

    # Get content items
    content_index = _get_paragraph_index_by_label('Inhalt:', paras)
    comments_index = _get_paragraph_index_by_label(
        'Textkritischer Kommentar:', paras) or len(paras) - 1

    description['content'] = _get_items(
        paras[(content_index + 1):comments_index])

    source_description['description'] = description

    return source_description


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
    elif sibling_para.text.endswith('.'):
        paras.append(sibling_para)
        return paras
    # If the current paragraph does not meet the criteria, recursively search the next sibling
    else:
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
        r'^<p><strong>([A-Z])([a-z])?</strong></p>$')

    siglum_indices = []

    for index, para in enumerate(paras):
        # if para contains the pattern for a siglum
        if siglum_pattern.match(str(para)):
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
def _get_folio_label(stripped_para_text: str, folio_str: str) -> str:
    """
    Extracts the folio label from a paragraph of text containing a folio number.

    Args:
        stripped_para_text (str): The text of the paragraph with whitespace removed.
        folio_str (str): The string indicating the folio number, such as 'Bl.'.

    Returns:
        str: The extracted folio label if found in the paragraph text, otherwise an empty string.
    """
    folio_label = ''

    if folio_str in stripped_para_text:
        folio_label = stripped_para_text.lstrip('\t')
        folio_label = folio_label.replace(folio_str + '\xa0', '').strip()
        folio_label = folio_label.replace(folio_str, '').strip()

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

        # Check sibling paragraph for folioStr to create a new folio entry
        has_folio_str = para.find(string=re.compile(FOLIO_STR))
        if has_folio_str:
            # Create folio object
            folio = copy.deepcopy(emptyFolio)

            folio['folio'] = _get_folio_label(
                stripped_para_text[0].strip(), FOLIO_STR)
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
    delimiter = '('

    # Get content of para with inner tags
    para_content = _strip_tag(para, 'p')
    stripped_para_content = _strip_by_delimiter(para_content, delimiter)

    # Get text content of para without inner tags
    stripped_para_text = _strip_by_delimiter(para.text, delimiter)

    # Extract itemLabel
    item_label = stripped_para_text[0].strip()

    # When there is a slash in the item label,
    # it means that we probably have multiple sketch items for a row table.
    # In that case, link to 'SkRT'
    if item_label.find('/') != -1:
        item_link_to = 'SkRT'
    # In all other cases, link to the id created from the itemLabel
    else:
        item_link_to = item_label.replace(' ', '_').replace('.', '_')

    # Extract itemDescription
    # (re-add delimiter that was removed in the stripping action above; and remove trailing colon)
    if len(stripped_para_content) == 1:
        print('Something went wrong. Maybe there is some bold formatting in line:', para)
    item_description = delimiter + stripped_para_content[1].strip().rstrip(':')

    # Create item object
    item = copy.deepcopy(emptyContentItem)
    item['item'] = item_label or ''
    item['itemLinkTo'] = item_link_to or ''
    item['itemDescription'] = item_description or ''

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
        if para.find('strong'):
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
            elif sibling_content.endswith(';'):
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

        else:
            print('No', SYSTEM_STR, 'found in', para)

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
