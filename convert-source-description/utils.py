import copy
import json
import os
import re
from typing import Any, Dict, List, NotRequired, Optional, TypedDict

import mammoth
from bs4 import Tag


############################################
# Helper variables: Typed Classes
############################################
class Row(TypedDict):
    rowType: str
    rowBase: str
    rowNumber: str

class System(TypedDict):
    system: str
    measure: str
    linkTo: str
    row: NotRequired[Row]

class Folio(TypedDict):
    folio: str
    folioLinkTo: str
    folioDescription: str
    systemGroups: List[List[System]]

class ContentItem(TypedDict):
    item: str
    itemLinkTo: str
    itemDescription: str
    folios: List[Folio]

class WritingInstruments(TypedDict):
  """
    A typed dictionary that represents a set of writing instruments.
  """
  main: str
  secondary: List[str]

class Description(TypedDict):
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
    id: str
    siglum: str
    siglumAddendum: str
    type: str
    location: str
    description: Description

class SourceList(TypedDict):
   sources: List[SourceDescription]


############################################
# Helper variables: Strings & Objects
############################################

systemStr = 'System'
measureStr = 'T.'
folioStr = 'Bl.'

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
    ############################################
    # Public class function: createSourceList
    ############################################
    def createSourceList(paras: List[Tag]) -> SourceList:
        """
        Creates a list of source descriptions based on the given paragraph tags.

        Args:
            paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing the paragraphs in the document.

        Returns:
            A SourceList object containing a list of SourceDescription objects.
        """
        sourceList = copy.deepcopy(emptySourceList)
        sources = sourceList['sources']

        # Find all siglum indices
        siglumIndices = _findSiglumIndices(paras)

        # Iterate over siglum ranges and create source descriptions
        for i, currentSiglumIndex in enumerate(siglumIndices):
          try:
              nextSiglumIndex = siglumIndices[i + 1]
          except IndexError:
              nextSiglumIndex = len(paras) - 1

          filteredParas = paras[currentSiglumIndex:nextSiglumIndex]
          sourceDescription = _createSourceDescription(filteredParas)

          try:
              source = next(source for source in sources if source['siglum'] == sourceDescription['siglum'])
              print(f"Source description for {sourceDescription['siglum']} already included. Overwriting with latest changes...")
              source.update(sourceDescription)
          except StopIteration:
              print(f"Appending source description for {sourceDescription['siglum']}...")
              sources.append(sourceDescription)
        
        return sourceList


    ############################################
    # Helper function: pprint
    ############################################
    def pprint(output: Dict) -> None:
        """
        Pretty prints a dictionary as JSON object to the console with indentation of 2.

        Args:
            output (Dict): The dictionary to be pretty printed.

        Returns:
            None
        """
        print(json.dumps(output, indent=2))


    ############################################
    # Public class function: readHtmlFromWordFile
    ############################################
    def readHtmlFromWordFile(filePath: str) -> str:
        """
        Reads a Word file in .docx format and returns its content as an HTML string.

        Args:
            filePath (str): The name of the Word file to be read, without the .docx extension.

        Returns:
            str: The content of the Word file as an HTML string.
        """
        sourceFileName = filePath + ".docx"
        if not os.path.exists(sourceFileName):
            raise FileNotFoundError("File not found: " + filePath + ".docx")

        with open(sourceFileName, "rb") as sourceFile:
            try:
                result = mammoth.convert_to_html(sourceFile)
                return result.value  # The generated HTML
            except Exception as e:
                raise Exception("Error converting file: " + str(e))


    ############################################
    # Public class function: writeJson
    ############################################
    def writeJson(data: Dict, filePath: str)-> None:
        """
        Serializes a data dictionary as a JSON formatted string and writes it to a file.

        Args:
            data (Dict): The data dictionary to be serialized and written.
            filePath (str): The path to the file to be written, without the .json extension.

        Returns:
            None
        """
        # Serializing json 
        jsonObject = json.dumps(data, indent=4, ensure_ascii=False).encode('utf8').decode('utf8')
          
        # Writing to target file
        targetFileName = filePath + ".json"
        try:
            with open(targetFileName, "w", encoding='utf-8') as targetFile:
                targetFile.write(jsonObject)
            print(f"Data written to {targetFileName} successfully.")
        except IOError:
            print(f"Error writing data to {targetFileName}.")



