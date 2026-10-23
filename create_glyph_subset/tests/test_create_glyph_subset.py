"""Tests for create_glyph_subset.py"""

import hashlib
import json
import re
import shutil
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont

from create_glyph_subset import create_glyph_subset, main, parse_args
from utils.constants import (
    DEFAULT_FONT_PATH,
    FONT_FILENAME,
    LICENSE_FILENAME,
    MANIFEST_FILENAME,
    PREVIEW_FILENAME,
)


def read_manifest(out_dir: Path) -> dict:
    """Return the parsed manifest JSON of an output folder."""
    return json.loads((out_dir / MANIFEST_FILENAME).read_text(encoding="utf-8"))


class TestParseArgs:
    """Tests for the parse_args function."""

    def test_parses_input_and_out(self, tmp_path):
        """Test that the input path and output folder are parsed as paths."""
        args = parse_args(["glyphs.ts", "--out", str(tmp_path)])
        assert args.glyphs_data.name == "glyphs.ts"
        assert args.out == tmp_path

    def test_uses_bundled_font_by_default(self, tmp_path):
        """Test that the bundled Bravura is the default source font."""
        assert parse_args(["glyphs.ts", "--out", str(tmp_path)]).font == DEFAULT_FONT_PATH

    def test_bundled_font_exists(self):
        """Test that the default font path points to an existing file."""
        assert DEFAULT_FONT_PATH.is_file()

    def test_preview_is_off_by_default(self, tmp_path):
        """Test that the preview is only written on request."""
        assert parse_args(["glyphs.ts", "--out", str(tmp_path)]).preview is False
        assert parse_args(["glyphs.ts", "--out", str(tmp_path), "--preview"]).preview is True

    def test_requires_out(self, capsys):
        """Test that the output folder is required."""
        with pytest.raises(SystemExit):
            parse_args(["glyphs.ts"])
        assert "--out" in capsys.readouterr().err


