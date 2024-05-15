"""Default objects that are used to create new source descriptions objects in the utils module."""

from typed_classes import (Row, System, Folio, ContentItem, Description,
                           SourceDescription, SourceList, LinkBox,
                           TextcriticalComment, TextCritics, TextcriticsList)

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
    "textcritics": []
}

defaultTextcritics: TextCritics = {
    "id": "",
    "label": "",
    "description": [],
    # "rowTable": False,
    "comments": [],
    "linkBoxes": []
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
