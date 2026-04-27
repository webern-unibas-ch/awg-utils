"""Tests for convert_intro_to_md.py"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from convert_intro_to_md import convert_intro_to_md, get_intro_context, main
from utils.processing_utils import ProcessingUtils


class TestConvertIntroToMd:
    """Tests for the convert_intro_to_md function."""

    def test_returns_string(self):
        """Test that the function returns a string."""
        assert isinstance(convert_intro_to_md({"content": []}, "en"), str)

    def test_empty_content_returns_newline(self):
        """Test that an intro with no content blocks produces a bare newline."""
        assert convert_intro_to_md({"content": []}, "en") == "\n"

    def test_block_header_included(self):
        """Test that a block header is rendered as an h2."""
        intro = {
            "content": [
                {"blockHeader": "My Section", "blockContent": [], "blockNotes": []}
            ]
        }
        result = convert_intro_to_md(intro, "en")
        assert "## My Section" in result

    def test_null_block_header_skipped(self):
        """Test that a null blockHeader does not produce an h2 line."""
        intro = {
            "content": [{"blockHeader": None, "blockContent": [], "blockNotes": []}]
        }
        result = convert_intro_to_md(intro, "en")
        assert "##" not in result

    def test_empty_block_header_skipped(self):
        """Test that a whitespace-only blockHeader does not produce an h2 line."""
        intro = {
            "content": [{"blockHeader": "   ", "blockContent": [], "blockNotes": []}]
        }
        result = convert_intro_to_md(intro, "en")
        assert "##" not in result

    def test_delegates_process_block_content(self):
        """Test that blockContent is routed through ProcessingUtils.process_block_content."""
        intro = {"content": [{"blockContent": ["<p>Text</p>"], "blockNotes": []}]}
        with patch.object(
            ProcessingUtils, "process_block_content", return_value=[]
        ) as mock:
            convert_intro_to_md(intro, "en")
        mock.assert_called_once_with(["<p>Text</p>"])

    def test_delegates_process_block_notes(self):
        """Test that blockNotes are routed through ProcessingUtils.process_block_notes."""
        intro = {
            "content": [{"blockContent": [], "blockNotes": ["<p id='note-1'>N</p>"]}]
        }
        with patch.object(
            ProcessingUtils, "process_block_notes", return_value=None
        ) as mock:
            convert_intro_to_md(intro, "en")
        mock.assert_called_once()
        assert mock.call_args[0][0] == ["<p id='note-1'>N</p>"]

    def test_delegates_process_end_notes(self):
        """Test that collected notes are passed through ProcessingUtils.process_end_notes."""
        intro = {"content": [{"blockContent": [], "blockNotes": []}]}
        with patch.object(
            ProcessingUtils, "process_end_notes", return_value=[]
        ) as mock:
            convert_intro_to_md(intro, "de")
        mock.assert_called_once_with({}, "de")

    def test_delegates_assemble_markdown(self):
        """Test that the final lines are assembled via ProcessingUtils.assemble_markdown."""
        intro = {"content": []}
        with patch.object(
            ProcessingUtils, "assemble_markdown", return_value="done\n"
        ) as mock:
            result = convert_intro_to_md(intro, "en")
        mock.assert_called_once()
        assert result == "done\n"

    def test_missing_content_key(self):
        """Test that an intro dict without a 'content' key is handled gracefully."""
        assert convert_intro_to_md({}, "en") == "\n"


class TestGetIntroContext:
    """Tests for the get_intro_context function."""

    def test_extracts_locale_from_id(self):
        """Test that the locale is the part before the first hyphen in the id."""
        _, locale, _ = get_intro_context({"id": "de-awg-I-5"}, Path("intro.md"))
        assert locale == "de"

    def test_extracts_id(self):
        """Test that the intro id is returned unchanged."""
        intro_id, _, _ = get_intro_context({"id": "en-awg-I-5"}, Path("intro.md"))
        assert intro_id == "en-awg-I-5"

    def test_output_path_includes_locale(self):
        """Test that the output path has the locale appended before the extension."""
        _, _, out = get_intro_context({"id": "de-awg-I-5"}, Path("intro.md"))
        assert out.name == "intro_de.md"

    def test_id_without_hyphen_uses_id_as_locale(self):
        """Test that an id with no hyphen is used directly as the locale."""
        _, locale, _ = get_intro_context({"id": "en"}, Path("intro.md"))
        assert locale == "en"

    def test_missing_id_falls_back_to_base_path(self):
        """Test that a missing id leaves the output path unchanged."""
        _, _, out = get_intro_context({}, Path("intro.md"))
        assert out.name == "intro.md"

    def test_preserves_output_directory(self):
        """Test that the output file is placed in the same directory as the base path."""
        _, _, out = get_intro_context({"id": "de-awg-I-5"}, Path("out/intro.md"))
        assert out.parent == Path("out")


class TestMain:
    """Tests for the main function."""

    def test_exits_with_no_args(self):
        """Test that main exits with code 1 when no arguments are provided."""
        with patch("sys.argv", ["prog"]):
            with pytest.raises(SystemExit) as exc:
                main()
        assert exc.value.code == 1

    def test_prints_usage_hint_to_stderr(self, capsys):
        """Test that a usage example is printed to stderr when no args are given."""
        with patch("sys.argv", ["prog"]):
            with pytest.raises(SystemExit):
                main()
        assert "Example:" in capsys.readouterr().err

    def test_exits_when_no_intro_array(self, tmp_path):
        """Test that main exits when the JSON has no 'intro' key."""
        f = tmp_path / "intro.json"
        f.write_text(json.dumps({}), encoding="utf-8")
        with patch("sys.argv", ["prog", str(f)]):
            with pytest.raises(SystemExit) as exc:
                main()
        assert exc.value.code == 1

    def test_prints_no_intro_error_to_stderr(self, tmp_path, capsys):
        """Test that an error message is printed when the intro array is missing."""
        f = tmp_path / "intro.json"
        f.write_text(json.dumps({}), encoding="utf-8")
        with patch("sys.argv", ["prog", str(f)]):
            with pytest.raises(SystemExit):
                main()
        assert "No intro array" in capsys.readouterr().err

    def test_writes_output_file(self, tmp_path):
        """Test that main writes an output file for a given intro."""
        data = {"intro": [{"id": "de-awg-I-5", "content": []}]}
        f = tmp_path / "intro.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        with patch("sys.argv", ["prog", str(f)]):
            main()
        assert (tmp_path / "intro_de.md").exists()

    def test_writes_one_file_per_locale(self, tmp_path):
        """Test that main writes separate files for each locale in the intro array."""
        data = {
            "intro": [
                {"id": "de-awg-I-5", "content": []},
                {"id": "en-awg-I-5", "content": []},
            ]
        }
        f = tmp_path / "intro.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        with patch("sys.argv", ["prog", str(f)]):
            main()
        assert (tmp_path / "intro_de.md").exists()
        assert (tmp_path / "intro_en.md").exists()

    def test_prints_converted_and_written_lines(self, tmp_path, capsys):
        """Test that main prints 'Converted' and 'Written' lines for each intro."""
        data = {"intro": [{"id": "de-awg-I-5", "content": []}]}
        f = tmp_path / "intro.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        with patch("sys.argv", ["prog", str(f)]):
            main()
        out = capsys.readouterr().out
        assert "Converted:" in out
        assert "Written:" in out
