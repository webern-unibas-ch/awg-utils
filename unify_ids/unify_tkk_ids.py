#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unify TKK Group IDs - Pure Python Script
Made by Eli (lili041 --Github) with Google Gemini
"""

import sys

from utils.constants import TKK
from utils.extraction_utils import extract_moldenhauer_number, extract_svg_group_ids
from utils.file_utils import load_and_validate_inputs, create_svg_loader, save_results
from utils.logger_utils import Logger
from utils.models import Settings
from utils.svg_utils import (
    build_id_to_file_index_by_class,
    find_relevant_svg_files,
    update_svg_id_by_class,
)
from utils.validation_utils import display_validation_report


def process_single_svg_group_id(
    textcritics_entry_id,
    svg_group_id,
    block_comment,
    matching_files,
    get_svg_data,
    new_id,
    settings,
    logger,
):
    """Process a single svgGroupId through the complete update workflow."""
    if len(matching_files) == 0:
        logger.bump_stats("ids_missing")
        logger.log(
            "error",
            "svg_group_id_not_found",
            textcritics_entry_id,
            f"'{svg_group_id}' with class '{TKK.css_class}' not found in any relevant SVG files",
        )
        return False

    if len(matching_files) > 1:
        logger.bump_stats("ids_multiple")
        logger.log(
            "warning",
            "multiple_svg_occurrences",
            textcritics_entry_id,
            f"'{svg_group_id}' found in {len(matching_files)} files: {matching_files}; "
            f"skipping — manual review required",
        )
        return False

    svg_filename = matching_files[0]
    svg_data = get_svg_data(svg_filename)

    changed, update_error = update_svg_id_by_class(
        svg_data, svg_group_id, new_id, TKK.css_class
    )

    if update_error is not None:
        logger.bump_stats("svg_errors")
        logger.log(
            "warning",
            "svg_update_error",
            textcritics_entry_id,
            f"Could not update '{svg_group_id}' in {svg_filename}; JSON unchanged ({update_error})",
        )
        return False

    if not changed:
        logger.bump_stats("svg_unchanged")
        logger.log(
            "info",
            "svg_unchanged",
            textcritics_entry_id,
            f"SVG already had '{new_id}' in {svg_filename}; updating JSON only",
        )

    logger.bump_stats("ids_changed")

    if settings.verbose:
        dry_marker = " [DRY-RUN]" if settings.dry_run else ""
        print(f"{dry_marker} [JSON] Changing '{svg_group_id}' -> '{new_id}'")
        print(
            f"{dry_marker} [SVG]  Changing '{svg_group_id}' -> '{new_id}' in {svg_filename}"
        )

    if settings.dry_run:
        return True

    block_comment["svgGroupId"] = new_id
    return True


def process_textcritics_entry(
    textcritics_entry, all_svg_files, get_svg_data, settings, logger
):
    """Process a single textcritics entry and all its block comments."""
    if not isinstance(textcritics_entry, dict):
        return

    textcritics_entry_id = textcritics_entry.get("id", "")
    if not textcritics_entry_id:
        return

    logger.bump_stats("entries_seen")
    if settings.verbose:
        print(f"\nProcessing textcritics entry ID: {textcritics_entry_id}")

    svg_group_ids, block_comments = extract_svg_group_ids(textcritics_entry)

    if not svg_group_ids:
        if settings.verbose:
            print(" No svgGroupIds to process")
        return

    current_mnr_number = extract_moldenhauer_number(textcritics_entry_id)
    relevant_svgs = find_relevant_svg_files(
        textcritics_entry_id, all_svg_files, current_mnr_number
    )

    if settings.verbose:
        if "SkRT" in textcritics_entry_id:
            print(f" SkRT anchor detected: {textcritics_entry_id}")
        else:
            print(f" Standard anchor: {textcritics_entry_id}")
        print(f" Relevant SVGs ({len(relevant_svgs)}): {relevant_svgs}")

    id_to_file_index = build_id_to_file_index_by_class(
        relevant_svgs,
        get_svg_data,
        target_class=TKK.css_class,
    )

    counter = 1
    entry_id_formatted = textcritics_entry_id.lower()

    for svg_group_id, block_comment in zip(svg_group_ids, block_comments):
        logger.bump_stats("ids_seen")

        matching_files = id_to_file_index.get(svg_group_id, [])

        new_id = f"{TKK.prefix}{entry_id_formatted}-{counter:03d}"

        updated = process_single_svg_group_id(
            textcritics_entry_id,
            svg_group_id,
            block_comment,
            matching_files,
            get_svg_data,
            new_id,
            settings=settings,
            logger=logger,
        )

        if updated:
            counter += 1


def unify_tkk_ids(json_path, svg_folder, settings):
    """Unify TKK IDs in JSON and SVG files.

     For each JSON entry:
     1. Collect all svgGroupIds and their block comments
     2. Find those IDs in relevant SVG files ( with tkk class)
     3. Replace with new TKK IDs in both JSON and SVG

    Args:
        json_path (str): Path to the JSON file containing textcritics entries
        svg_folder (str): Path to the folder containing SVG files
        settings (Settings): Configuration settings for processing

    Returns:
        bool: True if processing completed successfully, False if there were issues
    """
    logger = Logger(verbose=settings.verbose)

    if settings.verbose:
        print("--- Starting TKK ID processing ---")
        if settings.dry_run:
            print(" [DRY-RUN] No files will be written.")

    json_data, all_svg_files = load_and_validate_inputs(json_path, svg_folder)

    svg_file_cache = {}
    get_svg_data = create_svg_loader(svg_folder, svg_file_cache)

    all_textcritics_entries = (
        json_data.get("textcritics", json_data)
        if isinstance(json_data, dict)
        else json_data
    )

    for textcritics_entry in all_textcritics_entries:
        process_textcritics_entry(
            textcritics_entry,
            all_svg_files,
            get_svg_data,
            settings=settings,
            logger=logger,
        )

    if not settings.dry_run:
        if logger.stats["ids_changed"] > 0:
            save_results(json_data, svg_file_cache, json_path)
        elif settings.verbose:
            print(" No changes detected; skipping writes.")

        display_validation_report(json_data, svg_file_cache, TKK.prefix)
        logger.print_report()

    elif settings.verbose:
        print(" [DRY-RUN] Skipping write + validation report.")
        logger.print_report()

    if settings.verbose:
        logger.print_stats_summary()

    return True


def main():
    """Main function to process tkk IDs"""

    # --- CONFIGURATION ---

    ##### fill in:
    json_path = "./tests/data/textcritics.json"

    ##### fill in:
    svg_folder = "./tests/img/"

    try:
        settings = Settings(dry_run=False, verbose=True)
        success = unify_tkk_ids(json_path, svg_folder, settings)
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
