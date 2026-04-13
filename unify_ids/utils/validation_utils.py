#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation utilities for TKK ID processing.

This module contains functions for validating the success of TKK ID unification
across JSON and SVG files, ensuring all IDs have been properly updated.
"""

from .extraction_utils import has_class_token


def validate_json_entries(data, prefix):
    """Validate JSON entries for unchanged svgGroupId values.

    Args:
        data (dict): The processed JSON textcritics data structure
        prefix (str): The target prefix that all updated IDs should start with

    Returns:
        int: Number of errors found
    """
    errors_found = 0
    all_entries = data.get("textcritics", data) if isinstance(data, dict) else data

    for entry in all_entries:
        entry_id = entry.get("id", "Unknown")
        comments_list = entry.get("commentary", {}).get("comments", [])
        for comment_group in comments_list:
            for block_comment in comment_group.get("blockComments", []):
                val = block_comment.get("svgGroupId")
                if val and not val.startswith(prefix) and val != "TODO":
                    print(
                        f"  [!] JSON ERROR: Unchanged ID '{val}' in Entry: {entry_id}"
                    )
                    errors_found += 1

    return errors_found


def validate_svg_entries(svg_file_cache, prefix, target_class="tkk"):
    """
    Validate SVG entries for IDs that have not been updated with the target prefix.

    Args:
        svg_file_cache (dict): Cache for currently loaded SVG files to validate.
        prefix (str): The target prefix that all updated SVG IDs should start with.
        target_class (str): The target class name for SVG elements to be validated
                            (default is "tkk").

    Returns:
        int: Number of SVG ID errors found (IDs not updated with the prefix).
    """
    errors = 0
    for svg_filename, svg_data in svg_file_cache.items():
        svg_root = (svg_data or {}).get("svg_root")
        if svg_root is None:
            continue
        seen = set()

        for elem in svg_root.iter():
            svg_id = elem.get("id")
            class_attr = elem.get("class", "")

            if not svg_id or svg_id in seen:
                continue
            if not has_class_token(class_attr, target_class):
                continue

            seen.add(svg_id)
            if not svg_id.startswith(prefix):
                errors += 1
                print(
                    f"  [!] SVG ORPHAN: ID '{svg_id}' with class '{target_class}' "
                    f"in {svg_filename} was NOT updated."
                )

    return errors


def display_validation_report(data, svg_file_cache, prefix, target_class="tkk"):
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
        svg_file_cache (dict): Cache for currently loaded SVG files to validate.
        prefix (str): The target prefix that all updated IDs should start with
                     (e.g., "awg-tkk-").
        target_class (str): The target class name for SVG elements to be
                            validated (default is "tkk").

    Returns:
        None: Prints validation results directly to stdout. Does not return values.
    """
    print("\n--- UNCERTAINTY & ERROR REPORT ---")

    json_errors = validate_json_entries(data, prefix)
    svg_errors = validate_svg_entries(svg_file_cache, prefix, target_class=target_class)
    total_errors = json_errors + svg_errors

    if total_errors == 0:
        print("  [✓] All JSON and SVG 'tkk' IDs successfully updated.")
    else:
        print(f"  [!] Total issues found: {total_errors}")