############################################
# Helper function: _createSourceDescription
############################################
def _createSourceDescription(paras: List[Tag]) -> SourceDescription:
    """Create a source description dictionary from a list of BeautifulSoup `Tag` objects.

    Args:
        paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing paragraphs.

    Returns:
        SourceDescription: A dictionary representing the source description.
    """        
    ############## Get siglum, id, type, and location
    siglum = paras[0].text.strip() or ''
    id = 'source' + siglum if siglum else ''
    sourceType = paras[1].text.strip() or ''
    location = paras[2].text.strip() or ''

    sourceDescription = copy.deepcopy(emptySourceDescription)
    sourceDescription['id'] = id
    sourceDescription['siglum'] = siglum
    sourceDescription['type'] = sourceType
    sourceDescription['location'] = location

    ############## Get description
    description = copy.deepcopy(emptyDescription)
    desc = paras[3].text.strip() or ''
    description['desc'].append(desc)

    # Get writing material and instruments
    writingMaterial = _getParagraphContentByLabel('Beschreibstoff:', paras)
    writingInstrumentsText = _getParagraphContentByLabel('Schreibstoff:', paras)
    writingInstruments = _extractWritingInstruments(writingInstrumentsText)

    description['writingMaterial'] = writingMaterial
    description['writingInstruments'] = writingInstruments

    # Get title, date, measureNumbers, instrumentation, and annotations
    description['title'] = _getParagraphContentByLabel('Titel:', paras)
    description['date'] = _getParagraphContentByLabel('Datierung:', paras)
    description['pagination'] = _getParagraphContentByLabel('Paginierung:', paras)
    description['measureNumbers'] = _getParagraphContentByLabel('Taktzahlen:', paras)
    description['instrumentation'] = _getParagraphContentByLabel('Besetzung:', paras)
    description['annotations'] = _getParagraphContentByLabel('Eintragungen:', paras)

    ############## Get content items
    contentIndex = _getParagraphIndexByLabel('Inhalt:', paras, paras)
    commentsIndex = _getParagraphIndexByLabel('Textkritischer Kommentar:', paras, paras) or 50 # len(paras) - 1  

    description['content'] = _getItems(paras[(contentIndex + 1):commentsIndex])

    sourceDescription['description'] = description

    return sourceDescription


############################################
# Helper function: _extractWritingInstruments
############################################
def _extractWritingInstruments(writingInstrumentsText: str) -> WritingInstruments:
  """
  Extracts the main and secondary writing instruments from the given text.

  Args:
      writingInstrumentsText (str): The text to extract writing instruments from.

  Returns:
      A dictionary of type WritingInstruments that represents the set of writing instruments
        extracted from the text string. If no writing instruments are found in the input text, the default value of an empty main writing instrument and
      an empty list of secondary writing instruments is returned.
  """
  # Default value for empty writing instruments
  writingInstruments = {'main': '', 'secondary': []}
  if writingInstrumentsText is not None:
      strippedWritingInstruments = _stripByDelimiter(writingInstrumentsText, ';')

      # Strip . from last main and secondary writing instruments
      main = strippedWritingInstruments[0].strip().rstrip('.')
      if len(strippedWritingInstruments) > 1:
        secondary = [instr.strip().rstrip('.') for instr in _stripByDelimiter(strippedWritingInstruments[1], ',')]
      else:
        secondary = []
      writingInstruments = {'main': main, 'secondary': secondary}
  return writingInstruments


############################################
# Helper function: _findLabelTagInSoup
############################################
def _findLabelTagInSoup(label: str, paras: List[Tag]) -> Optional[Tag]:
  """
  Searches for a specific label in a list of BeautifulSoup tags.

  Args:
    label (str): The label to search for.
    paras (List[Tag]): The list of BeautifulSoup tags to search within.

  Returns:
    The BeautifulSoup.Tag with the specified label.
  """
  for para in paras:
     if para.find(text=re.compile(label)):
        return para.find(text=re.compile(label))


