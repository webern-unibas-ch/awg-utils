"""Tests for convert_source_description.py."""

import pytest
from unittest.mock import patch

from convert_source_description import convert_source_description, main


class TestConvertSourceDescription:
    """Tests for the convert_source_description function."""

    def _run(self, file_path="path/to/source.docx"):
        """Run convert_source_description with all collaborators patched."""
        source_list = {"sources": []}
        textcritics = {"textcritics": []}

        with (
            patch(
                "convert_source_description.FileUtils.read_html_from_word_file",
                return_value="<html></html>",
            ),
            patch(
                "convert_source_description.SourcesUtils.create_source_list",
                return_value=source_list,
            ) as mock_sources,
            patch(
                "convert_source_description.TextcriticsUtils.create_textcritics",
                return_value=textcritics,
            ) as mock_textcritics,
            patch(
                "convert_source_description.FileUtils.write_json"
            ) as mock_write,
        ):
            convert_source_description(file_path)
            return mock_sources, mock_textcritics, mock_write

    def test_calls_create_source_list_with_parsed_soup(self):
        """Test that create_source_list is called once with a BeautifulSoup object."""
        mock_sources, _, _ = self._run()
        mock_sources.assert_called_once()

    def test_calls_create_textcritics_with_parsed_soup(self):
        """Test that create_textcritics is called once with a BeautifulSoup object."""
        _, mock_textcritics, _ = self._run()
        mock_textcritics.assert_called_once()

    def test_writes_source_description_json(self):
        """Test that write_json is called for the source description output file."""
        _, _, mock_write = self._run(file_path="path/to/source.docx")
        paths = [c.args[1] for c in mock_write.call_args_list]
        assert "path/to/source_source-description" in paths

    def test_writes_textcritics_json(self):
        """Test that write_json is called for the textcritics output file."""
        _, _, mock_write = self._run(file_path="path/to/source.docx")
        paths = [c.args[1] for c in mock_write.call_args_list]
        assert "path/to/source_textcritics" in paths

    def test_write_json_called_twice(self):
        """Test that write_json is called exactly twice (one per output file)."""
        _, _, mock_write = self._run()
        assert mock_write.call_count == 2

    def test_source_list_passed_to_write_json(self):
        """Test that the source_list returned by create_source_list is written."""
        source_list = {"sources": [{"id": "source_A"}]}
        with (
            patch(
                "convert_source_description.FileUtils.read_html_from_word_file",
                return_value="<html></html>",
            ),
            patch(
                "convert_source_description.SourcesUtils.create_source_list",
                return_value=source_list,
            ),
            patch(
                "convert_source_description.TextcriticsUtils.create_textcritics",
                return_value={},
            ),
            patch(
                "convert_source_description.FileUtils.write_json"
            ) as mock_write,
        ):
            convert_source_description("path/to/source.docx")
        written_data = [c.args[0] for c in mock_write.call_args_list]
        assert source_list in written_data

    def test_raises_when_file_path_has_wrong_extension(self):
        """Test that a ValueError is raised when file_path does not end with .docx."""
        with pytest.raises(ValueError, match="Expected a .docx file"):
            convert_source_description("path/to/source.txt")

    def test_file_path_passed_to_read_html(self):
        """Test that the file_path is passed directly to read_html_from_word_file."""
        with (
            patch(
                "convert_source_description.FileUtils.read_html_from_word_file",
                return_value="<html></html>",
            ) as mock_read,
            patch(
                "convert_source_description.SourcesUtils.create_source_list",
                return_value={},
            ),
            patch(
                "convert_source_description.TextcriticsUtils.create_textcritics",
                return_value={},
            ),
            patch("convert_source_description.FileUtils.write_json"),
        ):
            convert_source_description("my/dir/myfile.docx")
        mock_read.assert_called_once_with("my/dir/myfile.docx")


class TestMain:
    """Tests for the main() entry point."""

    def test_calls_convert_source_description_with_parsed_args(self, monkeypatch):
        """Test that main() passes the file_path arg to convert_source_description."""
        monkeypatch.setattr("sys.argv", ["prog", "my/dir/myfile.docx"])
        with patch(
            "convert_source_description.convert_source_description"
        ) as mock_fn:
            main()
        mock_fn.assert_called_once_with("my/dir/myfile.docx")

    def test_file_path_argument_is_passed_correctly(self, monkeypatch):
        """Test that the file_path positional argument is forwarded."""
        monkeypatch.setattr("sys.argv", ["prog", "some/path/my_source.docx"])
        with patch(
            "convert_source_description.convert_source_description"
        ) as mock_fn:
            main()
        assert mock_fn.call_args.args[0] == "some/path/my_source.docx"
