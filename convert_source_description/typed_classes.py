"""Typed dictionaries used for representing source descriptions."""

from typing import List, NotRequired, TypedDict


############################################
# Typed Classes
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


class ContentItemLinkTo(TypedDict):
    """A typed dictionary that represents a content item linkTo section."""
    complexId: str
    sheetId: str


class ContentItem(TypedDict):
    """A typed dictionary that represents a content item."""
    item: str
    itemLinkTo: ContentItemLinkTo
    itemDescription: str
    folios: List[Folio]


class WritingInstruments(TypedDict):
    """A typed dictionary that represents a set of writing instruments."""
    main: str
    secondary: List[str]


class PhysDesc(TypedDict):
    """A typed dictionary that represents a physical description of a source description."""
    conditions: List[str]
    writingMaterialStrings: List[str]
    writingInstruments: WritingInstruments
    titles: List[str]
    dates: List[str]
    paginationss: List[str]
    measureNumbers: List[str]
    instrumentations: List[str]
    annotations: List[str]
    contents: List[ContentItem]


class SourceDescription(TypedDict):
    """A typed dictionary that represents a source description."""
    id: str
    siglum: str
    siglumAddendum: str
    type: str
    location: str
    physDesc: PhysDesc


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


class TextcriticalCommentBlock(TypedDict):
    """A typed dictionary that represents a textcritical comment block."""
    blockHeader: str
    blockComments: List[TextcriticalComment]

class TextcriticalCommentary(TypedDict):
    """A typed dictionary that represents a textcritical commentary."""
    preamble: str
    comments: List[TextcriticalCommentBlock]


class TextCritics(TypedDict):
    """A typed dictionary that represents a textcritics object."""
    id: str
    label: str
    evaluations: List[str]
    rowTable: bool
    commentary: TextcriticalCommentary
    linkBoxes: List[LinkBox]


class TextcriticsList(TypedDict):
    """A typed dictionary that represents a list of textcritics objects."""
    textcritics: List[TextCritics]
    corrections: List[TextCritics]