############################################
# Helper function: _findParentTagOfLabelInSoup
############################################
def _findParentTagOfLabelInSoup(label: str, paras: List[Tag]) -> Optional[Tag]:
  """
  Searches for the parent of a BeautifulSoup.Tag containing the specified label.

  Args:
    label (str): The label to search for.
    paras (List[Tag]): The list of BeautifulSoup tags to search within.

  Returns:
    The parent element of the BeautifulSoup.Tag with the specified label, or None if not found.
  """
  labelTag = _findLabelTagInSoup(label, paras)
  return labelTag.parent if labelTag is not None else None


############################################
# Helper function: _findSiblings
############################################
def _findSiblings(siblingPara: Tag, paraList: List[Tag]) -> List[Tag]:
    """
    Recursively finds all sibling paragraphs of a given first sibling paragraph in a given list of paragrphas
    and finishes the recursion if the paragraph contains a <strong> tag or ends with a period.

    Args:
        siblingPara (BeautifulSoup.Tag): The first sibling paragraph to start the search from.
        siblingParas (List[Tag]): A list of sibling paragraphs to append to.

    Returns:
        List[BeautifulSoup.Tag]: A list of all sibling paragraphs.
    """
    # Check if the current paragraph contains a <strong> tag
    if siblingPara.find('strong'):
        return paraList
    # Check if the current paragraph ends with a period
    elif siblingPara.text.endswith('.'):
      paraList.append(siblingPara)
      return paraList
    # If the current paragraph does not meet the criteria, recursively search the next sibling
    else:
      paraList.append(siblingPara)
      return _findSiblings(siblingPara.next_sibling, paraList)


############################################
# Helper function: _findSiglumIndices
############################################
def _findSiglumIndices(paras: List[Tag]) -> List[int]:
  """
  Finds the indices of all paragraphs in a list of BeautifulSoup `Tag` objects that contain a single bold siglum.

  Args:
      paras (List[Tag]): A list of BeautifulSoup `Tag` objects representing paragraphs.

  Returns:
      A list of integers representing the indices of the paragraphs that contain a single bold siglum.
  """
  regpattern = re.compile(r'^([A-Z]{1})$') # matches single siglum
  
  siglum_indices = []

  for index, para in enumerate(paras):
      if para.find('strong', text=regpattern): # if para contains a single bold siglum
          siglum_indices.append(index)

  return siglum_indices


############################################
# Helper function: _getFolioLabel
############################################
def _getFolioLabel(strippedParaText: str, folioStr: str) -> str:
    """
    Extracts the folio label from a paragraph of text containing a folio number.

    Args:
        strippedParaText (str): The text of the paragraph with leading/trailing whitespace removed.
        folioStr (str): The string indicating the folio number, such as 'Bl.'.

    Returns:
        str: The extracted folio label if found in the paragraph text, otherwise returns an empty string.
    """
    folioLabel = ''

    if folioStr in strippedParaText:
        folioLabel = strippedParaText.lstrip('\t')
        folioLabel = folioLabel.replace(folioStr + '\xa0', '').strip()
        folioLabel = folioLabel.replace(folioStr, '').strip()
        
    return folioLabel   


############################################
# Helper function: _getFolios
############################################
def _getFolios(siblingParas: List[Tag]) -> List[Folio]:
    """
    Parses a list of sibling paragraphs to extract folios and their system groups.

    Args:
        siblingParas (List[BeautifulSoup.Tag]): A list of BeautifulSoup Tag objects representing sibling paragraphs.

    Returns:
        List[Folio]: A list of dictionaries representing folios and their system groups.
    """
    folios = []
  
    for para in siblingParas:
        strippedParaText = _stripByDelimiter(para.text, ' \t')
        if len(strippedParaText) == 1:
           strippedParaText = _stripByDelimiter(para.text, '\t')

        # Check sibling paragraph for folioStr to create a new folio entry
        if para.find(text=re.compile(folioStr)):
            # Create folio object
            folio = copy.deepcopy(emptyFolio)

            folio['folio'] = _getFolioLabel(strippedParaText[0].strip(), folioStr)
            folio['systemGroups'] = [_getSystemGroup(strippedParaText)]

            # Add folio to folios
            folios.append(folio)

        # If there is no folioStr, but a systemStr, add a new systemGroup to the folio's systemGroups
        elif not para.find(text=re.compile(folioStr)) and para.find(text=re.compile(systemStr)):
            folio['systemGroups'].append(_getSystemGroup(strippedParaText))

    return folios


