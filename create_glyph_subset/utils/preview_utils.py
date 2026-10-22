"""Utility functions for writing an HTML preview of the AWG edition glyph subset."""

import base64
import html
import re
from dataclasses import dataclass, field
from pathlib import Path
from string import Template

from fontTools.ttLib import TTFont

from utils.codepoint_utils import (
    HEX_VALUE_PATTERN,
    UNICODE_ESCAPE_PATTERN,
    CodepointUtils,
)

SECTION_PATTERN = re.compile(r"^\s*/\*\*\s+([A-Z][A-Z ]*?)\s+/\s*$", re.MULTILINE)
ENTRY_PATTERN = re.compile(r"(\w+):\s*\{([^{}]*)\}")
ALT_VALUE_PATTERN = re.compile(r"\balt:\s*(['\"`])(.*?)\1")
TEMPLATE_PATH = Path(__file__).resolve().parent / "preview_template.html"
DEFAULT_GROUP_TITLE = "Glyphs"
SAMPLE_GROUP_TITLE = "Dynamics"
SAMPLE_SIZE = 6


@dataclass
class GlyphEntry:
    """A single entry of ``EDITION_GLYPHS_DATA``."""

    key: str
    alt: str
    text: str
    codepoints: list[int]


@dataclass
class GlyphGroup:
    """A section of ``EDITION_GLYPHS_DATA`` with its entries."""

    title: str
    entries: list[GlyphEntry] = field(default_factory=list)


class PreviewUtils:
    """A class that contains utility functions for writing an HTML preview of the glyph subset."""

    @staticmethod
    def parse_glyph_groups(content: str) -> list[GlyphGroup]:
        """Parse the glyph entries of a TypeScript source, grouped by their section comments.

        Entries before the first section comment are collected in a group named ``Glyphs``.
        Entries without a ``hex`` value are skipped.

        Args:
            content (str): The TypeScript source text.

        Returns:
            list[GlyphGroup]: The groups with their entries, in source order.
        """
        tokens = [(match.start(), match) for match in SECTION_PATTERN.finditer(content)]
        tokens += [(match.start(), match) for match in ENTRY_PATTERN.finditer(content)]

        groups: list[GlyphGroup] = []
        for _, match in sorted(tokens, key=lambda token: token[0]):
            if match.re is SECTION_PATTERN:
                groups.append(GlyphGroup(match.group(1).title()))
                continue
            hex_match = HEX_VALUE_PATTERN.search(match.group(2))
            if not hex_match:
                continue
            alt_match = ALT_VALUE_PATTERN.search(match.group(2))
            hex_value = hex_match.group(2)
            if not groups:
                groups.append(GlyphGroup(DEFAULT_GROUP_TITLE))
            groups[-1].entries.append(
                GlyphEntry(
                    key=match.group(1),
                    alt=alt_match.group(2) if alt_match else "",
                    text=UNICODE_ESCAPE_PATTERN.sub(
                        lambda escape: chr(int(escape.group(1), 16)), hex_value
                    ),
                    codepoints=[
                        int(escape, 16) for escape in UNICODE_ESCAPE_PATTERN.findall(hex_value)
                    ],
                )
            )
        return [group for group in groups if group.entries]

    @staticmethod
    def render_preview(groups: list[GlyphGroup], font_path: Path) -> str:
        """Render the HTML preview of all glyph entries with the embedded font.

        Args:
            groups (list[GlyphGroup]): The glyph groups to show.
            font_path (Path): Path to the WOFF2 subset, embedded as data URI.

        Returns:
            str: The self-contained HTML page.
        """
        font = TTFont(font_path)
        cmap = font.getBestCmap() or {}
        name_table = font["name"]

        names = {
            name_id: html.escape(name_table.getDebugName(name_id) or "")
            for name_id in (1, 2, 5, 6, 10)
        }
        all_entries = [entry for group in groups for entry in group.entries]
        codepoints = {codepoint for entry in all_entries for codepoint in entry.codepoints}
        found = sum(codepoint in cmap for codepoint in codepoints)
        sample_entries = next(
            (group.entries for group in groups if group.title == SAMPLE_GROUP_TITLE), all_entries
        )

        return Template(TEMPLATE_PATH.read_text(encoding="utf-8")).substitute(
            font_base64=base64.b64encode(font_path.read_bytes()).decode("ascii"),
            family=names[1],
            style=names[2],
            version=names[5],
            postscript_name=names[6],
            note=names[10],
            font_file=html.escape(font_path.name),
            font_size=f"{font_path.stat().st_size:,}",
            status_class="status" if found == len(codepoints) else "status bad",
            found=found,
            total=len(codepoints),
            sections="".join(PreviewUtils._render_group(group, cmap) for group in groups),
            sample=" ".join(
                f'<span class="g">{html.escape(entry.text)}</span>'
                for entry in sample_entries[:SAMPLE_SIZE]
            ),
        )

    @staticmethod
    def write_preview(preview_path: Path, glyphs_data_path: Path, font_path: Path) -> None:
        """Write the HTML preview for a glyph data file and its font subset.

        Args:
            preview_path (Path): Path to the output HTML file.
            glyphs_data_path (Path): Path to ``edition-glyphs.data.ts``.
            font_path (Path): Path to the WOFF2 subset.
        """
        groups = PreviewUtils.parse_glyph_groups(glyphs_data_path.read_text(encoding="utf-8"))
        preview_path.write_text(PreviewUtils.render_preview(groups, font_path), encoding="utf-8")

    @staticmethod
    def _render_group(group: GlyphGroup, cmap: dict[int, str]) -> str:
        """Render a glyph group as a section with one card per entry.

        Args:
            group (GlyphGroup): The glyph group to render.
            cmap (dict[int, str]): The cmap of the font, to mark entries with missing glyphs.

        Returns:
            str: The HTML of the section.
        """
        cards = []
        for entry in group.entries:
            missing = any(codepoint not in cmap for codepoint in entry.codepoints)
            codes = " + ".join(CodepointUtils.format_codepoint(cp) for cp in entry.codepoints)
            cards.append(
                f'<figure class="card{" missing" if missing else ""}">'
                f'<div class="glyph">{html.escape(entry.text)}</div>'
                f'<figcaption><code class="key">{html.escape(entry.key)}</code>'
                f'<span class="meta">{html.escape(entry.alt)} · {codes}</span></figcaption>'
                "</figure>"
            )
        return (
            f"<section><h2>{html.escape(group.title)}</h2>"
            f'<div class="grid">{"".join(cards)}</div></section>'
        )
