# pylint: disable=protected-access
"""Tests for textcritics_utils.py."""

from unittest.mock import patch

from bs4 import BeautifulSoup

from utils.replacement_utils import ReplacementUtils
from utils.textcritics_utils import TextcriticsUtils


class TestCreateTextcritics:
    """Tests for the create_textcritics function."""

    def test_create_textcritics_with_no_tables_returns_empty_dict(self):
        """Test no textcritics/corrections keys remain when there are no tables."""
        soup = BeautifulSoup(
            "<html><body><p>No tables</p></body></html>", "html.parser"
        )

        result = TextcriticsUtils().create_textcritics(soup)

        assert result == {}

    def test_create_textcritics_delegates_to_process_table_once_per_table(self):
        """Test that _process_table is called once for each table in the soup."""
        html = """
            <table><tr><td>Takt</td></tr></table>
            <table><tr><td>Takt</td></tr></table>
        """
        soup = BeautifulSoup(html, "html.parser")
        utils = TextcriticsUtils()

        with patch.object(
            utils, "_process_table", wraps=utils._process_table
        ) as mock_process:
            utils.create_textcritics(soup)

        assert mock_process.call_count == 2

    def test_create_textcritics_removes_empty_textcritics_key(self):
        """Test that the textcritics key is removed when _process_table adds nothing to it."""
        soup = BeautifulSoup("<table><tr><td>T</td></tr></table>", "html.parser")
        utils = TextcriticsUtils()

        def add_to_corrections(textcritics_list, _table, _table_index):
            textcritics_list["corrections"].append({"dummy": True})

        with patch.object(utils, "_process_table", side_effect=add_to_corrections):
            result = utils.create_textcritics(soup)

        assert "textcritics" not in result
        assert "corrections" in result

    def test_create_textcritics_removes_empty_corrections_key(self):
        """Test that the corrections key is removed when _process_table adds nothing to it."""
        soup = BeautifulSoup("<table><tr><td>T</td></tr></table>", "html.parser")
        utils = TextcriticsUtils()

        def add_to_textcritics(textcritics_list, _table, _table_index):
            textcritics_list["textcritics"].append({"dummy": True})

        with patch.object(utils, "_process_table", side_effect=add_to_textcritics):
            result = utils.create_textcritics(soup)

        assert "corrections" not in result
        assert "textcritics" in result