############################################
# Helper function: _getItem
############################################
def _getItem(para: Tag) -> ContentItem:
    """
    Extracts a source description item from a given paragraph tag.

    Args:
        para (BeautifulSoup.Tag): The paragraph tag to extract the item information from.

    Returns:
        ContentItem: A dictionary containing the extracted content item information.
    """
    delimiter = '('
    
    # Get content of para with inner tags
    paraContent = _stripTag(para, 'p')
    strippedParaContent = _stripByDelimiter(paraContent, delimiter)

    # Get text content of para without inner tags
    paraText = para.text
    strippedParaText = _stripByDelimiter(paraText, delimiter)

    # Extract itemLabel
    itemLabel = strippedParaText[0].strip()
    
    # When there is a slash in the item label, 
    # it means that we probably have multiple sketch items for a row table.
    # In that case, link to 'SkRT'
    if (itemLabel.find('/') != -1):
      itemLinkTo = 'SkRT'
    # In all other cases, link to the id created from the itemLabel
    else:
      itemLinkTo = itemLabel.replace(' ', '_').replace('.', '_')

    # Extract itemDescription (re-add delimiter that was removed in the stripping action above; and remove trailing colon)
    if len(strippedParaContent) == 1:
        print('Something went wrong. Maybe there is some bold formatting in line:', para)
    itemDescription = delimiter + strippedParaContent[1].strip().rstrip(':')

    # Create item object
    item = copy.deepcopy(emptyContentItem)
    item['item'] = itemLabel or ''
    item['itemLinkTo'] = itemLinkTo or ''
    item['itemDescription'] = itemDescription or ''
    
    return item

############################################
# Helper function: _getItems
############################################
def _getItems(paras: List[Tag]) -> List[ContentItem]:
  """
  Given a list of BeautifulSoup Tag objects representing paragraphs, extracts the items and their associated folios from
  the paragraphs and returns a list of content item dictionaries.

  Parameters:
  - paras (List[Tag]): A list of BeautifulSoup Tag objects representing paragraphs.

  Returns:
  - List[ContentItem]: A list of dictionaries, where each dictionary represents a content item and its associated folios.
  """
  items = []

  for para in paras:
      if para.find('strong'):    
          # Find item
          item = _getItem(para)

          # Find all paragraphs that belong to an item
          siblingParas = []
          siblingParas = _findSiblings(para.next_sibling, siblingParas)
          
          # Find folios of all paragraphs of an item
          folios = _getFolios(siblingParas)

          item['folios'] = folios
          items.append(item)
  
  return items


############################################
# Helper function: _getParagraphIndexByLabel
############################################
def _getParagraphIndexByLabel(label: str, pList: list, paras: List[Tag]) -> int:
  """
  Gets the index of the first BeautifulSoup `p` element containing the specified label.

  Args:
    label (str): The label to search for.
    pList (list): A list of BeautifulSoup `p` elements.
    paras (List[Tag]): The list of BeautifulSoup tags to search within.

  Returns:
    The index of the BeautifulSoup `p` tag containing the specified label, or -1 if not found.
  """
  parentTagOfLabel = _findParentTagOfLabelInSoup(label, paras)
  if parentTagOfLabel in pList:
    return pList.index(parentTagOfLabel)
  else:
    return -1
  

