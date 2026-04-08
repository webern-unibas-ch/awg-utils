#!/usr/bin/env python3
"""
Convert AWG intro JSON (HTML fragments) to Markdown.

Usage:
    python scripts/convert_intro_to_md.py \\
        src/assets/data/edition/series/1/section/5/intro.json \\
        src/assets/data/edition/series/1/section/5/intro.md

Requires: markdownify (pip install markdownify)
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from markdownify import markdownify as md
except ImportError:
    print("Error: markdownify not found. Install with: pip install markdownify", file=sys.stderr)
    sys.exit(1)


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace: collapse \xa0 and multiple newlines."""
    text = text.replace('\xa0', ' ')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def strip_angular_bindings(html: str) -> str:
    """Remove Angular event bindings like (click)="..." or (click)='...' from HTML."""
    html = re.sub(r'\s\([^)]+\)="[^"]*"', '', html)
    html = re.sub(r"\s\([^)]+\)='[^']*'", '', html)
    return html


def replace_footnote_refs(html: str) -> str:
    """Replace <sup><a id='note-ref-N' ...>N</a></sup> with @@FNREF_N@@ tokens."""
    # Match footnote anchors and replace with tokens that won't be escaped by the converter
    return re.sub(
        r"<sup>\s*<a\b[^>]*\bid=(['\"])note-ref-(\d+)\1[^>]*>[\s\S]*?</a>\s*</sup>",
        lambda m: f"@@FNREF_{m.group(2)}@@",
        html,
        flags=re.IGNORECASE
    )


def parse_block_notes(block_notes: List[str]) -> Dict[str, str]:
    """
    Parse blockNotes HTML strings into a dict of noteNum -> inner HTML content.

    Each entry looks like:
        <p id='note-N' class='...'>
            <a class='note-backlink' ...>N</a> | actual text...
        </p>
    """
    result = {}
    for note_html in block_notes:
        # Extract note number from id='note-N'
        id_match = re.search(r"\bid=(['\"])note-(\d+)\1", note_html, re.IGNORECASE)
        if not id_match:
            continue
        note_num = id_match.group(2)

        # Strip the note-backlink anchor and the pipe separator
        inner = re.sub(
            r"<a\b[^>]*class=(['\"])[^'\"]*note-backlink[^'\"]*\1[^>]*>[\s\S]*?</a>\s*\|\s*",
            "",
            note_html,
            flags=re.IGNORECASE
        )
        # Strip wrapping <p ...> and </p>
        inner = re.sub(r"^<p\b[^>]*>", "", inner, flags=re.IGNORECASE)
        inner = re.sub(r"</p>\s*$", "", inner, flags=re.IGNORECASE)
        inner = inner.strip()

        result[note_num] = inner

    return result


def html_to_md(html: str, footnotes: Dict[str, str]) -> str:
    """
    Convert HTML string to Markdown.
    
    - Angular bindings are stripped first
    - @@FNREF_N@@ tokens are converted to [^N] after conversion
    - Literal [ and ] are unescaped (markdownify over-escapes them)
    """
    if not html or not isinstance(html, str):
        return ""

    # Strip Angular bindings
    cleaned = strip_angular_bindings(html)

    # Convert HTML to Markdown
    result = md(cleaned, heading_style="atx").strip()

    # Restore footnote references (match both escaped and unescaped underscore variants)
    result = re.sub(r"@@FNREF\\?_(\d+)@@", r"[^\1]", result)

    # Unescape literal brackets that aren't part of links
    # (markdownify over-escapes [ and ] in body text)
    result = result.replace(r"\[", "[").replace(r"\]", "]")

    return result


def main():
    if len(sys.argv) < 2:
        print("Missing input JSON path.", file=sys.stderr)
        print("Example: python scripts/convert_intro_to_md.py "
              "src/assets/.../intro.json src/assets/.../intro.md", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path.with_suffix(".md")

    # Read and parse JSON
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    intro_items = data.get("intro", [])
    if not intro_items:
        print("No intro array found in input JSON.", file=sys.stderr)
        sys.exit(1)

    output_lines = []
    all_footnotes: Dict[str, str] = {}

    for intro_entry in intro_items:
        entry_id = intro_entry.get("id", "")
        blocks = intro_entry.get("content", [])

        if entry_id:
            output_lines.append(f"# Intro {entry_id}")
            output_lines.append("")

        for block in blocks:
            header = (block.get("blockHeader") or "").strip()
            fragments = block.get("blockContent", [])
            notes = block.get("blockNotes", [])

            if header:
                output_lines.append(f"## {header}")
                output_lines.append("")

            for fragment in fragments:
                # Replace footnote-ref anchors with tokens BEFORE conversion
                with_tokens = replace_footnote_refs(fragment)
                result = html_to_md(with_tokens, all_footnotes)
                if result:
                    output_lines.append(result)
                    output_lines.append("")

            # Collect footnotes from blockNotes; first occurrence wins
            for num, html in parse_block_notes(notes).items():
                if num not in all_footnotes:
                    all_footnotes[num] = html

    # Append footnotes section
    if all_footnotes:
        output_lines.append("---")
        output_lines.append("")

        # Sort footnotes numerically
        for num in sorted(all_footnotes.keys(), key=int):
            html = all_footnotes[num]
            note_text = html_to_md(html, all_footnotes)
            output_lines.append(f"[^{num}]: {note_text}")
            output_lines.append("")

    # Write output
    final_md = normalize_whitespace("\n".join(output_lines)) + "\n"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_md)

    print(f"Converted: {input_path}")
    print(f"Written:   {output_path}")


if __name__ == "__main__":
    main()
