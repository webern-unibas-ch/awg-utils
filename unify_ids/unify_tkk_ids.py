#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unify TKK Group IDs - Pure Python Script
Made by Eli (lili041 --Github) with Google Gemini
"""

import re
import sys

from utils.constants import TKK
from utils.extraction_utils import (
    extract_moldenhauer_number, extract_svg_group_ids
)
from utils.file_utils import (
    load_and_validate_inputs, create_svg_loader, save_results
)
from utils.models import Settings
from utils.stats_utils import Stats
from utils.svg_utils import (
    find_matching_svg_files_by_class, find_relevant_svg_files, update_svg_id_by_class
)
from utils.validation_utils import display_validation_report

# Global regex patterns and constants
G_TAG_RE = re.compile(r"<g\b[^>]*>", re.IGNORECASE | re.DOTALL)
ATTR_RE = re.compile(r"([:\w-]+)\s*=\s*(\"[^\"]*\"|'[^']*')", re.DOTALL)


def _extract_attrs(tag_text):
    attrs = {}
    for name, value in ATTR_RE.findall(tag_text):
        attrs[name.lower()] = value[1:-1]
    return attrs


def _class_contains(class_attr, needle=TKK.css_class):
    return (needle or "").strip().lower() in (class_attr or "").lower()


def _build_tkk_id_index(relevant_svgs, get_svg_data):
    """Build map: svgGroupId -> [svg filenames], scanning each SVG once."""
    id_to_files = {}

    for svg_filename in relevant_svgs:
        svg_data = get_svg_data(svg_filename)
        content = svg_data.get("content", "")
        seen_ids_in_file = set()

        for g_tag in G_TAG_RE.findall(content):
            attrs = _extract_attrs(g_tag)
            svg_id = attrs.get("id")
            class_attr = attrs.get("class", "")

            # class only needs to contain "tkk"
            if svg_id and _class_contains(class_attr, TKK.css_class) and svg_id not in seen_ids_in_file:
                id_to_files.setdefault(svg_id, []).append(svg_filename)
                seen_ids_in_file.add(svg_id)

    return id_to_files


def _get_cached_matching_files(svg_group_id, relevant_svgs, get_svg_data, cache):
    """Fallback cache using existing matching logic."""
    if svg_group_id not in cache:
        cache[svg_group_id] = find_matching_svg_files_by_class(
            svg_group_id, relevant_svgs, get_svg_data, TKK.css_class
        )
    return cache[svg_group_id]


def process_single_svg_group_id(svg_group_id, block_comment, matching_files,
                                get_svg_data, new_id, settings, stats):
    """Process a single svgGroupId through the complete update workflow."""
    if len(matching_files) == 0:
        stats.bump("ids_missing")
        if settings.verbose:
            print(
                f" [!] ERROR: '{svg_group_id}' with class 'tkk' not found "
                f"in any relevant SVG files"
            )
        return False

    if len(matching_files) > 1:
        stats.bump("ids_multiple")
        if settings.verbose:
            print(
                f" [!] WARNING: '{svg_group_id}' found in {len(matching_files)} "
                f"files: {matching_files}"
            )
            print(
                "     Skipping due to multiple occurrences - "
                "manual review required"
            )
        return False

    svg_filename = matching_files[0]
    svg_data = get_svg_data(svg_filename)

    updated_content, update_error = update_svg_id_by_class(
        svg_data["content"], svg_group_id, new_id, TKK.css_class
    )

    if update_error is not None:
        stats.bump("svg_errors")
        if settings.verbose:
            print(
                f" [!] WARNING: Could not update '{svg_group_id}' in "
                f"{svg_filename}; JSON unchanged ({update_error})"
            )
        return False

    if updated_content == svg_data["content"]:
        stats.bump("svg_unchanged")
        if settings.verbose:
            print(f" [i] SVG already had '{new_id}' in {svg_filename}; updating JSON only")

    stats.bump("ids_changed")

    if settings.verbose:
        dry_marker = " [DRY-RUN]" if settings.dry_run else ""
        print(f"{dry_marker} [JSON] Changing '{svg_group_id}' -> '{new_id}'")
        print(f"{dry_marker} [SVG]  Changing '{svg_group_id}' -> '{new_id}' in {svg_filename}")

    if settings.dry_run:
        return True

    # Keep old behavior for direct unit tests
    block_comment['svgGroupId'] = new_id
    svg_data["content"] = updated_content
    return True


def process_textcritics_entry(
        textcritics_entry, all_svg_files, get_svg_data,
        settings, stats):
    """Process a single textcritics entry and all its block comments."""
    if not isinstance(textcritics_entry, dict):
        return

    textcritics_entry_id = textcritics_entry.get('id', '')
    if not textcritics_entry_id:
        return

    stats.bump("entries_seen")
    if settings.verbose:
        print(f"\nProcessing textcritics entry ID: {textcritics_entry_id}")

    svg_group_ids, block_comments = extract_svg_group_ids(textcritics_entry)

    if not svg_group_ids:
        if settings.verbose:
            print(" No svgGroupIds to process")
        return

    current_main_number = extract_moldenhauer_number(textcritics_entry_id)
    relevant_svgs = find_relevant_svg_files(
        textcritics_entry_id, all_svg_files, current_main_number
    )

    if settings.verbose:
        if "SkRT" in textcritics_entry_id:
            print(f" SkRT anchor detected: {textcritics_entry_id}")
        else:
            print(f" Standard anchor: {textcritics_entry_id}")
        print(f" Relevant SVGs ({len(relevant_svgs)}): {relevant_svgs}")



    tkk_id_index = {}
    fallback_cache = {}
    try:
        tkk_id_index = _build_tkk_id_index(relevant_svgs, get_svg_data)
    except (TypeError, AttributeError, KeyError):
        # Keep tests/mocked flows compatible
        tkk_id_index = {}

    counter = 1
    entry_id_formatted = textcritics_entry_id.lower()

    for svg_group_id, block_comment in zip(svg_group_ids, block_comments):
        stats.bump("ids_seen")

        if svg_group_id in tkk_id_index:
            matching_files = tkk_id_index[svg_group_id]
        else:
            matching_files = _get_cached_matching_files(
                svg_group_id, relevant_svgs, get_svg_data, fallback_cache
            )

        new_id = f"{TKK.prefix}{entry_id_formatted}-{counter:03d}"

        updated = process_single_svg_group_id(
            svg_group_id, block_comment, matching_files,
            get_svg_data, new_id,
            settings=settings, stats=stats
        )

        if updated:
            counter += 1


def unify_tkk_ids(json_path, svg_folder,
                  settings):
    """Unify TKK IDs in JSON and SVG files."""
    if settings.verbose:
        print("--- Starting TKK ID processing ---")
        if settings.dry_run:
            print(" [DRY-RUN] No files will be written.")

    json_data, all_svg_files = load_and_validate_inputs(json_path, svg_folder)

    svg_file_cache = {}
    get_svg_data = create_svg_loader(
        svg_folder, svg_file_cache
    )

    all_textcritics_entries = (
        json_data.get('textcritics', json_data)
        if isinstance(json_data, dict)
        else json_data
    )

    stats = Stats()

    for textcritics_entry in all_textcritics_entries:
        process_textcritics_entry(
            textcritics_entry, all_svg_files, get_svg_data,
            settings=settings, stats=stats
        )

    if not settings.dry_run:
        if stats.ids_changed > 0:
            save_results(json_data, svg_file_cache, json_path)
        elif settings.verbose:
            print(" No changes detected; skipping writes.")

        display_validation_report(json_data, svg_file_cache, TKK.prefix)
    elif settings.verbose:
        print(" [DRY-RUN] Skipping write + validation report.")

    if settings.verbose:
        print(f" Summary: {stats.summary()}")

    return True


def main():
    """Main function to process tkk IDs"""

    # --- CONFIGURATION ---

    ##### fill in:
    json_path = './tests/data/textcritics.json'

    ##### fill in:
    svg_folder = './tests/img/'

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
