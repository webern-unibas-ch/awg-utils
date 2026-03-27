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
from utils.models import (
    ContextHelpers,
    SvgGroupIdContext,
    TextcriticsEntryContext,
)
from utils.svg_utils import (
    build_id_to_file_index_by_class,
    find_relevant_svg_files,
    update_svg_id_by_class,
)
from utils.validation_utils import display_validation_report


def get_textcritics_entry_context(textcritics_entry, all_svg_files, logger):
    """Resolve extracted IDs and relevant SVG scope for one textcritics entry."""
    textcritics_entry_id = textcritics_entry.get("id", "")
    if not textcritics_entry_id:
        return None

    svg_group_ids, block_comments = extract_svg_group_ids(textcritics_entry)
    if not svg_group_ids:
        if logger.verbose:
            print(" No svgGroupIds to process")
        return None

    current_mnr_number = extract_moldenhauer_number(textcritics_entry_id)
    relevant_svgs = find_relevant_svg_files(
        textcritics_entry_id, all_svg_files, current_mnr_number
    )

    if logger.verbose:
        logger.log_entry_context(textcritics_entry_id, relevant_svgs)

    return TextcriticsEntryContext(
        textcritics_entry_id=textcritics_entry_id,
        svg_group_ids=svg_group_ids,
        block_comments=block_comments,
        relevant_svgs=relevant_svgs,
    )


def get_single_matching_svg_file(textcritics_entry_id, svg_group_id_context, helpers):
    """Resolve a single target SVG file, logging and counting mismatches."""
    svg_group_id = svg_group_id_context.svg_group_id
    matching_files = svg_group_id_context.matching_files

    if len(matching_files) == 0:
        helpers.logger.log_ids_missing(
            textcritics_entry_id, svg_group_id, TKK.css_class
        )
        return None

    if len(matching_files) > 1:
        helpers.logger.log_ids_multiple(
            textcritics_entry_id,
            svg_group_id,
            matching_files,
        )
        return None

    return matching_files[0]


def _update_svg_target_id(
    textcritics_entry_id, svg_group_id_context, svg_filename, helpers
):
    """Update a matched SVG ID and return whether processing should continue."""
    svg_data = helpers.svg_loader(svg_filename)
    changed, update_error = update_svg_id_by_class(
        svg_data,
        svg_group_id_context.svg_group_id,
        svg_group_id_context.new_id,
        TKK.css_class,
    )

    if update_error is not None:
        helpers.logger.log_svg_error(
            textcritics_entry_id,
            svg_group_id_context.svg_group_id,
            svg_filename,
            update_error,
        )
        return False

    if not changed:
        helpers.logger.log_svg_unchanged(
            textcritics_entry_id, svg_group_id_context.new_id, svg_filename
        )

    return True


def process_entry_svg_group_ids(textcritics_entry_context, id_to_file_index, helpers):
    """Process all svgGroupIds for a single textcritics entry."""
    counter = 1
    entry_id_formatted = textcritics_entry_context.textcritics_entry_id.lower()

    for svg_group_id, block_comment in zip(
        textcritics_entry_context.svg_group_ids,
        textcritics_entry_context.block_comments,
    ):
        helpers.logger.bump_stats("ids_seen")
        matching_files = id_to_file_index.get(svg_group_id, [])
        new_id = f"{TKK.prefix}{entry_id_formatted}-{counter:03d}"
        svg_group_id_context = SvgGroupIdContext(
            svg_group_id=svg_group_id,
            block_comment=block_comment,
            matching_files=matching_files,
            new_id=new_id,
        )

        updated = process_single_svg_group_id(
            textcritics_entry_context.textcritics_entry_id,
            svg_group_id_context,
            helpers,
        )

        if updated:
            counter += 1


def process_single_svg_group_id(textcritics_entry_id, svg_group_id_context, helpers):
    """Process a single svgGroupId through the complete update workflow."""
    svg_filename = get_single_matching_svg_file(
        textcritics_entry_id,
        svg_group_id_context,
        helpers,
    )
    if svg_filename is None:
        return False

    if not _update_svg_target_id(
        textcritics_entry_id,
        svg_group_id_context,
        svg_filename,
        helpers,
    ):
        return False

    helpers.logger.log_id_change(
        svg_group_id_context.svg_group_id,
        svg_group_id_context.new_id,
        svg_filename,
    )

    if helpers.logger.dry_run:
        return True

    svg_group_id_context.block_comment["svgGroupId"] = svg_group_id_context.new_id
    return True


def process_textcritics_entry(textcritics_entry, all_svg_files, svg_loader, logger):
    """Process a single textcritics entry and all its block comments."""
    if not isinstance(textcritics_entry, dict):
        return

    if logger.verbose:
        textcritics_entry_id = textcritics_entry.get("id", "")
        if textcritics_entry_id:
            print(f"\nProcessing textcritics entry ID: {textcritics_entry_id}")

    context = get_textcritics_entry_context(textcritics_entry, all_svg_files, logger)
    if context is None:
        return

    logger.bump_stats("entries_seen")

    textcritics_entry_context = context
    helpers = ContextHelpers(svg_loader=svg_loader, logger=logger)

    id_to_file_index = build_id_to_file_index_by_class(
        textcritics_entry_context.relevant_svgs,
        helpers.svg_loader,
        target_class=TKK.css_class,
    )

    process_entry_svg_group_ids(
        textcritics_entry_context,
        id_to_file_index,
        helpers,
    )


def unify_tkk_ids(json_path, svg_folder, logger):
    """Unify TKK IDs in JSON and SVG files.

     For each JSON entry:
     1. Collect all svgGroupIds and their block comments
     2. Find those IDs in relevant SVG files ( with tkk class)
     3. Replace with new TKK IDs in both JSON and SVG

    Args:
        json_path (str): Path to the JSON file containing textcritics entries
        svg_folder (str): Path to the folder containing SVG files
        logger (Logger): Logger instance for reporting

    Returns:
        bool: True if processing completed successfully, False if there were issues
    """
    if logger.verbose:
        print("--- Starting TKK ID processing ---")
        if logger.dry_run:
            print(" [DRY-RUN] No files will be written.")

    json_data, all_svg_files = load_and_validate_inputs(json_path, svg_folder)

    svg_file_cache = {}
    svg_loader = create_svg_loader(svg_folder, svg_file_cache)

    all_textcritics_entries = (
        json_data.get("textcritics", json_data)
        if isinstance(json_data, dict)
        else json_data
    )

    for textcritics_entry in all_textcritics_entries:
        process_textcritics_entry(
            textcritics_entry,
            all_svg_files,
            svg_loader,
            logger,
        )

    if not logger.dry_run:
        if logger.stats["ids_changed"] > 0:
            save_results(json_data, svg_file_cache, json_path)
        elif logger.verbose:
            print(" No changes detected; skipping writes.")

        display_validation_report(json_data, svg_file_cache, TKK.prefix)
        logger.print_report()

    elif logger.verbose:
        print(" [DRY-RUN] Skipping write + validation report.")
        logger.print_report()

    if logger.verbose:
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
        logger = Logger(dry_run=False, verbose=True)
        success = unify_tkk_ids(json_path, svg_folder, logger)
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
