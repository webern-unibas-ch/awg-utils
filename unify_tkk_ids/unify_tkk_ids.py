#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unify TKK Group IDs - Pure Python Script
Made by Eli (lili041 --Github) with Google Gemini

This script unifies TKK group IDs in JSON textcritic files and corresponding SVG files.
You need to fill in the path to the JSON textcritics file and the SVG folder path.

ACHTUNG: TODO entries are skipped, but they are also not counted within a block,
and counting continues as if nothing happened: g-tkk-1, g-tkk-2, TODO, g-tkk-3, ...
"""

import sys
from extraction_utils import extract_moldenhauer_number, extract_svg_group_ids
from file_utils import load_and_validate_inputs, create_svg_loader, save_results
from svg_utils import find_matching_svg_files, find_relevant_svg_files, update_svg_id
from validation_utils import display_validation_report


def process_single_svg_group_id(svg_group_id, block_comment, matching_files,
                               get_svg_data, new_id):
    """Process a single svgGroupId through the complete update workflow.

    Handles duplicate detection, JSON updates, and SVG file modifications
    for a single svgGroupId. Returns success/failure status for counter management.

    Args:
        svg_group_id (str): The original ID to replace
        block_comment (dict): The block comment object to update
        matching_files (list): List of SVG files containing this ID
        get_svg_data (function): Function to load SVG data
        new_id (str): The new ID to use as replacement

    Returns:
        bool: True if updated successfully, False if skipped
    """
    if len(matching_files) == 0:
        print(f" [!] ERROR: '{svg_group_id}' with class 'tkk' not found in any relevant SVG files")
        return False
    if len(matching_files) > 1:
        print(f" [!] WARNING: '{svg_group_id}' found in {len(matching_files)} files: "
              f"{matching_files}")
        print("     Skipping due to multiple occurrences - manual review required")
        return False

    # Update JSON and SVG for single occurrence
    block_comment['svgGroupId'] = new_id
    print(f" [JSON] Changing '{svg_group_id}' -> '{new_id}'")

    # Update the single matching SVG file
    svg_filename = matching_files[0]
    svg_data = get_svg_data(svg_filename)
    svg_data["content"], _ = update_svg_id(svg_data["content"], svg_group_id, new_id)
    print(f" [SVG] Changing '{svg_group_id}' -> '{new_id}' in {svg_filename}")

    return True


def process_textcritics_entry(textcritics_entry, all_svg_files, get_svg_data, prefix):
    """Process a single textcritics entry and all its block comments.

    Args:
        textcritics_entry (dict): Single textcritics entry
        all_svg_files (list): List of all available SVG files
        get_svg_data (function): Function to load SVG data
        prefix (str): Prefix for new IDs

    Returns:
        None: Modifies entry in place and handles file operations
    """
    if not isinstance(textcritics_entry, dict):
        return

    textcritics_entry_id = textcritics_entry.get('id', '')
    if not textcritics_entry_id:
        return

    print(f"\nProcessing Entry ID: {textcritics_entry_id}")

    # Get relevant SVG files for this entry
    current_main_number = extract_moldenhauer_number(textcritics_entry_id)
    relevant_svgs = find_relevant_svg_files(
        textcritics_entry_id, all_svg_files, current_main_number
    )

    if "SkRT" in textcritics_entry_id:
        print(f" SkRT anchor detected: {textcritics_entry_id}")
    else:
        print(f" Standard anchor: {textcritics_entry_id}")

    print(f" Relevant SVGs ({len(relevant_svgs)}): {relevant_svgs}")

    # Extract all svgGroupIds from this entry's blockComments
    svg_group_ids, block_comments = extract_svg_group_ids(textcritics_entry)

    if not svg_group_ids:
        print(" No svgGroupIds to process")
        return

    # Process each svgGroupId and replace with g-tkk-1, g-tkk-2, etc.
    counter = 1
    for svg_group_id, block_comment in zip(svg_group_ids, block_comments):
        # Find all matching SVG files for this ID
        matching_files = find_matching_svg_files(svg_group_id, relevant_svgs, get_svg_data)

        # Update if single occurrence found
        new_id = f"{prefix}{counter}"
        if process_single_svg_group_id(svg_group_id, block_comment, matching_files,
                                      get_svg_data, new_id):
            counter += 1


def unify_tkk_ids(json_path, svg_folder, prefix="g-tkk-"):
    """Unify TKK IDs in JSON and SVG files.

    For each JSON entry:
    1. Collect all svgGroupIds from blockComments
    2. Find those IDs in relevant SVG files (where tkk class exists)
    3. Replace with g-tkk-1, g-tkk-2, etc. in sequence per entry

    Args:
        json_path (str): Path to the JSON textcritics file
        svg_folder (str): Path to the folder containing SVG files
        prefix (str): Prefix to use for new IDs (default: "g-tkk-")

    Returns:
        bool: True if processing completed successfully
    """
    print("--- Starting TKK ID processing ---")

    # Load and validate inputs
    json_data, all_svg_files = load_and_validate_inputs(json_path, svg_folder)

    # Initialize SVG loader
    final_svg_cache = {}
    loaded_svg_texts = {}
    get_svg_data = create_svg_loader(svg_folder, final_svg_cache, loaded_svg_texts)

    # Get entries from textcritics data structure
    all_textcritics_entries = (
        json_data.get('textcritics', json_data)
        if isinstance(json_data, dict)
        else json_data
    )

    # Process each textcritics entry independently
    for textcritics_entry in all_textcritics_entries:
        process_textcritics_entry(textcritics_entry, all_svg_files, get_svg_data, prefix)

    # Save all modified files
    save_results(json_data, loaded_svg_texts, json_path)

    # Generate final validation report
    display_validation_report(json_data, prefix, loaded_svg_texts)

    return True



def main():
    """Main function to process tkk IDs"""

    # --- CONFIGURATION ---

    ##### fill in:
    json_path = './tests/data/textcritics.json'

    ##### fill in:
    svg_folder = './tests/img/'

    prefix = "g-tkk-"

    try:
        success = unify_tkk_ids(json_path, svg_folder, prefix)
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


if __name__ == "__main__": # pragma: no cover
    main()
