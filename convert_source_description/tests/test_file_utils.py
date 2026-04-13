"""Tests for file_utils.py."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from utils.file_utils import FileUtils


class TestReadHtmlFromWordFile:
    """Tests for FileUtils.read_html_from_word_file."""

    def test_raises_when_docx_missing(self, tmp_path):
        """Raise FileNotFoundError when the .docx file does not exist."""
        file_utils = FileUtils()
        base_path = str(tmp_path / "missing_file")

        with pytest.raises(FileNotFoundError, match="File not found"):
            file_utils.read_html_from_word_file(base_path)

    def test_returns_html_when_conversion_succeeds(self, tmp_path, monkeypatch):
        """Return mammoth generated HTML on successful conversion."""
        file_utils = FileUtils()
        base_path = tmp_path / "source"
        docx_path = Path(str(base_path) + ".docx")
        docx_path.write_bytes(b"dummy-docx-content")

        def mock_convert_to_html(file_obj, style_map):
            assert file_obj is not None
            assert "small-caps => span.smallcaps" in style_map
            return SimpleNamespace(value="<p>converted html</p>")

        monkeypatch.setattr(
            "utils.file_utils.mammoth.convert_to_html", mock_convert_to_html
        )

        actual = file_utils.read_html_from_word_file(str(base_path))

        assert actual == "<p>converted html</p>"

    def test_raises_value_error_when_conversion_fails(self, tmp_path, monkeypatch):
        """Wrap mammoth ValueError with conversion context."""
        file_utils = FileUtils()
        base_path = tmp_path / "source"
        docx_path = Path(str(base_path) + ".docx")
        docx_path.write_bytes(b"dummy-docx-content")

        def mock_convert_to_html(_file_obj, style_map):
            assert "small-caps => span.smallcaps" in style_map
            raise ValueError("bad docx")

        monkeypatch.setattr(
            "utils.file_utils.mammoth.convert_to_html", mock_convert_to_html
        )

        with pytest.raises(ValueError, match="Error converting file: bad docx"):
            file_utils.read_html_from_word_file(str(base_path))


class TestWriteJson:
    """Tests for FileUtils.write_json."""

    def test_writes_json_file_with_trailing_newline(self, tmp_path):
        """Write JSON output to target path with .json extension and newline."""
        file_utils = FileUtils()
        base_path = tmp_path / "out"
        data = {"hello": "world", "value": 1}

        file_utils.write_json(data, str(base_path))

        target_file = Path(str(base_path) + ".json")
        assert target_file.exists()

        content = target_file.read_text(encoding="utf-8")
        assert content.endswith("\n")
        assert '"hello": "world"' in content

    def test_prints_error_when_io_write_fails(self, monkeypatch, capsys):
        """Print an error message if writing the output file fails."""
        file_utils = FileUtils()

        def mock_open(*_args, **_kwargs):
            raise IOError("no write permission")

        monkeypatch.setattr("builtins.open", mock_open)

        file_utils.write_json({"x": 1}, "target/path")

        captured = capsys.readouterr()
        assert "Error writing data to target/path.json." in captured.out
