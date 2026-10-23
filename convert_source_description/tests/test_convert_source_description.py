"""Tests for convert_source_description.py."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest

from convert_source_description import (
    check_file_path,
    convert_source_description,
    main,
)
from utils.constants import DEFAULT_GLYPHS_DATA_PATH

GLYPHS = {"[a]": "glyph accid"}


class TestCheckFilePath:
    """Tests for the check_file_path function."""

    def test_accepts_docx_file(self):
        """Test that a path with .docx extension passes."""
        check_file_path("path/to/source.docx")

    def test_raises_when_file_path_has_wrong_extension(self):
        """Test that a ValueError is raised when file_path does not end with .docx."""
        with pytest.raises(ValueError, match="Expected a .docx file"):
            check_file_path("path/to/source.txt")


class TestConvertSourceDescription:
    """Tests for the convert_source_description function."""

    def _run(self, file_path="path/to/source.docx", source_list=None):
        """Run convert_source_description with all collaborators patched."""
        with (
            patch(
                "convert_source_description.FileUtils.read_html_from_word_file",
                return_value="<html></html>",
            ) as mock_read,
            patch(
                "convert_source_description.SourcesUtils.create_source_list",
                return_value=source_list or {"sources": []},
            ) as mock_sources,
            patch("convert_source_description.TextcriticsUtils") as mock_textcritics_utils,
            patch("convert_source_description.FileUtils.write_json") as mock_write,
        ):
            mock_textcritics_utils.return_value.create_textcritics.return_value = {
                "textcritics": []
            }
            convert_source_description(file_path, GLYPHS)
        return SimpleNamespace(
            read=mock_read,
            sources=mock_sources,
            textcritics_utils=mock_textcritics_utils,
            textcritics=mock_textcritics_utils.return_value.create_textcritics,
            write=mock_write,
        )

    def test_passes_glyphs_to_textcritics_utils(self):
        """Test that the given glyphs are passed to TextcriticsUtils."""
        mocks = self._run()
        mocks.textcritics_utils.assert_called_once_with(GLYPHS)

    def test_calls_create_source_list_with_parsed_soup(self):
        """Test that create_source_list is called once with a BeautifulSoup object."""
        mocks = self._run()
        mocks.sources.assert_called_once()

    def test_calls_create_textcritics_with_parsed_soup(self):
        """Test that create_textcritics is called once with a BeautifulSoup object."""
        mocks = self._run()
        mocks.textcritics.assert_called_once()

    def test_writes_source_description_json(self):
        """Test that write_json is called for the source description output file."""
        mocks = self._run(file_path="path/to/source.docx")
        paths = [c.args[1] for c in mocks.write.call_args_list]
        assert "path/to/source_source-description" in paths

    def test_writes_textcritics_json(self):
        """Test that write_json is called for the textcritics output file."""
        mocks = self._run(file_path="path/to/source.docx")
        paths = [c.args[1] for c in mocks.write.call_args_list]
        assert "path/to/source_textcritics" in paths

    def test_write_json_called_twice(self):
        """Test that write_json is called exactly twice (one per output file)."""
        mocks = self._run()
        assert mocks.write.call_count == 2

    def test_source_list_passed_to_write_json(self):
        """Test that the source_list returned by create_source_list is written."""
        source_list = {"sources": [{"id": "source_A"}]}
        mocks = self._run(source_list=source_list)
        written_data = [c.args[0] for c in mocks.write.call_args_list]
        assert source_list in written_data

    def test_raises_when_file_path_has_wrong_extension(self):
        """Test that a ValueError is raised when file_path does not end with .docx."""
        with pytest.raises(ValueError, match="Expected a .docx file"):
            convert_source_description("path/to/source.txt", GLYPHS)

    def test_file_path_passed_to_read_html(self):
        """Test that the file_path is passed directly to read_html_from_word_file."""
        mocks = self._run(file_path="my/dir/myfile.docx")
        mocks.read.assert_called_once_with("my/dir/myfile.docx")


class TestMain:
    """Tests for the main() entry point."""

    def _run_main(self, monkeypatch, argv):
        """Run main() with the given arguments and glyph reading and conversion patched."""
        monkeypatch.setattr("sys.argv", ["prog", *argv])
        with (
            patch(
                "convert_source_description.GlyphUtils.read_glyphs",
                return_value=GLYPHS,
            ) as mock_glyphs,
            patch("convert_source_description.convert_source_description") as mock_fn,
        ):
            main()
        return mock_glyphs, mock_fn

    def test_calls_convert_source_description_with_parsed_args(self, monkeypatch):
        """Test that main() passes the file_path and the read glyphs."""
        _, mock_fn = self._run_main(monkeypatch, ["my/dir/myfile.docx"])
        mock_fn.assert_called_once_with("my/dir/myfile.docx", GLYPHS)

    def test_file_path_argument_is_passed_correctly(self, monkeypatch):
        """Test that the file_path positional argument is forwarded."""
        _, mock_fn = self._run_main(monkeypatch, ["some/path/my_source.docx"])
        assert mock_fn.call_args.args[0] == "some/path/my_source.docx"

    def test_reads_glyphs_from_default_path(self, monkeypatch):
        """Test that the glyphs are read from the default awg-app path."""
        mock_glyphs, _ = self._run_main(monkeypatch, ["my_source.docx"])
        mock_glyphs.assert_called_once_with(DEFAULT_GLYPHS_DATA_PATH)

    def test_reads_glyphs_from_glyphs_data_option(self, monkeypatch):
        """Test that the --glyphs-data option is used as a Path to read the glyphs."""
        mock_glyphs, _ = self._run_main(
            monkeypatch, ["my_source.docx", "--glyphs-data", "x/glyphs.data.ts"]
        )
        mock_glyphs.assert_called_once_with(Path("x/glyphs.data.ts"))

    def test_exits_with_error_when_glyph_data_is_missing(
        self, monkeypatch, tmp_path, capsys
    ):
        """Test that a missing glyph data file exits with code 1 before converting."""
        missing_path = str(tmp_path / "missing.ts")
        monkeypatch.setattr(
            "sys.argv", ["prog", "my_source.docx", "--glyphs-data", missing_path]
        )
        with (
            patch("convert_source_description.convert_source_description") as mock_fn,
            pytest.raises(SystemExit) as exit_info,
        ):
            main()
        assert exit_info.value.code == 1
        assert "Error: Glyph data not found" in capsys.readouterr().err
        mock_fn.assert_not_called()

    def test_exits_with_error_when_file_has_wrong_extension(self, monkeypatch, capsys):
        """Test that a wrong file extension exits with code 1 before reading the glyphs."""
        monkeypatch.setattr("sys.argv", ["prog", "my_source.txt"])
        with (
            patch("convert_source_description.GlyphUtils.read_glyphs") as mock_glyphs,
            pytest.raises(SystemExit) as exit_info,
        ):
            main()
        assert exit_info.value.code == 1
        assert "Error: Expected a .docx file" in capsys.readouterr().err
        mock_glyphs.assert_not_called()

    def test_conversion_errors_are_not_caught(self, monkeypatch):
        """Test that errors during the conversion keep their traceback."""
        monkeypatch.setattr("sys.argv", ["prog", "my_source.docx"])
        with (
            patch(
                "convert_source_description.GlyphUtils.read_glyphs",
                return_value=GLYPHS,
            ),
            patch(
                "convert_source_description.convert_source_description",
                side_effect=ValueError("broken table"),
            ),
            pytest.raises(ValueError, match="broken table"),
        ):
            main()
