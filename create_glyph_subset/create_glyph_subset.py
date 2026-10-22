#!/usr/bin/env python3
"""Create a renamed WOFF2 subset of Bravura 1.380 with the glyphs of the AWG Online Edition.

Reads the codepoints from the ``hex`` values of ``EDITION_GLYPHS_DATA`` in the awg-app
file ``edition-glyphs.data.ts``, subsets Bravura to these codepoints and renames the
result to "AWG Edition Glyphs", because "Bravura" is a Reserved Font Name under the OFL.

Writes three files to the output folder:
    AWGEditionGlyphs-Regular.woff2   the font subset
    AWGEditionGlyphs.json            a manifest with the list of codepoints
    OFL.txt                          the license of the source font

Usage:
    python create_glyph_subset.py <path>/<to>/edition-glyphs.data.ts --out <output folder>

Requires: fonttools, brotli (pip install -r requirements.txt --require-hashes)
"""

import argparse
import sys
from pathlib import Path

from fontTools.ttLib import TTLibError

from utils.codepoint_utils import CodepointUtils
from utils.constants import (
    DEFAULT_FONT_PATH,
    FONT_FILENAME,
    LICENSE_FILENAME,
    MANIFEST_FILENAME,
)
from utils.file_utils import FileUtils
from utils.font_utils import FontUtils


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command line arguments.

    Args:
        argv (list[str] | None): The arguments to parse, or None to use ``sys.argv``.

    Returns:
        argparse.Namespace: The parsed arguments ``glyphs_data``, ``out`` and ``font``.
    """
    parser = argparse.ArgumentParser(
        description="Create a renamed WOFF2 subset of Bravura with the AWG edition glyphs."
    )
    parser.add_argument(
        "glyphs_data", type=Path, help="Path to edition-glyphs.data.ts of awg-app."
    )
    parser.add_argument(
        "--out", type=Path, required=True, help="Output folder for font, manifest and license."
    )
    parser.add_argument(
        "--font",
        type=Path,
        default=DEFAULT_FONT_PATH,
        help=f"Source font with {LICENSE_FILENAME} next to it (default: %(default)s).",
    )
    return parser.parse_args(argv)


def create_glyph_subset(
    glyphs_data_path: Path, font_path: Path, out_dir: Path
) -> tuple[list[int], list[Path]]:
    """Create the font subset, manifest and license in the output folder.

    Args:
        glyphs_data_path (Path): Path to ``edition-glyphs.data.ts``.
        font_path (Path): Path to the source font, with ``OFL.txt`` in the same folder.
        out_dir (Path): The output folder.

    Returns:
        tuple[list[int], list[Path]]: The subset codepoints and the paths of the written files.
    """
    codepoints = CodepointUtils.read_codepoints(glyphs_data_path)

    font = FontUtils.load_font(font_path)
    FontUtils.check_codepoints(font, codepoints)
    FontUtils.subset_font(font, codepoints)
    FontUtils.rename_font(font)

    # Copy the license first, so a missing OFL.txt never leaves an unlicensed font behind
    out_dir.mkdir(parents=True, exist_ok=True)
    license_out_path = FileUtils.copy_license(font_path.parent / LICENSE_FILENAME, out_dir)
    font_out_path = out_dir / FONT_FILENAME
    manifest_out_path = out_dir / MANIFEST_FILENAME
    FontUtils.save_font(font, font_out_path)
    FileUtils.write_manifest(manifest_out_path, codepoints)

    return codepoints, [font_out_path, manifest_out_path, license_out_path]


def main(argv: list[str] | None = None) -> None:
    """Main function to parse arguments, create the subset and report the written files.

    Args:
        argv (list[str] | None): The arguments to parse, or None to use ``sys.argv``.
    """
    args = parse_args(argv)

    try:
        codepoints, written_paths = create_glyph_subset(args.glyphs_data, args.font, args.out)
    except (OSError, ValueError, TTLibError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    print(f"Subset:    {len(codepoints)} codepoints from {args.glyphs_data}")
    for path in written_paths:
        print(f"Written:   {path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":  # pragma: no cover
    main()
