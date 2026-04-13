#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils package for unify_tkk_ids

This package contains utility modules for TKK ID processing:
- constants: Shared constants for ID unification
- extraction_utils: Functions for extracting data from JSON and SVG files
- file_utils: File I/O operations and validation
- logger_utils: Logging and statistics tracking
- models: Data models and configuration classes
- svg_utils: SVG file processing and manipulation
- validation_utils: Validation and reporting utilities
"""

# Import all commonly used functions to make them available at package level
from .constants import TKK, LINKBOX
from .extraction_utils import (
    extract_file_info_list,
    extract_id_suffix,
    extract_link_boxes,
    extract_moldenhauer_number,
    extract_svg_group_ids,
    extract_textcritics_entry_id,
    has_class_token
)
from .file_utils import (
    load_and_validate_inputs,
    create_svg_loader,
    save_results
)
from .logger_utils import Logger
from .models import (
    IdMapping,
    ContextHelpers,
    SvgGroupIdContext,
    TextcriticalComments,
)
from .svg_utils import (
    build_id_to_file_index_by_class,
    build_entry_id_index,
    find_relevant_svg_files,
    update_svg_id_by_class
)
from .validation_utils import (
    display_validation_report,
    validate_json_entries,
    validate_svg_entries
)

__all__ = [
    # constants
    'TKK',
    'LINKBOX',
    # extraction_utils
    'extract_file_info_list',
    'extract_id_suffix',
    'extract_link_boxes',
    'extract_moldenhauer_number',
    'extract_svg_group_ids',
    'extract_textcritics_entry_id',
    'has_class_token',
    # file_utils
    'load_and_validate_inputs',
    'create_svg_loader',
    'save_results',
    # logger_utils
    'Logger',
    # models
    'IdMapping',
    'ContextHelpers',
    'SvgGroupIdContext',
    'TextcriticalComments',
    # svg_utils
    'build_id_to_file_index_by_class',
    'build_entry_id_index',
    'find_relevant_svg_files',
    'update_svg_id_by_class',
    # validation_utils
    'display_validation_report',
    'validate_json_entries',
    'validate_svg_entries'
]
