"""Utility functions for subsetting, renaming and saving the Bravura font."""

from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

from utils.codepoint_utils import CodepointUtils
from utils.constants import (
    FAMILY_NAME,
    FULL_NAME,
    POSTSCRIPT_NAME,
    STYLE_NAME,
    SUBSET_NOTE,
)

NAME_ID_COPYRIGHT = 0
NAME_ID_FAMILY = 1
NAME_ID_SUBFAMILY = 2
NAME_ID_UNIQUE_ID = 3
NAME_ID_FULL_NAME = 4
NAME_ID_VERSION = 5
NAME_ID_POSTSCRIPT = 6
NAME_ID_DESCRIPTION = 10
NAME_ID_TYPOGRAPHIC_FAMILY = 16
NAME_ID_TYPOGRAPHIC_SUBFAMILY = 17


class FontUtils:
    """A class that contains utility functions for subsetting, renaming and saving fonts."""

    @staticmethod
    def load_font(font_path: Path) -> TTFont:
        """Load a font without recalculating its timestamp on save.

        Keeping ``head.modified`` from the source font makes the output reproducible,
        so regenerating the subset does not change the binary without reason.

        Args:
            font_path (Path): Path to the source font file.

        Returns:
            TTFont: The loaded font.
        """
        return TTFont(font_path, recalcTimestamp=False)

    @staticmethod
    def check_codepoints(font: TTFont, codepoints: list[int]) -> None:
        """Check that all codepoints are mapped in the font's cmap.

        Args:
            font (TTFont): The source font.
            codepoints (list[int]): The codepoints to check.

        Raises:
            ValueError: If any codepoint is missing in the font.
        """
        cmap = font.getBestCmap() or {}
        missing = [
            CodepointUtils.format_codepoint(codepoint)
            for codepoint in codepoints
            if codepoint not in cmap
        ]
        if missing:
            raise ValueError(f"Codepoints missing in source font: {', '.join(missing)}")

    @staticmethod
    def subset_font(font: TTFont, codepoints: list[int]) -> None:
        """Subset a font in place to the given codepoints.

        All name IDs are kept (the subsetter keeps only 0-6 by default), so designer,
        trademark and license entries of the source font survive.

        Args:
            font (TTFont): The font to subset.
            codepoints (list[int]): The codepoints to keep.
        """
        options = subset.Options()
        options.name_IDs = ["*"]
        subsetter = subset.Subsetter(options=options)
        subsetter.populate(unicodes=codepoints)
        subsetter.subset(font)

    @staticmethod
    def add_subset_note(copyright_text: str) -> str:
        """Insert the subset note after the copyright statement.

        Bravura's copyright entry carries the full OFL text after the first paragraph,
        so the note is placed right after the copyright statement instead of at the end.

        Args:
            copyright_text (str): The original copyright string.

        Returns:
            str: The copyright string with the subset note inserted as second paragraph.
        """
        statement, separator, rest = copyright_text.partition("\n\n")
        note = f"{SUBSET_NOTE}."
        if not separator:
            return f"{statement} {note}"
        return f"{statement}\n\n{note}\n\n{rest}"

    @staticmethod
    def rename_font(font: TTFont) -> None:
        """Rename a font in place to the AWG edition glyph names.

        Bravura is a Reserved Font Name under the OFL, so family, style, full,
        unique and PostScript names are replaced in the name table and in the CFF
        table. The copyright is kept and extended by the subset note, which is
        also set as description.

        Args:
            font (TTFont): The font to rename.
        """
        name_table = font["name"]
        version = name_table.getDebugName(NAME_ID_VERSION)
        new_names = {
            NAME_ID_FAMILY: FAMILY_NAME,
            NAME_ID_SUBFAMILY: STYLE_NAME,
            NAME_ID_UNIQUE_ID: f"{version};{POSTSCRIPT_NAME}" if version else POSTSCRIPT_NAME,
            NAME_ID_FULL_NAME: FULL_NAME,
            NAME_ID_POSTSCRIPT: POSTSCRIPT_NAME,
            NAME_ID_DESCRIPTION: SUBSET_NOTE,
        }

        platforms = {
            (record.platformID, record.platEncID, record.langID)
            for record in name_table.names
        }
        for record in name_table.names:
            if record.nameID == NAME_ID_COPYRIGHT:
                record.string = FontUtils.add_subset_note(record.toUnicode())
        for name_id, value in new_names.items():
            for platform_id, plat_enc_id, lang_id in platforms:
                name_table.setName(value, name_id, platform_id, plat_enc_id, lang_id)
        name_table.removeNames(nameID=NAME_ID_TYPOGRAPHIC_FAMILY)
        name_table.removeNames(nameID=NAME_ID_TYPOGRAPHIC_SUBFAMILY)

        if "CFF " in font:
            FontUtils.rename_cff(font)

    @staticmethod
    def rename_cff(font: TTFont) -> None:
        """Rename the font names stored in the CFF table of a font in place.

        Args:
            font (TTFont): The font with a ``CFF `` table.
        """
        cff = font["CFF "].cff
        top_dict = cff.topDictIndex[0]
        top_dict.FamilyName = FAMILY_NAME
        top_dict.FullName = FULL_NAME
        cff.fontNames[0] = POSTSCRIPT_NAME

    @staticmethod
    def save_font(font: TTFont, out_path: Path) -> None:
        """Save a font as WOFF2.

        Args:
            font (TTFont): The font to save.
            out_path (Path): Path to the output ``.woff2`` file.
        """
        font.flavor = "woff2"
        font.save(out_path)
