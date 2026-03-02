#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SVG utilities for TKK Group ID processing

Functions for finding, matching, and updating SVG files and their content.
"""

import re
from .extraction_utils import extract_moldenhauer_number


def find_matching_svg_files(svg_group_id, relevant_svgs, get_svg_data):
    """Find all SVG files that contain a specific svgGroupId with tkk class.

    Args:
        svg_group_id (str): The ID to search for
        relevant_svgs (list): List of relevant SVG filenames to search in
        get_svg_data (function): Function to load SVG data

    Returns:
        list: List of SVG filenames that contain the ID with tkk class
    """
    matching_files = []
    for svg_filename in relevant_svgs:
        svg_data = get_svg_data(svg_filename)
        # Test if this ID exists with class tkk in this SVG
        test_content, error = update_svg_id(svg_data["content"], svg_group_id, "test")
        if error is None and test_content != svg_data["content"]:
            matching_files.append(svg_filename)
    return matching_files


def find_relevant_svg_files(new_id, all_svg_files, current_main_number):
    """Find relevant SVG files for a given entry ID.

    Args:
        new_id (str): The entry ID
        all_svg_files (list): List of all SVG files
        current_main_number (str): Extracted number from the ID

    Returns:
        list: List of relevant SVG filenames
    """
    # Helper function for candidate filtering
    def matches_moldenhauer_number(filename):
        return current_main_number == extract_moldenhauer_number(filename)

    # SkRT entries: only row table files
    if "SkRT" in new_id:
        return [
            f for f in all_svg_files
            if matches_moldenhauer_number(f) and "Reihentabelle" in f
        ]

    # Filter candidate files: matching Moldenhauer number, excluding row table files
    candidate_svg_files = [
        f for f in all_svg_files
        if matches_moldenhauer_number(f) and "Reihentabelle" not in f
    ]

    # TF entries: specific Textfassung
    tf_match = re.search(r'TF(\d+)', new_id)
    if tf_match:
        tf_number = tf_match.group(1)
        return [f for f in candidate_svg_files if f"Textfassung{tf_number}" in f]

    # Sk entries: specific Sketch with exact matching
    sk_match = re.search(r'(Sk\d+(?:_\d+)*)', new_id)
    if sk_match:
        sk_identifier = sk_match.group(1)
        # Prevent matching when the Sk identifier is followed by any digit or underscore
        pattern = rf'{re.escape(sk_identifier)}(?![\d_])'
        return [f for f in candidate_svg_files if re.search(pattern, f)]

    # Default: all non-Reihentabelle files for this Moldenhauer number
    return candidate_svg_files


def update_svg_id(svg_content, old_val, new_val):
    """Update an ID in SVG content while preserving elements with class="tkk".

    Handles elements that may have multiple CSS classes, as long as "tkk" is one of them.
    Supports both single and double quotes, and various attribute orders.

    Examples of supported formats:
    - <g class="tkk" id="old-id">  (single class)
    - <g class="tkk other-class" id="old-id">  (tkk first)
    - <g class="active tkk selected" id="old-id">  (tkk in middle)
    - <g id="old-id" class='other-class tkk'>  (tkk last, single quotes)

    Args:
        svg_content (str): The SVG content to process
        old_val (str): The old ID value to replace
        new_val (str): The new ID value to use as replacement

    Returns:
        tuple: (updated_content, error_message)
               error_message is None if successful, string if error occurred
    """
    # Only match the ID if the same tag contains class with "tkk" as a word
    escaped_id = re.escape(old_val)

    # Create patterns for both quote styles and both attribute orders
    # Use word boundaries (\b) to match "tkk" as complete word within class attribute
    patterns = [
        # Double quotes: id first, then class with tkk
        f'<[^>]*?id="{escaped_id}"[^>]*?class="[^"]*\\btkk\\b[^"]*"[^>]*?>',
        # Double quotes: class with tkk first, then id
        f'<[^>]*?class="[^"]*\\btkk\\b[^"]*"[^>]*?id="{escaped_id}"[^>]*?>',
        # Single quotes: id first, then class with tkk
        f"<[^>]*?id='{escaped_id}'[^>]*?class='[^']*\\btkk\\b[^']*'[^>]*?>",
        # Single quotes: class with tkk first, then id
        f"<[^>]*?class='[^']*\\btkk\\b[^']*'[^>]*?id='{escaped_id}'[^>]*?>",
    ]

    # Count total tkk matches first
    total_tkk_matches = 0
    for pattern in patterns:
        total_tkk_matches += len(re.findall(pattern, svg_content))

    if total_tkk_matches > 1:
        return (svg_content,
                f"Multiple class='tkk' elements found with ID '{old_val}' "
                f"({total_tkk_matches} occurrences)")

    def replace_id(match):
        full_tag = match.group(0)
        return (full_tag.replace(f'id="{old_val}"', f'id="{new_val}"')
                        .replace(f"id='{old_val}'", f"id='{new_val}'"))

    # Apply all patterns
    content = svg_content
    for pattern in patterns:
        content = re.sub(pattern, replace_id, content)
    return content, None
