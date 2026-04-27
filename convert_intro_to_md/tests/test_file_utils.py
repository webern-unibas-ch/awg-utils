"""Tests for utils/file_utils.py"""

import json
import pytest

from utils.file_utils import FileUtils


class TestReadJson:
    """Tests for the read_json function."""

    def test_reads_valid_json(self, tmp_path):
        """Test that a valid JSON file is read and returned as a dict."""
        data = {"key": "value", "number": 42}
        file = tmp_path / "test.json"
        file.write_text(json.dumps(data), encoding="utf-8")
        assert FileUtils.read_json(file) == data

    def test_reads_nested_json(self, tmp_path):
        """Test that a nested JSON structure is parsed correctly."""
        data = {"outer": {"inner": [1, 2, 3]}}
        file = tmp_path / "nested.json"
        file.write_text(json.dumps(data), encoding="utf-8")
        assert FileUtils.read_json(file) == data

    def test_exits_on_missing_file(self, tmp_path):
        """Test that sys.exit is called when the file does not exist."""
        missing = tmp_path / "missing.json"
        with pytest.raises(SystemExit):
            FileUtils.read_json(missing)

    def test_exits_on_invalid_json(self, tmp_path):
        """Test that sys.exit is called when the file contains invalid JSON."""
        file = tmp_path / "bad.json"
        file.write_text("not valid json {", encoding="utf-8")
        with pytest.raises(SystemExit):
            FileUtils.read_json(file)

    def test_prints_error_on_missing_file(self, tmp_path, capsys):
        """Test that an error message is printed to stderr when the file is missing."""
        missing = tmp_path / "missing.json"
        with pytest.raises(SystemExit):
            FileUtils.read_json(missing)
        assert "Error reading" in capsys.readouterr().err

    def test_prints_error_on_invalid_json(self, tmp_path, capsys):
        """Test that an error message is printed to stderr for invalid JSON."""
        file = tmp_path / "bad.json"
        file.write_text("{invalid}", encoding="utf-8")
        with pytest.raises(SystemExit):
            FileUtils.read_json(file)
        assert "Error reading" in capsys.readouterr().err


class TestWriteMd:
    """Tests for the write_md function."""

    def test_writes_content_to_file(self, tmp_path):
        """Test that the given content is written to the specified file."""
        file = tmp_path / "output.md"
        FileUtils.write_md(file, "# Hello")
        assert file.read_text(encoding="utf-8") == "# Hello"

    def test_creates_parent_directories(self, tmp_path):
        """Test that missing parent directories are created automatically."""
        file = tmp_path / "a" / "b" / "output.md"
        FileUtils.write_md(file, "content")
        assert file.exists()

    def test_overwrites_existing_file(self, tmp_path):
        """Test that writing to an existing file overwrites its content."""
        file = tmp_path / "output.md"
        file.write_text("old content", encoding="utf-8")
        FileUtils.write_md(file, "new content")
        assert file.read_text(encoding="utf-8") == "new content"

    def test_writes_empty_string(self, tmp_path):
        """Test that an empty string can be written to a file."""
        file = tmp_path / "empty.md"
        FileUtils.write_md(file, "")
        assert file.read_text(encoding="utf-8") == ""

    def test_writes_multiline_content(self, tmp_path):
        """Test that multiline Markdown content is written correctly."""
        content = "# Title\n\nParagraph one.\n\nParagraph two.\n"
        file = tmp_path / "multi.md"
        FileUtils.write_md(file, content)
        assert file.read_text(encoding="utf-8") == content
