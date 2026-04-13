#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils package for convert_source_description.

This package contains utility modules for converting source descriptions:
- default_objects: Default typed dictionary templates
- file_utils: Word/JSON file input and output helpers
- paragraph_utils: Paragraph lookup and labeled-content extraction helpers
- typed_classes: TypedDict models for source and textcritical data
- utils: Main conversion orchestration helpers
- utils_helper: Low-level parsing and transformation helpers
"""

# Import commonly used objects to make them available at package level.
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
from .paragraph_utils import ParagraphUtils
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
from .utils import ConversionUtils
from .utils_helper import ConversionUtilsHelper

__all__ = [
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
	# utils
	"ConversionUtils",
	# utils_helper
	"ConversionUtilsHelper",
]