class TestProcessTable:
    """Tests for the _process_table helper method."""

    def test_process_table_delegates_row_parsing_to_process_table_rows(self):
        """Test that row parsing is delegated to _process_table_rows."""
        html = """
            <table>
                <tr>
                    <td>Takt</td><td>System</td><td>Position</td><td>Kommentar</td>
                </tr>
                <tr><td>4</td><td>S4</td><td>Pos 4</td><td>Comment 4.</td></tr>
            </table>
        """
        table = BeautifulSoup(html, "html.parser").find("table")
        textcritics_list = {"textcritics": [], "corrections": []}
        utils = TextcriticsUtils()

        with patch.object(
            utils,
            "_process_table_rows",
            wraps=utils._process_table_rows,
        ) as mock_rows:
            utils._process_table(textcritics_list, table, table_index=0)

        mock_rows.assert_called_once()

    def test_process_table_delegates_corrections_to_process_corrections(self):
        """Test that Korrektur table is delegated to _process_corrections."""
        html = """
            <table>
                <tr>
                    <td>Takt</td><td>System</td><td>Position</td><td>Korrektur</td>
                </tr>
                <tr><td>7</td><td>S7</td><td>Pos 7</td><td>Comment 7.</td></tr>
            </table>
        """
        table = BeautifulSoup(html, "html.parser").find("table")
        textcritics_list = {"textcritics": [], "corrections": []}
        utils = TextcriticsUtils()

        with patch.object(
            utils,
            "_process_corrections",
            wraps=utils._process_corrections,
        ) as mock_corrections:
            utils._process_table(textcritics_list, table, table_index=0)

        mock_corrections.assert_called_once()
        assert not textcritics_list["textcritics"]
        assert len(textcritics_list["corrections"]) == 1

    def test_process_table_appends_to_textcritics_for_tkk_table(self):
        """Test that a tkk table is appended to textcritics."""
        html = """
            <table>
                <tr>
                    <td>Takt</td><td>System</td><td>Position</td><td>Kommentar</td>
                </tr>
                <tr><td>4</td><td>S4</td><td>Pos 4</td><td>Comment 4.</td></tr>
            </table>
        """
        table = BeautifulSoup(html, "html.parser").find("table")
        textcritics_list = {"textcritics": [], "corrections": []}

        TextcriticsUtils()._process_table(textcritics_list, table, table_index=0)

        assert len(textcritics_list["textcritics"]) == 1
        assert not textcritics_list["corrections"]

    def test_process_table_result_has_default_textcritics_structure(self):
        """Test that the appended textcritics entry has the expected top-level keys."""
        html = """
            <table>
                <tr>
                    <td>Takt</td><td>System</td><td>Position</td><td>Kommentar</td>
                </tr>
                <tr><td>4</td><td>S4</td><td>Pos 4</td><td>Comment 4.</td></tr>
            </table>
        """
        table = BeautifulSoup(html, "html.parser").find("table")
        textcritics_list = {"textcritics": [], "corrections": []}

        TextcriticsUtils()._process_table(textcritics_list, table, table_index=0)

        result = textcritics_list["textcritics"][0]
        assert "id" in result
        assert "label" in result
        assert "evaluations" in result
        assert "linkBoxes" in result
        assert "commentary" in result
        assert "comments" in result["commentary"]

    def test_skips_table_with_no_rows(self, capsys):
        """Test that a table with no <tr> rows is skipped with a warning."""
        table = BeautifulSoup("<table></table>", "html.parser").find("table")
        textcritics_list = {"textcritics": [], "corrections": []}

        TextcriticsUtils()._process_table(textcritics_list, table, table_index=0)

        assert not textcritics_list["textcritics"]
        assert not textcritics_list["corrections"]
        assert (
            "--- Potential error? Table 1 has no rows or no header columns, skipped."
            in capsys.readouterr().out
        )

    def test_skips_table_whose_first_row_has_no_td(self, capsys):
        """Test that a table whose first row contains only <th> cells is skipped."""
        html = "<table><tr><th>Takt</th><th>System</th></tr></table>"
        table = BeautifulSoup(html, "html.parser").find("table")
        textcritics_list = {"textcritics": [], "corrections": []}

        TextcriticsUtils()._process_table(textcritics_list, table, table_index=0)

        assert not textcritics_list["textcritics"]
        assert not textcritics_list["corrections"]
        assert (
            "--- Potential error? Table 1 has no rows or no header columns, skipped."
            in capsys.readouterr().out
        )


class TestProcessCorrections:
    """Tests for the _process_corrections helper method."""

    def _make_textcritics(self):
        """Return a minimal textcritics dict with linkBoxes and svgGroupId."""
        return {
            "id": "",
            "label": "",
            "evaluations": [],
            "commentary": {
                "preamble": "",
                "comments": [
                    {
                        "blockHeader": "B",
                        "blockComments": [
                            {
                                "svgGroupId": "TODO",
                                "measure": "1",
                                "system": "S1",
                                "position": "p",
                                "comment": "c",
                            }
                        ],
                    }
                ],
            },
            "linkBoxes": [],
        }

    def test_process_corrections_removes_link_boxes(self):
        """Test that _process_corrections removes the linkBoxes key in place."""
        textcritics = self._make_textcritics()
        TextcriticsUtils()._process_corrections(textcritics)
        assert "linkBoxes" not in textcritics

    def test_process_corrections_removes_svg_group_id_from_block_comments(self):
        """Test that _process_corrections removes svgGroupId from each blockComment in place."""
        textcritics = self._make_textcritics()
        TextcriticsUtils()._process_corrections(textcritics)
        assert (
            "svgGroupId"
            not in textcritics["commentary"]["comments"][0]["blockComments"][0]
        )


