#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unify Link Box IDs - Pure Python Script

This script unifies link box svgGroupIds in JSON textcritic files
and corresponding SVG files. 

For each linkBox:
- The new ID is formatted as: {entry_id}to{sheetId}
  where sheetId is extracted from the linkTo.sheetId field

Example:
- Entry ID: "op25_WE"
- LinkBox svgGroupId: "g6407"
- LinkBox linkTo.sheetId: "M_317_Sk2"
- New ID: "op25_WEtoM_317_Sk2"
"""

import sys
from utils.extraction_utils import extract_link_boxes, extract_moldenhauer_number
from utils.file_utils import (
    load_and_validate_inputs, create_svg_loader, save_results
)
from utils.svg_utils import (
    find_matching_svg_files_by_class, find_relevant_svg_files, update_svg_id_by_class
)


def process_single_link_box(svg_group_id, link_box, entry_id, matching_files,
                            get_svg_data):
    """Process a single linkBox through the complete update workflow.

    Handles duplicate detection, JSON updates, and SVG file modifications
    for a single link box svgGroupId.

    Args:
        svg_group_id (str): The original ID to replace
        link_box (dict): The linkBox object to update
        entry_id (str): The entry ID for naming
        matching_files (list): List of SVG files containing this ID
        get_svg_data (function): Function to load SVG data

    Returns:
        bool: True if updated successfully, False if skipped
    """
    if len(matching_files) == 0:
        print(
            f" [!] ERROR: '{svg_group_id}' with class 'link-box' not found "
            f"in any relevant SVG files"
        )
        return False
    if len(matching_files) > 1:
        print(
            f" [!] WARNING: '{svg_group_id}' found in {len(matching_files)} "
            f"files: {matching_files}"
        )
        print(
            "     Skipping due to multiple occurrences - "
            "manual review required"
        )
        return False

    # Get sheet ID from linkTo
    sheet_id = link_box.get('linkTo', {}).get('sheetId', '')
    if not sheet_id:
        print(f" [!] ERROR: No sheetId found in linkBox with svgGroupId '{svg_group_id}'")
        return False

    # Create new ID: g-lb-{entry_id}-to-{sheetId}
    new_id = f"g-lb-{entry_id}-to-{sheet_id}"

    # Update JSON
    link_box['svgGroupId'] = new_id
    print(f" [JSON] Changing '{svg_group_id}' -> '{new_id}'")

    # Update the single matching SVG file
    svg_filename = matching_files[0]
    svg_data = get_svg_data(svg_filename)
    svg_data["content"], error = update_svg_id_by_class(
        svg_data["content"], svg_group_id, new_id, "link-box"
    )
    if error:
        print(f" [!] WARNING: {error}")
        return False
    
    print(f" [SVG] Changing '{svg_group_id}' -> '{new_id}' in {svg_filename}")

    return True


def process_textcritics_entry(textcritics_entry, all_svg_files, get_svg_data):
    """Process a single textcritics entry and all its linkBoxes.

    Args:
        textcritics_entry (dict): Single textcritics entry
        all_svg_files (list): List of all available SVG files
        get_svg_data (function): Function to load SVG data

    Returns:
        None: Modifies entry in place and handles file operations
    """
    if not isinstance(textcritics_entry, dict):
        return

    entry_id = textcritics_entry.get('id', '')
    if not entry_id:
        return

    print(f"\nProcessing Entry ID: {entry_id}")

    # Get relevant SVG files for this entry
    current_main_number = extract_moldenhauer_number(entry_id)
    relevant_svgs = find_relevant_svg_files(
        entry_id, all_svg_files, current_main_number
    )

    if "SkRT" in entry_id:
        print(f" SkRT anchor detected: {entry_id}")
    else:
        print(f" Standard anchor: {entry_id}")

    print(f" Relevant SVGs ({len(relevant_svgs)}): {relevant_svgs}")

    # Extract all linkBoxes from this entry
    link_boxes = extract_link_boxes(textcritics_entry)

    if not link_boxes:
        print(" No linkBoxes to process")
        return

    print(f" Found {len(link_boxes)} linkBox(es)")

    # Process each linkBox
    for link_box in link_boxes:
        svg_group_id = link_box.get('svgGroupId', '')
        if not svg_group_id:
            print(" [!] ERROR: linkBox without svgGroupId")
            continue

        # Find all matching SVG files for this ID
        matching_files = find_matching_svg_files_by_class(
            svg_group_id, relevant_svgs, get_svg_data, "link-box"
        )

        # Update if single occurrence found
        process_single_link_box(
            svg_group_id, link_box, entry_id, matching_files, get_svg_data
        )


def unify_link_box_ids(json_path, svg_folder):
    """Unify link box IDs in JSON and SVG files.

    For each JSON entry:
    1. Collect all linkBoxes
    2. Find those IDs in relevant SVG files (with link-box class)
    3. Replace with {entry_id}to{sheetId} format

    Args:
        json_path (str): Path to the JSON textcritics file
        svg_folder (str): Path to the folder containing SVG files

    Returns:
        bool: True if processing completed successfully
    """
    print("--- Starting Link Box ID processing ---")

    # Load and validate inputs
    json_data, all_svg_files = load_and_validate_inputs(json_path, svg_folder)

    # Initialize SVG loader
    final_svg_cache = {}
    loaded_svg_texts = {}
    get_svg_data = create_svg_loader(
        svg_folder, final_svg_cache, loaded_svg_texts
    )

    # Get entries from textcritics data structure
    all_textcritics_entries = (
        json_data.get('textcritics', json_data)
        if isinstance(json_data, dict)
        else json_data
    )

    # Process each textcritics entry independently
    for textcritics_entry in all_textcritics_entries:
        process_textcritics_entry(
            textcritics_entry, all_svg_files, get_svg_data
        )

    # Save all modified files
    save_results(json_data, loaded_svg_texts, json_path)

    print("\n--- Link Box ID processing completed ---")
    return True


def main():
    """Main function to process link box IDs"""

    # --- CONFIGURATION ---

    ##### fill in:
    json_path = './tests/data/textcritics.json'

    ##### fill in:
    svg_folder = './tests/img/'

    try:
        success = unify_link_box_ids(json_path, svg_folder)
        if success:
            print("\n Finished!")
        else:
            print("\n Processing completed with warnings.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except (ValueError, KeyError, OSError, PermissionError) as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
