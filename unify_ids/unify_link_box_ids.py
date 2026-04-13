#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unify Link Box IDs - Pure Python Script

This script unifies link box svgGroupIds in JSON textcritic files
and corresponding SVG files.

For each linkBox:
- The new ID is formatted as: awg-lb-{entry_id}-to-{sheetId}
  where sheetId is extracted from the linkTo.sheetId field

Example:
- Entry ID: "M34_Sk1"
- LinkBox svgGroupId: "g6407"
- LinkBox linkTo.sheetId: "M_317_Sk2"
- New ID: "awg-lb-m34_sk1c-to-m317_sk2a"
"""

import sys

from utils.constants import LINKBOX
from utils.extraction_utils import (
    extract_id_suffix,
    extract_file_info_list,
    extract_link_boxes,
    extract_textcritics_entry_id,
)
from utils.file_utils import load_and_validate_inputs, create_svg_loader, save_results
from utils.logger_utils import Logger
from utils.models import ContextHelpers
from utils.svg_utils import (
    build_entry_id_index,
    update_svg_id_by_class,
)


def process_single_link_box(
    textcritics_entry_id, svg_group_id, parent_link_boxes, matching_files, helpers
):
    """Process a single linkBox through the complete update workflow.

    Handles duplicate detection, JSON updates, and SVG file modifications
    for a single link box svgGroupId.

    Args:
        textcritics_entry_id (str): The textcritics entry ID for naming
        svg_group_id (str): The original ID to replace
        parent_link_boxes (list): List of all linkBoxes in the entry
        matching_files (list): SVG files that contain svg_group_id with link-box class
        helpers (ContextHelpers): Helper functions and logger

    Returns:
        bool: True if updated successfully, False if skipped
    """

    if len(matching_files) == 0:
        helpers.logger.log(
            "error",
            "svg_group_id_not_found",
            textcritics_entry_id,
            (
                f"'{svg_group_id}' with class '{LINKBOX.css_class}' "
                "not found in any relevant SVG files"
            ),
        )
        return False

    # Find the link box to update by svg_group_id
    link_box = next(
        (lb for lb in parent_link_boxes if lb.get("svgGroupId") == svg_group_id), None
    )

    # Get target sheetId from linkBox
    target_sheet_id = link_box.get("linkTo", {}).get("sheetId", "")
    if not target_sheet_id:
        helpers.logger.log(
            "error",
            "missing_sheetid",
            textcritics_entry_id,
            f"No target sheetId found in linkBox with svgGroupId '{svg_group_id}'",
        )
        return False

    # Log if multiple SVGs reference the same original svgGroupId
    expanded_json = False
    if len(matching_files) > 1:
        if helpers.logger.verbose:
            print(
                f" [!] MULTIPLE SVGs reference '{svg_group_id}'. "
                f"Expanding JSON entry to {len(matching_files)} distinct IDs."
            )
        expanded_json = True

    # Remove the original linkBox from the parent list
    parent_link_boxes.remove(link_box)

    success = True
    for svg_filename in matching_files:
        # Extract suffix from filename if present
        suffix = extract_id_suffix(svg_filename)
        entry_id = textcritics_entry_id + suffix if suffix else textcritics_entry_id

        # Warn if entry_id is identical to target_sheet_id
        if entry_id == target_sheet_id:
            helpers.logger.log(
                "warning",
                "self_reference",
                textcritics_entry_id,
                (
                    f"Self-reference detected: entry_id ('{entry_id}') "
                    f"is identical to target_sheet_id ('{target_sheet_id}') "
                    f"for svgGroupId '{svg_group_id}'"
                ),
            )

        # Create new ID
        new_group_id = f"{LINKBOX.prefix}{entry_id}-to-{target_sheet_id}".lower()

        # Shallow-copy linkBox with overridden svgGroupId and append to JSON list
        parent_link_boxes.append({**link_box, "svgGroupId": new_group_id})

        if expanded_json:
            helpers.logger.log(
                "info",
                "json_expanded",
                textcritics_entry_id,
                (
                    f"Expanded JSON entry: Added new linkBox with svgGroupId '{new_group_id}' "
                    f"for original '{svg_group_id}'"
                ),
            )
        helpers.logger.log_id_change_json(svg_group_id, new_group_id)

        # Update SVG file
        svg_data = helpers.svg_loader(svg_filename)
        _, update_error = update_svg_id_by_class(
            svg_data, svg_group_id, new_group_id, LINKBOX.css_class
        )
        if update_error:
            if helpers.logger.verbose:
                print(f" [!] WARNING: {update_error} in {svg_filename}")
            success = False
        else:
            helpers.logger.log_id_change_svg(svg_group_id, new_group_id, svg_filename)

    return success


def process_link_boxes_per_entry(
    textcritics_entry_id, link_boxes, id_to_file_index, helpers
):
    """Process all linkBoxes for a single textcritics entry."""
    # Iterate over a copy to avoid modifying the list during iteration
    for link_box in list(link_boxes):
        svg_group_id = link_box.get("svgGroupId", "")
        if not svg_group_id:
            helpers.logger.log(
                "error",
                "missing_svgGroupId",
                textcritics_entry_id,
                "linkBox without svgGroupId",
            )
            continue

        matching_files = id_to_file_index.get(svg_group_id, [])

        process_single_link_box(
            textcritics_entry_id, svg_group_id, link_boxes, matching_files, helpers
        )

    # Sort linkBoxes by svgGroupId after all processing
    if isinstance(link_boxes, list):
        link_boxes.sort(key=lambda lb: lb.get("svgGroupId", ""))


def process_textcritics_entry(textcritics_entry, file_info_list, svg_loader, logger):
    """Process a single textcritics entry and all its linkBoxes.

    Args:
        textcritics_entry (dict): Single textcritics entry
        file_info_list (list): List of all available SVG file infos
        svg_loader (function): Function to load SVG data
        logger (Logger): Logger instance for reporting
    """
    textcritics_entry_id = extract_textcritics_entry_id(textcritics_entry)
    if textcritics_entry_id is None:
        return

    logger.log_processing_entry_start(textcritics_entry_id)

    # Extract all linkBoxes from this entry
    link_boxes = extract_link_boxes(textcritics_entry)

    logger.log_items_found(link_boxes, "linkBoxes")
    if not link_boxes:
        return

    id_to_file_index = build_entry_id_index(
        textcritics_entry_id, file_info_list, svg_loader, logger, LINKBOX.css_class
    )

    helpers = ContextHelpers(svg_loader=svg_loader, logger=logger)

    process_link_boxes_per_entry(
        textcritics_entry_id, link_boxes, id_to_file_index, helpers
    )


def unify_link_box_ids(json_path, svg_folder, logger):
    """Unify link box IDs in JSON and SVG files.

    For each JSON entry:
    1. Collect all linkBoxes
    2. Find those IDs in relevant SVG files (with link-box class)
    3. Replace with new linkbox IDs in both JSON and SVG

    Args:
        json_path (str): Path to the JSON textcritics file
        svg_folder (str): Path to the folder containing SVG files
        logger (Logger): Logger instance for reporting

    Returns:
        bool: True if processing completed successfully
    """

    logger.log_processing_start("Link Box ID")

    json_data, svg_file_names = load_and_validate_inputs(json_path, svg_folder)

    # Pre-extract file infos to avoid redundant parsing
    file_info_list = extract_file_info_list(svg_file_names)

    svg_file_cache = {}
    svg_loader = create_svg_loader(svg_folder, svg_file_cache)

    textcritics_entries = (
        json_data.get("textcritics", json_data)
        if isinstance(json_data, dict)
        else json_data
    )

    for textcritics_entry in textcritics_entries:
        process_textcritics_entry(textcritics_entry, file_info_list, svg_loader, logger)

    if not logger.dry_run:
        save_results(json_data, svg_file_cache, json_path)

        print("\n--- Link Box ID processing completed ---")
        logger.print_report()

        # later TODO: Validation that there is no link-box class in relevant svgs
        # that do not have a corresponding entry in textcritics.json

    elif logger.verbose:
        print(" [DRY-RUN] Skipping write + validation report.")
        logger.print_report()

    return True


def main():
    """Main function to process link box IDs"""

    # --- CONFIGURATION ---

    ##### fill in:
    json_path = "./tests/data/textcritics.json"

    ##### fill in:
    svg_folder = "./tests/img/"

    try:
        logger = Logger(dry_run=False, verbose=True)
        success = unify_link_box_ids(json_path, svg_folder, logger)
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