class TestProcessTableRows:
    """Tests for the _process_table_rows helper method."""

    def test_process_table_rows_uses_default_block_when_no_colspan_header(self):
        """Test that comments are appended to default empty-header block without colspan row."""
        html = """
            <table>
                <tr>
                    <td>Takt</td><td>System</td><td>Position</td><td>Kommentar</td>
                </tr>
                <tr><td>4</td><td>S4</td><td>Pos 4</td><td>Comment 4.</td></tr>
            </table>
        """
        rows_in_table = BeautifulSoup(html, "html.parser").find("table").find_all("tr")
        textcritics = {
            "commentary": {"comments": [{"blockHeader": "", "blockComments": []}]}
        }
        utils = TextcriticsUtils()

        with patch.object(
            utils,
            "_process_comment",
            return_value={
                "measure": "4",
                "system": "S4",
                "position": "Pos 4",
                "comment": "Comment 4.",
            },
        ) as mock_process_comment:
            result = utils._process_table_rows(
                textcritics, rows_in_table, block_index=0
            )

        comments = result["commentary"]["comments"]
        assert len(comments) == 1
        assert comments[0]["blockHeader"] == ""
        assert len(comments[0]["blockComments"]) == 1
        assert comments[0]["blockComments"][0]["svgGroupId"] == "g-tkk-1"
        mock_process_comment.assert_called_once()

    def test_process_table_rows_removes_default_empty_block_on_first_colspan(self):
        """Test that default empty-header block is removed when first data row is a block header."""
        html = """
            <table>
                <tr>
                    <td>Takt</td><td>System</td><td>Position</td><td>Kommentar</td>
                </tr>
                <tr><td colspan="4"><p>Header Block</p></td></tr>
                <tr><td>3</td><td>S3</td><td>Pos 3</td><td>Comment 3.</td></tr>
            </table>
        """
        rows_in_table = BeautifulSoup(html, "html.parser").find("table").find_all("tr")
        textcritics = {
            "commentary": {"comments": [{"blockHeader": "", "blockComments": []}]}
        }
        utils = TextcriticsUtils()

        with patch.object(
            utils,
            "_process_comment",
            return_value={
                "measure": "3",
                "system": "S3",
                "position": "Pos 3",
                "comment": "Comment 3.",
            },
        ) as mock_process_comment:
            result = utils._process_table_rows(
                textcritics, rows_in_table, block_index=0
            )

        blocks = result["commentary"]["comments"]
        assert len(blocks) == 1
        assert blocks[0]["blockHeader"] == "Header Block"
        assert len(blocks[0]["blockComments"]) == 1
        assert blocks[0]["blockComments"][0]["svgGroupId"] == "g-tkk-1"
        mock_process_comment.assert_called_once()

    def test_process_table_rows_skips_comment_rows_for_negative_block_index(self):
        """Test that comment rows are ignored when block index is negative."""
        row_html = """
            <tr><td>10</td><td>S4</td><td>left</td><td>Comment.</td></tr>
        """
        rows_in_table = [None, BeautifulSoup(row_html, "html.parser").find("tr")]
        textcritics = {"commentary": {"comments": []}}

        result = TextcriticsUtils()._process_table_rows(
            textcritics,
            rows_in_table,
            block_index=-1,
        )

        assert not result["commentary"]["comments"]

    def test_process_table_rows_assigns_incrementing_svg_group_ids(self):
        """Test that svgGroupId values increment for each data-row comment."""
        html = """
            <table>
                <tr>
                    <td>Takt</td><td>System</td><td>Position</td><td>Kommentar</td>
                </tr>
                <tr><td>5</td><td>S5</td><td>Pos 5</td><td>Comment 5.</td></tr>
                <tr><td>6</td><td>S6</td><td>Pos 6</td><td>Comment 6.</td></tr>
            </table>
        """
        rows_in_table = BeautifulSoup(html, "html.parser").find("table").find_all("tr")
        textcritics = {
            "commentary": {"comments": [{"blockHeader": "", "blockComments": []}]}
        }
        utils = TextcriticsUtils()

        def _make_comment(*_args, **_kwargs):
            return {"measure": "m", "system": "s", "position": "p", "comment": "c"}

        with patch.object(
            utils, "_process_comment", side_effect=_make_comment
        ) as mock_process_comment:
            result = utils._process_table_rows(
                textcritics, rows_in_table, block_index=0
            )

        block_comments = result["commentary"]["comments"][0]["blockComments"]
        assert block_comments[0]["svgGroupId"] == "g-tkk-1"
        assert block_comments[1]["svgGroupId"] == "g-tkk-2"
        assert mock_process_comment.call_count == 2

    def test_skips_empty_rows(self):
        """Test that rows with no <td> elements (e.g. empty or <th>-only rows) are skipped."""
        html = """
            <table>
                <tr>
                    <td>Takt</td><td>System</td><td>Position</td><td>Kommentar</td>
                </tr>
                <tr></tr>
                <tr><td>4</td><td>S4</td><td>Pos 4</td><td>Comment 4.</td></tr>
            </table>
        """
        rows_in_table = BeautifulSoup(html, "html.parser").find("table").find_all("tr")
        textcritics = {
            "commentary": {"comments": [{"blockHeader": "", "blockComments": []}]}
        }
        utils = TextcriticsUtils()

        with patch.object(
            utils,
            "_process_comment",
            return_value={
                "measure": "4",
                "system": "S4",
                "position": "Pos 4",
                "comment": "Comment 4.",
            },
        ) as mock_process_comment:
            utils._process_table_rows(textcritics, rows_in_table, block_index=0)

        mock_process_comment.assert_called_once()

    def test_skips_rows_with_fewer_than_four_columns(self, capsys):
        """Test that data rows with fewer than 4 <td> cells are skipped with a warning."""
        html = """
            <table>
                <tr>
                    <td>Takt</td><td>System</td><td>Position</td><td>Kommentar</td>
                </tr>
                <tr><td>4</td><td>S4</td></tr>
                <tr><td>5</td><td>S5</td><td>Pos 5</td><td>Comment 5.</td></tr>
            </table>
        """
        rows_in_table = BeautifulSoup(html, "html.parser").find("table").find_all("tr")
        textcritics = {
            "commentary": {"comments": [{"blockHeader": "", "blockComments": []}]}
        }
        utils = TextcriticsUtils()

        with patch.object(
            utils,
            "_process_comment",
            return_value={
                "measure": "5",
                "system": "S5",
                "position": "Pos 5",
                "comment": "Comment 5.",
            },
        ) as mock_process_comment:
            utils._process_table_rows(textcritics, rows_in_table, block_index=0)

        mock_process_comment.assert_called_once()
        assert (
            "--- Potential error? Table row with fewer than 4 columns skipped:"
            in capsys.readouterr().out
        )


