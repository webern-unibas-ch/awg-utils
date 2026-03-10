#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils package for unify_tkk_ids

This package contains utility modules for TKK ID processing:
- extraction_utils: Functions for extracting data from JSON and SVG files
- file_utils: File I/O operations and validation
- svg_utils: SVG file processing and manipulation
- validation_utils: Validation and reporting utilities
"""

# Import all commonly used functions to make them available at package level
from .extraction_utils import extract_moldenhauer_number, extract_svg_group_ids
from .file_utils import load_and_validate_inputs, create_svg_loader, save_results
from .svg_utils import find_matching_svg_files, find_relevant_svg_files, update_svg_id
from .validation_utils import display_validation_report, validate_json_entries, validate_svg_entries

__all__ = [
    # extraction_utils
    'extract_moldenhauer_number',
    'extract_svg_group_ids',
    # file_utils
    'load_and_validate_inputs',
    'create_svg_loader',
    'save_results',
    # svg_utils
    'find_matching_svg_files',
    'find_relevant_svg_files',
    'update_svg_id',
    # validation_utils
    'display_validation_report',
    'validate_json_entries',
    'validate_svg_entries'
]