############################################
# Helper function: _getParagraphContentByLabel
############################################
def _getParagraphContentByLabel(label: str, paras: List[Tag]) -> str:
  """
  Returns the content of the paragraph containing the specified label within the BeautifulSoup object.
  If the label is not found, an empty string is returned.

  Args:
      label (str): The label to search for within the BeautifulSoup object.
      paras (List[Tag]): The list of BeautifulSoup tags to search within.

  Returns:
      str: The content of the BeautifulSoup `p` tag containing the label, with leading and trailing whitespace removed.
  """
  contentParagraph = _findParentTagOfLabelInSoup(label, paras)
  if contentParagraph is not None:
    strippedContent = _stripTag(contentParagraph, 'p')
    content = _stripByDelimiter(strippedContent, label)[1]
    if content.endswith(';'):
      content += '<br />'
      content += _stripTag(contentParagraph.next_sibling, 'p')
  else:
    content = ''  
  return content.strip()


############################################
# Helper function: _getSystemGroup
############################################
def _getSystemGroup(strippedParaText: List[str]) -> List[List[System]]:
    """
    Extracts system groups from a list of stripped paragraph texts.

    Args:
        strippedParaText (List[str]): The stripped paragraph text containing system groups.

    Returns:
        List[List[System]]: A list of lists of system objects.
    """
    systemGroup = []

    for i in range(len(strippedParaText)):
        # Skip folio label
        if folioStr in strippedParaText[i]: continue

        # Create system object
        system = copy.deepcopy(emptySystem)

        # Extract system label
        if systemStr in strippedParaText[i]:
            strippedSystemText = _stripByDelimiter(strippedParaText[i], ':')
            systemLabel = strippedSystemText[0].replace(systemStr, '').strip()

            system['system'] = systemLabel

            # Extract measure label
            if len(strippedSystemText) == 1: 
               continue
            else:   
              if measureStr in strippedSystemText[1]:
                  # Remove leading measure string and trailing colon or dot.
                  measureLabel = strippedSystemText[1].lstrip(measureStr).rstrip('.;').strip()
                  system['measure'] = measureLabel
              else:
                  # Extract row label
                  # pattern matches, e.g., "Gg (1)", "KUgis (38)", or "Gg (I)", "KUgis (XXXVIII)", but also "Gg", "KUgis"
                  pattern = r"([A-Z]{1,2})([a-z]{1,3})(\s[(](\d{1,2}|[I,V,X,L]{1,7})[)])?" 
                  
                  if re.search(pattern, strippedSystemText[1]):
                    rowText = re.findall(pattern, strippedSystemText[1])[0]

                    row = copy.deepcopy(emptyRow)
                    row['rowType'] = rowText[0]
                    row['rowBase'] = rowText[1]
                    if len(rowText) > 3:
                      row['rowNumber'] = rowText[3]

                    system['row'] = row

            systemGroup.append(system)

        else:
          print('No', systemStr, 'found in', strippedParaText[i])

    return systemGroup


############################################
# Helper function: _stripByDelimiter
############################################
def _stripByDelimiter(inputStr: str, delimiter: str) -> List[str]:
  """
  Splits a string by a delimiter and returns a list of stripped substrings.

  Args:
      inputStr (str): The input string to split and strip.
      delimiter (str): The delimiter to split the string by.

  Returns:
      List[str]: A list of stripped substrings.
  """
  strippedSubstringList: List[str] = [s.strip() for s in inputStr.split(delimiter)]
  return strippedSubstringList


############################################
# Helper function: _stripTag
############################################
def _stripTag(input: Any, tag: str) -> str:
  """
  Strips opening and closing tags from an HTML/XML string and returns the
  content within the tags as a string.

  Args:
    input (Any): The input containing the HTML/XML tags.
    tag (str): The name of the tag to strip.

  Returns:
    str: The content within the specified tags, with leading and trailing whitespace removed.
  """
  strippedStr = ''
  inputStr = str(input)
  # Strip opening and closing tags from input
  inputStr = inputStr.lstrip('<' + tag + '>').rstrip('</' + tag + '>')
  # Strip trailing white space
  inputStr = inputStr.strip()
  strippedStr = inputStr
  return strippedStr

