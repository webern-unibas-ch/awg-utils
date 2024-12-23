"""Default objects that are used to create new source descriptions objects in the utils module."""

from typed_classes import (
    Row,
    System,
    Folio,
    ContentItem,
    Description,
    SourceDescription,
    SourceList,
    LinkBox,
    TextcriticalComment,
    TextCritics,
    TextcriticalCommentBlock,
    TextcriticsList)

########
defaultSourceList: SourceList = {
    "sources": []
}

defaultSourceDescription: SourceDescription = {
    "id": "",
    "siglum": "",
    "siglumAddendum": "",
    "type": "",
    "location": "",
    "description": {}
}

defaultDescription: Description = {
    "desc": [],
    "writingMaterialStrings": [],
    "writingInstruments": {
        "main": "",
        "secondary": []
    },
    "titles": [],
    "dates": [],
    "paginations": [],
    "measureNumbers": [],
    "instrumentations": [],
    "annotations": [],
    "contents": []
}

defaultContentItem: ContentItem = {
    "item": "",
    "itemLinkTo": {},
    "itemDescription": "",
    "folios": []
}

defaultFolio: Folio = {
    "folio": "",
    "folioLinkTo": "",
    "folioDescription": "",
    "systemGroups": []
}

defaultSystem: System = {
    "system": "",
    "measure": "",
    "linkTo": ""
}

defaultRow: Row = {
    "rowType": "",
    "rowBase": "",
    "rowNumber": ""
}

defaultTextcriticsList: TextcriticsList = {
    "textcritics": [],
    "corrections": []
}

defaultTextcritics: TextCritics = {
    "id": "",
    "label": "",
    "evaluations": [],
    # "rowTable": False,
    "commentary": {
        "preamble": "",
        "comments": []
    },
    "linkBoxes": []
}

defaultTextcriticalCommentBlock: TextcriticalCommentBlock = {
    "blockHeader": "",
    "blockComments": []
}

defaultTextcriticalComment: TextcriticalComment = {
    "svgGroupId": "TODO",
    "measure": "",
    "system": "",
    "position": "",
    "comment": ""
}

defaultLinkBox: LinkBox = {
    "svgGroupId": "",
    "linkTo": ""
}