class TestProcessComment:
    """Tests for the _process_comment helper method."""

    def test_process_comment_extracts_measure_system_and_position(self):
        """Test base field extraction from a 4-column row."""
        row_html = """
            <tr>
                <td>10</td><td>S4</td><td>left</td>
                <td><p>plain comment</p></td>
            </tr>
        """
        columns = BeautifulSoup(row_html, "html.parser").find_all("td")

        comment = TextcriticsUtils()._process_comment(columns)

        assert comment["measure"] == "10"
        assert comment["system"] == "S4"
        assert comment["position"] == "left"
        assert comment["comment"] == "plain comment"

    def test_process_comment_triggers_escape_curly_brackets(self):
        """Test that escape_curly_brackets is triggered in _process_comment."""
        row_html = """
            <tr>
                <td>10</td><td>S4</td><td>left</td>
                <td><p>{x}</p></td>
            </tr>
        """
        columns = BeautifulSoup(row_html, "html.parser").find_all("td")

        with patch.object(
            ReplacementUtils,
            "escape_curly_brackets",
            wraps=ReplacementUtils.escape_curly_brackets,
        ) as mock_escape:
            TextcriticsUtils()._process_comment(columns)

        mock_escape.assert_called_once()

    def test_process_comment_triggers_replace_glyphs(self):
        """Test that replace_glyphs is triggered in _process_comment."""
        row_html = """
            <tr>
                <td>10</td><td>S4</td><td>left</td>
                <td><p>[a]</p></td>
            </tr>
        """
        columns = BeautifulSoup(row_html, "html.parser").find_all("td")

        with patch.object(
            ReplacementUtils,
            "replace_glyphs",
            wraps=ReplacementUtils.replace_glyphs,
        ) as mock_replace_glyphs:
            TextcriticsUtils()._process_comment(columns)

        mock_replace_glyphs.assert_called_once()

    def test_process_comment_triggers_add_report_fragment_links(self):
        """Test that add_report_fragment_links is triggered in _process_comment."""
        row_html = """
            <tr>
                <td>10</td><td>S4</td><td>left</td>
                <td><p><strong>A</strong></p></td>
            </tr>
        """
        columns = BeautifulSoup(row_html, "html.parser").find_all("td")

        with patch.object(
            ReplacementUtils,
            "add_report_fragment_links",
            wraps=ReplacementUtils.add_report_fragment_links,
        ) as mock_add_links:
            TextcriticsUtils()._process_comment(columns)

        mock_add_links.assert_called_once()
