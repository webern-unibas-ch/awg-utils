#!/usr/bin/env python3
"""
Convert AWG intro JSON (HTML block_content) to Markdown.

Usage:
    python scripts/convert_intro_to_md.py \\
        src/assets/data/edition/series/1/section/5/intro.json \\
        src/assets/data/edition/series/1/section/5/intro.md

Requires: markdownify (pip install markdownify)
"""

import re
import sys
from pathlib import Path
from typing import Dict, List

from utils.file_utils import read_json, write_md

try:
    from markdownify import markdownify as md
except ImportError:
    print(
        "Error: markdownify not found. Install with: pip install markdownify",
        file=sys.stderr,
    )
    sys.exit(1)


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace: collapse \xa0 and multiple newlines."""
    text = text.replace("\xa0", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_angular_bindings(html: str) -> str:
    """Remove Angular event bindings like (click)="..." or (click)='...' from HTML."""
    html = re.sub(r'\s\(\w+\)="[^"]*"', "", html)
    html = re.sub(r"\s\(\w+\)='[^']*'", "", html)
    return html


def replace_footnote_crossrefs(html: str) -> str:
    """Replace internal cross-reference links to other Anmerkungen with @@FNCROSSREF_N@@ tokens.

    Matches anchors like:
        <a (click)="ref.navigateToIntroFragment({..., fragmentId: 'note-18'})">18</a>
    """
    return re.sub(
        r"<a\b[^>]*fragmentId:\s*'note-(\d+)'[^>]*>\s*\d+\s*</a>",
        lambda m: f"@@FNCROSSREF_{m.group(1)}@@",
        html,
        flags=re.IGNORECASE,
    )


def replace_footnote_refs(html: str) -> str:
    """Replace <sup><a id='note-ref-N' ...>N</a></sup> with @@FNREF_N@@ tokens."""
    # Match footnote anchors and replace with tokens that won't be escaped by the converter
    return re.sub(
        r"<sup>\s*<a\b[^>]*\bid=(['\"])note-ref-(\d+)\1[^>]*>[\s\S]*?</a>\s*</sup>",
        lambda m: f"@@FNREF_{m.group(2)}@@",
        html,
        flags=re.IGNORECASE,
    )


def replace_pipes(html: str) -> str:
    """Replace literal pipe characters in text content with @@PIPE@@ tokens.

    The lookahead (?![^<>]*>) matches | outside HTML tags (not inside <...>).
    Restored as \\| after Markdown conversion so table cells aren't broken.
    """
    return re.sub(r"\|(?![^<>]*>)", "@@PIPE@@", html)


def is_small_para(line_content: str) -> bool:
    """Return True if line_content is a <p> with class 'small' but not 'list'."""
    return bool(
        re.match(
            r"<p\b(?=[^>]*\bsmall\b)(?![^>]*\blist\b)[^>]*>",
            line_content.lstrip(),
            re.IGNORECASE,
        )
    )


def combine_small_paras(block_content: List[str]) -> str:
    """Wrap consecutive small-paragraph line contents in a single blockquote element."""
    parts = []
    for line_content in block_content:
        inner = re.sub(r"^<p\b[^>]*>", "", line_content, flags=re.IGNORECASE)
        inner = re.sub(r"</p>\s*$", "", inner, flags=re.IGNORECASE)
        parts.append(f"<p>{inner.strip()}</p>")
    return f"<blockquote>{''.join(parts)}</blockquote>"


def html_to_md(html: str) -> str:
    """
    Convert HTML string to Markdown.

    - Angular bindings are stripped first
    - @@FNREF_N@@ tokens are converted to [^N] after conversion
    - Literal [ and ] are unescaped (markdownify over-escapes them)
    """
    if not html or not isinstance(html, str):
        return ""

    # Tokenize footnote references and cross-references before stripping bindings
    html = replace_footnote_refs(html)
    html = replace_footnote_crossrefs(html)

    # Tokenize literal pipe characters so they survive as escaped pipes (\|) in tables
    html = replace_pipes(html)

    # Strip Angular bindings
    cleaned = strip_angular_bindings(html)

    # Convert HTML to Markdown
    result = md(cleaned, heading_style="atx").strip()

    # Restore footnote references (match both escaped and unescaped underscore variants)
    result = re.sub(r"@@FNREF\\?_(\d+)@@", r"[^\1]", result)

    # Restore cross-references to other Anmerkungen as plain inline links
    # footnote definition anchors use #fnN format
    result = re.sub(
        r"@@FNCROSSREF\\?_(\d+)@@",
        lambda m: f"[{m.group(1)}](#fn{m.group(1)})",
        result,
    )

    # Restore literal pipe characters as escaped Markdown pipes
    result = result.replace("@@PIPE@@", r"\|")

    # Unescape literal brackets that aren't part of links
    # (markdownify over-escapes [ and ] in body text)
    result = result.replace(r"\[", "[").replace(r"\]", "]")

    return result


def append_notes_section(notes: Dict[str, str], locale: str) -> List[str]:
    """Build the footnotes section lines from a note number -> HTML dict."""
    if not notes:
        return []
    header = "Notes" if locale == "en" else "Anmerkungen"
    lines = ["---", "", f"## {header}", ""]
    for num in sorted(notes.keys(), key=int):
        lines.append(f"[^{num}]: | {html_to_md(notes[num])}")
        lines.append("")
    return lines


def strip_note_html(note_html: str) -> str:
    """Strip backlink anchor, pipe separator, and wrapping <p> tags from a note HTML string."""
    inner = re.sub(
        r"<a\b[^>]*class=(['\"])[^'\"]*note-backlink[^'\"]*\1[^>]*>[\s\S]*?</a>\s*\|\s*",
        "",
        note_html,
        flags=re.IGNORECASE,
    )
    inner = re.sub(r"^<p\b[^>]*>", "", inner, flags=re.IGNORECASE)
    inner = re.sub(r"</p>\s*$", "", inner, flags=re.IGNORECASE)
    return inner.strip()


def process_block_content(block_content: List[str]) -> List[str]:
    """Convert a list of HTML fragment strings to Markdown lines."""
    lines: List[str] = []
    i = 0
    while i < len(block_content):
        line_content = block_content[i]
        if is_small_para(line_content):
            small_group = [line_content]
            while i + 1 < len(block_content) and is_small_para(block_content[i + 1]):
                i += 1
                small_group.append(block_content[i])
            result = html_to_md(combine_small_paras(small_group))
        else:
            result = html_to_md(line_content)
        if result:
            lines.append(result)
            lines.append("")
        i += 1
    return lines


def process_block_notes(block_notes: List[str]) -> Dict[str, str]:
    """
    Parse blockNotes HTML strings into a dict of noteNum -> inner HTML content.

    Each entry looks like:
        <p id='note-N' class='...'>
            <a class='note-backlink' ...>N</a> | actual text...
        </p>
    """
    result = {}

    for block_note in block_notes:
        # Extract note number from id='note-N'
        id_match = re.search(r"\bid=(['\"])note-(\d+)\1", block_note, re.IGNORECASE)
        if not id_match:
            continue
        note_num = id_match.group(2)

        # Strip note and store inner HTML
        result[note_num] = strip_note_html(block_note)

    return result


def convert_intro_to_md(intro: Dict, intro_locale: str) -> str:
    """Convert a single intro entry to Markdown and return the content."""
    blocks = intro.get("content", [])

    md_lines: List[str] = []
    notes: Dict[str, str] = {}

    for block in blocks:
        header = (block.get("blockHeader") or "").strip()
        block_content = block.get("blockContent", [])
        block_notes = block.get("blockNotes", [])

        if header:
            md_lines.append(f"## {header}")
            md_lines.append("")

        md_lines.extend(process_block_content(block_content))

        for num, note_content in process_block_notes(block_notes).items():
            if num not in notes:
                notes[num] = note_content

    md_lines.extend(append_notes_section(notes, intro_locale))

    return normalize_whitespace("\n".join(md_lines)) + "\n"


def extract_intro_context(intro: Dict, output_path: Path) -> tuple[str, str, Path]:
    """Extract id, locale, and output path from an intro entry."""
    intro_id = intro.get("id", "")
    intro_locale = intro_id.split("-")[0] if intro_id and "-" in intro_id else intro_id
    intro_output_path = (
        output_path.with_name(f"{output_path.stem}_{intro_locale}{output_path.suffix}")
        if intro_locale
        else output_path
    )
    return intro_id, intro_locale, intro_output_path


def main():
    if len(sys.argv) < 2:
        print("Missing input JSON path.", file=sys.stderr)
        print(
            "Example: python scripts/convert_intro_to_md.py "
            "src/assets/.../intro.json src/assets/.../intro.md",
            file=sys.stderr,
        )
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = (
        Path(sys.argv[2]) if len(sys.argv) >= 3 else input_path.with_suffix(".md")
    )

    data = read_json(input_path)

    intros = data.get("intro", [])
    if not intros:
        print("No intro array found in input JSON.", file=sys.stderr)
        sys.exit(1)

    for intro in intros:
        intro_id, intro_locale, intro_output_path = extract_intro_context(
            intro, output_path
        )

        intro_md = convert_intro_to_md(intro, intro_locale)

        write_md(intro_output_path, intro_md)

        print(f"Converted: {input_path} [{intro_id}]")
        print(f"Written:   {intro_output_path}")


if __name__ == "__main__":
    main()