class TestCreateGlyphSubset:
    """Tests for the create_glyph_subset function."""

    def test_writes_exactly_three_files(self, subset_out_dir):
        """Test that the font, manifest and license are written to the output folder."""
        assert sorted(path.name for path in subset_out_dir.iterdir()) == sorted(
            [FONT_FILENAME, MANIFEST_FILENAME, LICENSE_FILENAME]
        )

    def test_writes_text_files_with_lf_line_endings(self, subset_out_dir):
        """Test that the manifest and the license contain no CRLF line endings."""
        for filename in (MANIFEST_FILENAME, LICENSE_FILENAME):
            assert b"\r\n" not in (subset_out_dir / filename).read_bytes()

    def test_returns_codepoints_and_paths(self, glyphs_data_path, source_font_path, tmp_path,
                                          expected_codepoints):
        """Test that the codepoints and written paths are returned."""
        codepoints, paths = create_glyph_subset(glyphs_data_path, source_font_path, tmp_path)
        assert codepoints == expected_codepoints
        assert paths == [
            tmp_path / FONT_FILENAME,
            tmp_path / MANIFEST_FILENAME,
            tmp_path / LICENSE_FILENAME,
        ]

    def test_writes_preview_on_request(self, glyphs_data_path, source_font_path, tmp_path):
        """Test that the preview of the written subset is added as fourth file."""
        _, paths = create_glyph_subset(glyphs_data_path, source_font_path, tmp_path, preview=True)
        assert paths[-1] == tmp_path / PREVIEW_FILENAME
        assert "26 / 26 in cmap" in paths[-1].read_text(encoding="utf-8")
        assert len(list(tmp_path.iterdir())) == 4

    def test_creates_missing_output_folder(self, subset_out_dir):
        """Test that a missing (nested) output folder is created."""
        assert subset_out_dir.parent.name == "nested"
        assert (subset_out_dir / FONT_FILENAME).is_file()

    def test_writes_no_font_without_license(self, glyphs_data_path, source_font_path, tmp_path):
        """Test that no font is written when the OFL.txt next to the source font is missing."""
        font_path = tmp_path / "font" / source_font_path.name
        font_path.parent.mkdir()
        shutil.copyfile(source_font_path, font_path)
        out_dir = tmp_path / "out"
        with pytest.raises(OSError):
            create_glyph_subset(glyphs_data_path, font_path, out_dir)
        assert not (out_dir / FONT_FILENAME).exists()
        assert not (out_dir / MANIFEST_FILENAME).exists()

    def test_manifest_matches_font_cmap(self, subset_out_dir):
        """Test that the manifest lists exactly the codepoints mapped in the font."""
        manifest = read_manifest(subset_out_dir)
        cmap = TTFont(subset_out_dir / FONT_FILENAME).getBestCmap()
        assert manifest["codepoints"] == [f"U+{codepoint:04X}" for codepoint in sorted(cmap)]
        assert manifest["count"] == 26

    def test_manifest_hash_matches_written_font(self, subset_out_dir):
        """Test that the manifest carries the SHA-256 of the written font file as lowercase hex."""
        manifest = read_manifest(subset_out_dir)
        font_bytes = (subset_out_dir / FONT_FILENAME).read_bytes()
        assert manifest["sha256"] == hashlib.sha256(font_bytes).hexdigest()
        assert re.fullmatch(r"[0-9a-f]{64}", manifest["sha256"])

    def test_second_run_gives_same_hash(self, glyphs_data_path, source_font_path, tmp_path,
                                        subset_out_dir):
        """Test that a second run with the same input gives the same hash."""
        create_glyph_subset(glyphs_data_path, source_font_path, tmp_path)
        assert read_manifest(tmp_path)["sha256"] == read_manifest(subset_out_dir)["sha256"]

    def test_different_glyphs_give_different_hash(self, source_font_path, tmp_path,
                                                  subset_out_dir):
        """Test that a different glyph list gives a different font hash."""
        glyphs_data = tmp_path / "glyphs.ts"
        glyphs_data.write_text("FLAT: { alt: '[b]', hex: '\\uE260' },", encoding="utf-8")
        out_dir = tmp_path / "out"
        create_glyph_subset(glyphs_data, source_font_path, out_dir)
        assert read_manifest(out_dir)["sha256"] != read_manifest(subset_out_dir)["sha256"]

    def test_raises_for_codepoints_missing_in_font(self, source_font_path, tmp_path):
        """Test that nothing is written when a codepoint is missing in the source font."""
        glyphs_data = tmp_path / "glyphs.ts"
        glyphs_data.write_text("A: { hex: '\\uE260' }, B: { hex: '\\u0041' },", encoding="utf-8")
        out_dir = tmp_path / "out"
        with pytest.raises(ValueError, match="U\\+0041"):
            create_glyph_subset(glyphs_data, source_font_path, out_dir)
        assert not out_dir.exists()


class TestMain:
    """Tests for the main function."""

    def test_reports_written_files(self, glyphs_data_path, tmp_path, capsys):
        """Test that the number of codepoints and all written files, incl. preview, are reported."""
        main([str(glyphs_data_path), "--out", str(tmp_path), "--preview"])
        output = capsys.readouterr().out
        assert "26 codepoints" in output
        for filename in (FONT_FILENAME, MANIFEST_FILENAME, LICENSE_FILENAME, PREVIEW_FILENAME):
            assert filename in output

    def test_exits_on_missing_input(self, tmp_path, capsys):
        """Test that a missing input file exits with an error message."""
        with pytest.raises(SystemExit) as exc_info:
            main([str(tmp_path / "missing.ts"), "--out", str(tmp_path / "out")])
        assert exc_info.value.code == 1
        assert "Error:" in capsys.readouterr().err

    def test_exits_on_invalid_font(self, glyphs_data_path, tmp_path, capsys):
        """Test that a source font that is not a font file exits with an error message."""
        font_path = tmp_path / "invalid.woff2"
        font_path.write_bytes(b"not a font")
        with pytest.raises(SystemExit) as exc_info:
            main([str(glyphs_data_path), "--out", str(tmp_path / "out"), "--font", str(font_path)])
        assert exc_info.value.code == 1
        assert "Error:" in capsys.readouterr().err

    def test_exits_on_input_without_codepoints(self, tmp_path, capsys):
        """Test that an input without hex escapes exits with an error message."""
        glyphs_data = tmp_path / "empty.ts"
        glyphs_data.write_text("export const EMPTY = {} as const;", encoding="utf-8")
        with pytest.raises(SystemExit) as exc_info:
            main([str(glyphs_data), "--out", str(tmp_path / "out")])
        assert exc_info.value.code == 1
        assert "No \\uXXXX escapes" in capsys.readouterr().err
