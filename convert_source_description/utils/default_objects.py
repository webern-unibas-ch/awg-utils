"""Default objects that are used to create new source descriptions objects in the utils module."""

from utils.typed_classes import (
    ContentItem,
    Folio,
    LinkBox,
    PhysDesc,
    Row,
    SourceDescription,
    SourceList,
    System,
    TextcriticalComment,
    TextcriticalCommentBlock,
    TextCritics,
    TextcriticsList,
)

########
DEFAULT_SOURCE_LIST: SourceList = {"sources": []}

DEFAULT_SOURCE_DESCRIPTION: SourceDescription = {
    "id": "",
    "siglum": "",
    "siglumAddendum": "",
    "type": "",
    "location": "",
    "physDesc": {},
}

DEFAULT_PHYS_DESC: PhysDesc = {
    "conditions": [],
    "writingMaterialStrings": [],
    "writingInstruments": {"main": "", "secondary": []},
    "titles": [],
    "dates": [],
    "paginations": [],
    "measureNumbers": [],
    "instrumentations": [],
    "annotations": [],
    "contents": [],
}

DEFAULT_CONTENT_ITEM: ContentItem = {
    "item": "",
    "itemLinkTo": {},
    "itemDescription": "",
    "folios": [],
}

DEFAULT_FOLIO: Folio = {
    "folio": "",
    "folioLinkTo": "",
    "folioDescription": "",
    "systemGroups": [],
}

DEFAULT_SYSTEM: System = {"system": "", "measure": "", "linkTo": ""}

DEFAULT_ROW: Row = {"rowType": "", "rowBase": "", "rowNumber": ""}

DEFAULT_TEXTCRITICS_LIST: TextcriticsList = {"textcritics": [], "corrections": []}

DEFAULT_TEXTCRITICS: TextCritics = {
    "id": "",
    "label": "",
    "evaluations": [],
    # "rowTable": False,
    "commentary": {"preamble": "", "comments": []},
    "linkBoxes": [],
}

DEFAULT_TEXTCRITICAL_COMMENT_BLOCK: TextcriticalCommentBlock = {
    "blockHeader": "",
    "blockComments": [],
}

DEFAULT_TEXTCRITICAL_COMMENT: TextcriticalComment = {
    "svgGroupId": "TODO",
    "measure": "",
    "system": "",
    "position": "",
    "comment": "",
}

DEFAULT_LINK_BOX: LinkBox = {"svgGroupId": "", "linkTo": ""}
