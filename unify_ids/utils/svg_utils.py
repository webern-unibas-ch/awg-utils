#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SVG utilities for TKK Group ID processing

Functions for finding, matching, and updating SVG files and their content.
"""

import re
import xml.etree.ElementTree as ET

from .extraction_utils import extract_moldenhauer_number


def find_matching_svg_files_by_class(
    svg_group_id, relevant_svg_files, get_svg_data, target_class="tkk"
):
    """
    Find all SVG files that contain a specific svgGroupId with a required class.

    Args:
        svg_group_id (str): The ID to search for.
        relevant_svg_files (list): List of relevant SVG filenames to search in.
        get_svg_data (function): Function to load SVG data.
        target_class (str): The target class name for SVG elements to match
                            (default is "tkk").

    Returns:
        list: List of SVG filenames that contain the ID with the target class.
    """
    matching_files = []

    for svg_filename in relevant_svg_files:
        svg_data = get_svg_data(svg_filename)
        if not svg_data:
            continue
        svg_content = svg_data.get("content", "")
        parsed_svg_content, error = _parse_svg_xml(svg_content)
        if error:
            continue
        matches = _find_elements_by_id_and_class(
            parsed_svg_content, svg_group_id, target_class
        )
        if matches:
            matching_files.append(svg_filename)

    return matching_files


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


def update_svg_id_by_class(svg_content, old_id, new_id, target_class):
    """Update an ID in SVG content for elements with a specific class.

    Similar to update_svg_id but allows specifying which class to match.
    Supports both single and double quotes, and various attribute orders.

    Args:
        svg_content (str): The SVG content to process
        old_id (str): The old ID value to replace
        new_id (str): The new ID value to use as replacement
        target_class (str): The CSS class to match (e.g., "link-box", "tkk")

    Returns:
        tuple: (updated_content, error_message)
               error_message is None if successful, string if error occurred
    """
    # Check if the SVG content has an XML declaration
    has_xml_declaration = bool(re.match(r"^\s*<\?xml\b", svg_content))

    # Register the SVG namespace before serialization
    ET.register_namespace("", "http://www.w3.org/2000/svg")

    # Parse SVG content
    parsed_svg_content, parse_error = _parse_svg_xml(svg_content)
    if parse_error:
        return svg_content, parse_error

    # Find all elements with the matching id and class
    matches = _find_elements_by_id_and_class(parsed_svg_content, old_id, target_class)

    if not matches:
        return (
            svg_content,
            f"'{old_id}' with class containing '{target_class}' not found",
        )
    if len(matches) > 1:
        return (
            svg_content,
            "Multiple class="
            f"'{target_class}' elements found with ID '{old_id}' "
            f"({len(matches)} occurrences)",
        )

    # Update the id
    matches[0].set("id", new_id)

    # Serialize back to SVG content with stable formatting
    updated_content = _serialize_svg_xml(
        parsed_svg_content,
        include_xml_declaration=has_xml_declaration,
    )

    return updated_content, None


def _find_elements_by_id_and_class(parsed_svg_content, element_id, target_class):
    """Find all elements in parsed SVG with a specific ID and class.

    Args:
        parsed_svg_content (Element): The root element of parsed SVG
        element_id (str): The ID attribute value to match
        target_class (str): The CSS class token to match

    Returns:
        list: List of matching Element objects, or empty list if no matches
    """
    matches = []
    for elem in parsed_svg_content.iter():
        if elem.get("id") == element_id:
            class_attr = elem.get("class", "")
            if target_class in class_attr.split():
                matches.append(elem)

    return matches


def _parse_svg_xml(svg_content):
    """Parse SVG XML content into an ElementTree root.

    Args:
        svg_content (str): The SVG content to parse

    Returns:
        tuple: (root_element_or_none, error_message_or_none)
    """
    try:
        return ET.fromstring(svg_content), None
    except ET.ParseError as e:
        return None, f"XML parse error: {e}"


def _serialize_svg_xml(parsed_svg_content, include_xml_declaration=True):
    """Serialize SVG ElementTree root with stable declaration and EOF newline.

    Args:
        parsed_svg_content (Element): The root element of the parsed SVG.
        include_xml_declaration (bool): Whether to include XML declaration.

    Returns:
        str: Serialized SVG content.
    """
    updated_content = ET.tostring(
        parsed_svg_content, encoding="unicode", xml_declaration=include_xml_declaration
    )

    # Normalize XML declaration:
    if updated_content.startswith("<?xml"):
        decl_end = updated_content.find("?>") + 2
        xml_decl = updated_content[:decl_end]
        rest = updated_content[decl_end:]
        xml_decl = xml_decl.replace("'", '"')
        xml_decl = xml_decl.replace("utf-8", "UTF-8")
        updated_content = xml_decl + rest

    # Remove whitespace before self-closing tags
    updated_content = re.sub(r"\s+/>", "/>", updated_content)

    # Add newline at the end if not present
    if not updated_content.endswith("\n"):
        updated_content += "\n"

    return updated_content
