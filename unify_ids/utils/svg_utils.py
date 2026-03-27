#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SVG utilities for TKK Group ID processing

Functions for finding, matching, and updating SVG files and their content.
"""

import re

from .extraction_utils import extract_moldenhauer_number


def build_id_to_file_index_by_class(relevant_svg_files, get_svg_data, target_class):
    """Build map: svg group ID -> list of SVG filenames for elements matching target class.

    Each file is scanned once, and duplicate IDs within the same file are indexed once.

    Args:
        relevant_svg_files (list): List of SVG filenames to scan.
        get_svg_data (function): Function to load SVG data.
        target_class (str): The class token that indexed elements must contain.

    Returns:
        dict: Mapping of svg ID to list of filenames containing that ID with target class.
    """
    id_to_files = {}

    for svg_filename in relevant_svg_files:
        svg_data = get_svg_data(svg_filename)
        svg_root = svg_data.get("svg_root") if svg_data else None
        if svg_root is None:
            continue

        # Collect unique IDs first, then use shared matching helper for consistency.
        ids_in_file = {
            elem.get("id")
            for elem in svg_root.iter()
            if elem.get("id")
        }

        seen_ids_in_file = set()
        for svg_id in ids_in_file:
            matches = _find_elements_by_id_and_class(svg_root, svg_id, target_class)
            if not matches or svg_id in seen_ids_in_file:
                continue

            id_to_files.setdefault(svg_id, []).append(svg_filename)
            seen_ids_in_file.add(svg_id)

    return id_to_files


def find_relevant_svg_files(new_id, all_svg_files, current_mnr_number):
    """Find relevant SVG files for a given entry ID.

    Args:
        new_id (str): The entry ID
        all_svg_files (list): List of all SVG files
        current_mnr_number (str): Extracted mnr number from the ID

    Returns:
        list: List of relevant SVG filenames
    """
    # Pre-extract file info to avoid redundant parsing
    file_info = [
        {
            "file_name": filename,
            "mnr": extract_moldenhauer_number(filename),
            "is_rowtable": "Reihentabelle" in filename,
        }
        for filename in all_svg_files
    ]

    # SkRT entries: only row table files
    if "SkRT" in new_id:
        return [
            info["file_name"]
            for info in file_info
            if info["mnr"] == current_mnr_number and info["is_rowtable"]
        ]

    # Filter candidate files: matching Moldenhauer number, excluding row table files
    candidate_svg_files = [
        info["file_name"]
        for info in file_info
        if info["mnr"] == current_mnr_number and not info["is_rowtable"]
    ]

    # Look for specific patterns in the filename for TF and Sk entries
    tf_match = re.search(r"TF(\d+)", new_id)
    sk_match = re.search(r"(Sk\d+(?:_\d+)*)", new_id)

    if tf_match:
        tf_number = tf_match.group(1)
        return [f for f in candidate_svg_files if f"Textfassung{tf_number}" in f]

    if sk_match:
        sk_identifier = sk_match.group(1)
        # Prevent matching when the Sk identifier is followed by any digit or underscore
        pattern = rf"{re.escape(sk_identifier)}(?![\d_])"
        return [f for f in candidate_svg_files if re.search(pattern, f)]

    # Default: all non-Reihentabelle files for this Moldenhauer number
    return candidate_svg_files


def update_svg_id_by_class(svg_data, old_id, new_id, target_class):
    """Update an ID in a cached SVG root for elements with a specific class.

    Mutates the element in-place and marks the cache entry as dirty so it
    will be serialized and written to disk during the save phase.

    Args:
        svg_data (dict): The SVG cache entry with an 'svg_root' key (Element)
        old_id (str): The old ID value to replace
        new_id (str): The new ID value to use as replacement
        target_class (str): The CSS class to match (e.g., "link-box", "tkk")

    Returns:
        tuple: (changed, error_message)
               changed is True if the svg_root was modified, False otherwise.
               error_message is None if no error occurred, string otherwise.
    """
    svg_root = svg_data.get("svg_root") if svg_data else None
    if svg_root is None:
        return False, "No parsed svg_root available"

    matches = _find_elements_by_id_and_class(svg_root, old_id, target_class)

    if not matches:
        return False, f"'{old_id}' with class containing '{target_class}' not found"
    if len(matches) > 1:
        return (
            False,
            f"Multiple class='{target_class}' elements found with ID '{old_id}' "
            f"({len(matches)} occurrences)",
        )

    if matches[0].get("id") == new_id:
        return False, None

    matches[0].set("id", new_id)
    svg_data["dirty"] = True
    return True, None


def _find_elements_by_id_and_class(parsed_svg_root, element_id, target_class):
    """Find all elements in parsed SVG with a specific ID and class.

    Args:
        parsed_svg_root (Element): The root element of parsed SVG
        element_id (str): The ID attribute value to match
        target_class (str): The CSS class token to match

    Returns:
        list: List of matching Element objects, or empty list if no matches
    """
    matches = []
    for elem in parsed_svg_root.iter():
        if elem.get("id") == element_id:
            class_attr = elem.get("class", "")
            if target_class in class_attr.split():
                matches.append(elem)

    return matches
