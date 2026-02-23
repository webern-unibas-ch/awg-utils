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

import re
import sys
from extraction_utils import extract_moldenhauer_number, extract_svg_group_ids
from file_utils import load_and_validate_inputs, create_svg_loader, save_results
from validation_utils import display_validation_report


def find_matching_svg_files(svg_group_id, relevant_svgs, get_svg_text):
    """Find all SVG files that contain a specific svgGroupId with tkk class.
    
    Args:
        svg_group_id (str): The ID to search for
        relevant_svgs (list): List of relevant SVG filenames to search in
        get_svg_text (function): Function to load SVG content
        
    Returns:
        list: List of SVG filenames that contain the ID with tkk class
    """
    matching_files = []
    for svg_filename in relevant_svgs:
        svg_data = get_svg_text(svg_filename)
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
        pattern = rf'{re.escape(sk_identifier)}(?!_)'
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


def process_single_svg_group_id(svg_group_id, block_comment, matching_files,
                               get_svg_text, new_id):
    """Process a single svgGroupId through the complete update workflow.
    
    Handles duplicate detection, JSON updates, and SVG file modifications
    for a single svgGroupId. Returns success/failure status for counter management.
    
    Args:
        svg_group_id (str): The original ID to replace
        block_comment (dict): The block comment object to update
        matching_files (list): List of SVG files containing this ID
        get_svg_text (function): Function to load SVG content
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
    svg_data = get_svg_text(svg_filename)
    svg_data["content"], _ = update_svg_id(svg_data["content"], svg_group_id, new_id)
    print(f" [SVG] Changing '{svg_group_id}' -> '{new_id}' in {svg_filename}")

    return True


def process_entry(entry, all_svg_files, get_svg_text, prefix):
    """Process a single textcritics entry and all its block comments.
    
    Args:
        entry (dict): Single textcritics entry
        all_svg_files (list): List of all available SVG files
        get_svg_text (function): Function to load SVG content
        prefix (str): Prefix for new IDs
        
    Returns:
        None: Modifies entry in place and handles file operations
    """
    if not isinstance(entry, dict):
        return

    entry_id = entry.get('id', '')
    if not entry_id:
        return

    print(f"\nProcessing Entry ID: {entry_id}")

    # Get relevant SVG files for this entry
    current_main_number = extract_moldenhauer_number(entry_id)
    relevant_svgs = find_relevant_svg_files(entry_id, all_svg_files, current_main_number)

    if "SkRT" in entry_id:
        print(f" SkRT anchor detected: {entry_id}")
    else:
        print(f" Standard anchor: {entry_id}")

    print(f" Assigned SVGs ({len(relevant_svgs)}): {relevant_svgs}")

    # Extract all svgGroupIds from this entry's blockComments
    svg_group_ids, block_comments = extract_svg_group_ids(entry)

    if not svg_group_ids:
        print(" No svgGroupIds to process")
        return

    # Process each svgGroupId and replace with g-tkk-1, g-tkk-2, etc.
    counter = 1
    for svg_group_id, block_comment in zip(svg_group_ids, block_comments):
        # Find all matching SVG files for this ID
        matching_files = find_matching_svg_files(svg_group_id, relevant_svgs, get_svg_text)

        # Update if single occurrence found
        new_id = f"{prefix}{counter}"
        if process_single_svg_group_id(svg_group_id, block_comment, matching_files,
                                      get_svg_text, new_id):
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
    data, all_svg_files = load_and_validate_inputs(json_path, svg_folder)

    # Initialize SVG loader
    final_svg_cache = {}
    loaded_svg_texts = {}
    get_svg_text = create_svg_loader(svg_folder, final_svg_cache, loaded_svg_texts)

    # Get entries from data structure
    all_entries = data.get('textcritics', data) if isinstance(data, dict) else data

    # Process each entry independently
    for entry in all_entries:
        process_entry(entry, all_svg_files, get_svg_text, prefix)

    # Save all modified files
    save_results(data, loaded_svg_texts, json_path)

    # Generate final validation report
    display_validation_report(data, prefix, loaded_svg_texts)

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
