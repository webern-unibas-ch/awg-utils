#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils package for convert_source_description.

This package contains utility modules for converting source descriptions:
- constants: Shared string and parsing constants
- default_objects: Default typed dictionary templates
- file_utils: Word/JSON file input and output helpers
- index_utils: Paragraph index lookup helpers
- paragraph_utils: Paragraph lookup and labeled-content extraction helpers
- replacement_utils: Text replacement and glyph formatting helpers
- sources_utils: Source description parsing and conversion helpers
- stripping_utils: HTML tag stripping and cleanup helpers
- textcritics_utils: Textcritical commentary parsing helpers
- typed_classes: TypedDict models for source and textcritical data
"""

# Import commonly used objects to make them available at package level.
from .constants import (
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
from .default_objects import (
    DEFAULT_CONTENT_ITEM,
    DEFAULT_FOLIO,
    DEFAULT_LINK_BOX,
    DEFAULT_PHYS_DESC,
    DEFAULT_ROW,
    DEFAULT_SOURCE_DESCRIPTION,
    DEFAULT_SOURCE_LIST,
    DEFAULT_SYSTEM,
    DEFAULT_TEXTCRITICAL_COMMENT,
    DEFAULT_TEXTCRITICAL_COMMENT_BLOCK,
    DEFAULT_TEXTCRITICS,
    DEFAULT_TEXTCRITICS_LIST,
)
from .file_utils import FileUtils
from .index_utils import IndexUtils
from .paragraph_utils import ParagraphUtils
from .replacement_utils import ReplacementUtils
from .sources_utils import SourcesUtils
from .stripping_utils import StrippingUtils
from .textcritics_utils import TextcriticsUtils
from .typed_classes import (
    ContentItem,
    ContentItemLinkTo,
    Folio,
    LinkBox,
    PhysDesc,
    Row,
    SourceDescription,
    SourceList,
    System,
    TextcriticalComment,
    TextcriticalCommentary,
    TextcriticalCommentBlock,
    TextCritics,
    TextcriticsList,
    WritingInstruments,
)

__all__ = [
    # constants
    "COLON",
    "COMMA",
    "FOLIO_STR",
    "FULL_STOP",
    "M_SIGLE",
    "MX_SIGLE",
    "MEASURE_STR",
    "PAGE_STR",
    "PARENTHESIS",
    "P_TAG",
    "ROWTABLE_SHEET_ID",
    "SEMICOLON",
    "SLASH",
    "STAR",
    "STAR_STR",
    "STRONG_TAG",
    "SUP_TAG",
    "SYSTEM_STR",
    "UNDERSCORE",
    # default_objects
    "DEFAULT_CONTENT_ITEM",
    "DEFAULT_FOLIO",
    "DEFAULT_LINK_BOX",
    "DEFAULT_PHYS_DESC",
    "DEFAULT_ROW",
    "DEFAULT_SOURCE_DESCRIPTION",
    "DEFAULT_SOURCE_LIST",
    "DEFAULT_SYSTEM",
    "DEFAULT_TEXTCRITICAL_COMMENT",
    "DEFAULT_TEXTCRITICAL_COMMENT_BLOCK",
    "DEFAULT_TEXTCRITICS",
    "DEFAULT_TEXTCRITICS_LIST",
    # file_utils
    "FileUtils",
    # index_utils
    "IndexUtils",
    # paragraph_utils
    "ParagraphUtils",
    # replacement_utils
    "ReplacementUtils",
    # sources_utils
    "SourcesUtils",
    # stripping_utils
    "StrippingUtils",
    # textcritics_utils
    "TextcriticsUtils",
    # typed_classes
    "ContentItem",
    "ContentItemLinkTo",
    "Folio",
    "LinkBox",
    "PhysDesc",
    "Row",
    "SourceDescription",
    "SourceList",
    "System",
    "TextcriticalComment",
    "TextcriticalCommentary",
    "TextcriticalCommentBlock",
    "TextCritics",
    "TextcriticsList",
    "WritingInstruments",
]
