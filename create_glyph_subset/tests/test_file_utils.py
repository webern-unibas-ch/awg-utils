"""Tests for utils/file_utils.py"""

import json

from utils.constants import (
    DEFAULT_FONT_DIR,
    FAMILY_NAME,
    FONT_FILENAME,
    LICENSE_FILENAME,
    MANIFEST_FILENAME,
    POSTSCRIPT_NAME,
    SUBSET_NOTE,
)
from utils.file_utils import FileUtils


class TestCreateManifest:
    """Tests for the create_manifest function."""

    def test_contains_font_metadata(self):
        """Test that the manifest names the font, file, license and source."""
        manifest = FileUtils.create_manifest([0xE260])
        assert manifest["family"] == FAMILY_NAME
        assert manifest["style"] == "Regular"
        assert manifest["postscriptName"] == POSTSCRIPT_NAME
        assert manifest["file"] == FONT_FILENAME
        assert manifest["license"] == LICENSE_FILENAME
        assert manifest["source"] == "Bravura 1.380"
        assert manifest["note"] == SUBSET_NOTE

    def test_lists_codepoints_in_unicode_notation(self):
        """Test that the codepoints are listed as U+XXXX in the given order with their count."""
        manifest = FileUtils.create_manifest([0xE260, 0xE52F])
        assert manifest["codepoints"] == ["U+E260", "U+E52F"]
        assert manifest["count"] == 2


class TestWriteManifest:
    """Tests for the write_manifest function."""

    def test_writes_manifest_as_json(self, tmp_path):
        """Test that the written JSON equals the created manifest."""
        manifest_path = tmp_path / MANIFEST_FILENAME
        FileUtils.write_manifest(manifest_path, [0xE260, 0xE262])
        content = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert content == FileUtils.create_manifest([0xE260, 0xE262])

    def test_uses_four_space_indent_and_trailing_newline(self, tmp_path):
        """Test that the JSON follows the repo formatting (4-space indent, final newline)."""
        manifest_path = tmp_path / MANIFEST_FILENAME
        FileUtils.write_manifest(manifest_path, [0xE260])
        text = manifest_path.read_text(encoding="utf-8")
        assert text.startswith('{\n    "family"')
        assert text.endswith("}\n")

    def test_writes_lf_line_endings(self, tmp_path):
        """Test that the manifest is written with LF, not CRLF, on every platform."""
        manifest_path = tmp_path / MANIFEST_FILENAME
        FileUtils.write_manifest(manifest_path, [0xE260, 0xE262])
        assert b"\r\n" not in manifest_path.read_bytes()


class TestCopyLicense:
    """Tests for the copy_license function."""

    def test_copies_license_text(self, tmp_path):
        """Test that the OFL text is copied unchanged into the output folder."""
        source = DEFAULT_FONT_DIR / LICENSE_FILENAME
        copied = FileUtils.copy_license(source, tmp_path)
        assert copied == tmp_path / LICENSE_FILENAME
        assert copied.read_text(encoding="utf-8") == source.read_text(encoding="utf-8")

    def test_normalizes_crlf_to_lf(self, tmp_path):
        """Test that a license checked out with CRLF line endings is copied with LF."""
        source = tmp_path / "src" / LICENSE_FILENAME
        source.parent.mkdir()
        source.write_bytes(b"Copyright line\r\n\r\nLicense text\r\n")
        copied = FileUtils.copy_license(source, tmp_path)
        assert copied.read_bytes() == b"Copyright line\n\nLicense text\n"

    def test_bundled_license_names_reserved_font_name(self):
        """Test that the bundled license is the Bravura OFL with its Reserved Font Name."""
        text = (DEFAULT_FONT_DIR / LICENSE_FILENAME).read_text(encoding="utf-8")
        assert 'Reserved Font Name "Bravura"' in text
        assert "SIL Open Font License, Version 1.1" in text
