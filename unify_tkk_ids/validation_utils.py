#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation utilities for TKK ID processing.

This module contains functions for validating the success of TKK ID unification
across JSON and SVG files, ensuring all IDs have been properly updated.
"""

import re


def validate_json_entries(data, prefix):
    """Validate JSON entries for unchanged svgGroupId values.

    Args:
        data (dict): The processed JSON textcritics data structure
        prefix (str): The target prefix that all updated IDs should start with

    Returns:
        int: Number of errors found
    """
    errors_found = 0
    all_entries = data.get('textcritics', data) if isinstance(data, dict) else data

    for entry in all_entries:
        entry_id = entry.get('id', 'Unknown')
        comments_list = entry.get('commentary', {}).get('comments', [])
        for comment_group in comments_list:
            for block_comment in comment_group.get('blockComments', []):
                val = block_comment.get('svgGroupId')
                if val and not val.startswith(prefix) and val != "TODO":
                    print(f"  [!] JSON ERROR: Unchanged ID '{val}' in Entry: {entry_id}")
                    errors_found += 1

    return errors_found


def validate_svg_entries(loaded_svgs, prefix):
    """Validate SVG entries for unchanged tkk class IDs.

    Args:
        loaded_svgs (dict): Dictionary mapping SVG filenames to their content
        prefix (str): The target prefix that all updated IDs should start with

    Returns:
        int: Number of errors found
    """
    errors_found = 0
    tkk_id_regex = re.compile(
        r'<[^>]+?class=["\'][^"\']*\btkk\b[^"\']*["\'][^>]+?id=["\']([^"\']+)["\']'
        r'|<[^>]+?id=["\']([^"\']+)["\'][^>]+?class=["\'][^"\']*\btkk\b[^"\']*["\']'
    )

    for filename, sdata in loaded_svgs.items():
        matches = tkk_id_regex.findall(sdata["content"])
        for match in matches:
            found_id = match[0] if match[0] else match[1]
            if not found_id.startswith(prefix):
                print(f"  [!] SVG ORPHAN: ID '{found_id}' with class 'tkk' in {filename} "
                      f"was NOT updated.")
                errors_found += 1

    return errors_found


def display_validation_report(data, prefix, loaded_svgs):
    """Validate and report the success of TKK ID unification process.

    Performs post-processing validation to ensure all TKK-related IDs have been
    properly updated with the specified prefix. Identifies and reports:
    - JSON entries with unchanged svgGroupId values (excluding "TODO" entries)
    - SVG elements with class="tkk" that retain old ID values

    Generates a comprehensive error report with specific file locations and
    entry IDs for debugging purposes.

    Args:
        data (dict): The processed JSON textcritics data structure containing
                    textcritics entries with commentary and blockComments.
        prefix (str): The target prefix that all updated IDs should start with
                     (e.g., "g-tkk-").
        loaded_svgs (dict): Dictionary mapping SVG filenames to their content
                           and path information from the processing cache.

    Returns:
        None: Prints validation results directly to stdout. Does not return values.
    """
    print("\n--- UNCERTAINTY & ERROR REPORT ---")

    json_errors = validate_json_entries(data, prefix)
    svg_errors = validate_svg_entries(loaded_svgs, prefix)
    total_errors = json_errors + svg_errors

    if total_errors == 0:
        print("  [✓] All JSON and SVG 'tkk' IDs successfully updated.")
    else:
        print(f"  [!] Total issues found: {total_errors}")
