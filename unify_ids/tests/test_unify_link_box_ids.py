"""Tests for unify_link_box_ids.py."""

from unittest.mock import call
import pytest

from unify_link_box_ids import (
    log_report_message,
    main,
    process_single_link_box,
    process_textcritics_entry,
    unify_link_box_ids,
)


class TestLogReportMessage:
    """Tests for log_report_message."""

    def test_log_report_message_appends_to_list_and_prints(self, capsys):
        """Test that the formatted message is appended and printed when a message list is provided"""
        messages = []
        log_report_message(messages, "error", "some_code", "M143_TF1", "something went wrong")

        expected = " [ERROR] M143_TF1: something went wrong [some_code]"
        assert messages == [expected]
        assert expected in capsys.readouterr().out

    def test_log_report_message_with_none_list_only_prints(self, capsys):
        """Test that the message is printed but not stored when message_list is None."""
        log_report_message(None, "warning", "my_code", "M99", "a warning")

        expected = " [WARNING] M99: a warning [my_code]"
        assert expected in capsys.readouterr().out


@pytest.fixture(name="sample_svg_data")
def fixture_sample_svg_data():
    """Return mutable SVG data."""
    return {"content": "<svg-content>"}


class TestProcessSingleLinkBox:
    """Tests for process_single_link_box."""

    def test_process_single_link_box_with_success(
        self, mocker, capsys, sample_svg_data
    ):
        """Test successful processing of a link box with valid inputs."""
        link_box = {"svgGroupId": "g6407", "linkTo": {"sheetId": "M317_Sk2"}}
        parent_link_boxes = [link_box]
        get_svg_data = mocker.Mock(return_value=sample_svg_data)
        mocker.patch(
            "unify_link_box_ids.find_matching_svg_files_by_class",
            return_value=["sheet.svg"],
        )
        update_mock = mocker.patch(
            "unify_link_box_ids.update_svg_id_by_class",
            return_value=("<updated-svg-content>", None),
        )

        result = process_single_link_box(
            "g6407", parent_link_boxes, "op25_WE", ["sheet.svg"], get_svg_data
        )

        expected_new_id = "awg-lb-op25_wex-to-m317_sk2"  # 'x' suffix: no -NvonM- pattern in 'sheet.svg'

        assert result is True
        assert link_box not in parent_link_boxes  # original removed
        assert any(lb.get("svgGroupId") == expected_new_id for lb in parent_link_boxes)
        get_svg_data.assert_called_once_with("sheet.svg")
        update_mock.assert_called_once_with(
            "<svg-content>",
            "g6407",
            expected_new_id,
            "link-box",
        )
        new_link_box = next(lb for lb in parent_link_boxes if lb.get("svgGroupId") == expected_new_id)
        assert new_link_box["linkTo"] == {"sheetId": "M317_Sk2"}
        assert sample_svg_data["content"] == "<updated-svg-content>"

        output = capsys.readouterr().out
        assert f"[JSON] Changing 'g6407' -> '{expected_new_id}'" in output
        assert f"[SVG]  Changing 'g6407' -> '{expected_new_id}' in sheet.svg" in output

    def test_process_single_link_box_with_no_matching_files(self, mocker, capsys):
        """Test processing of a link box when no matching SVG files are found."""
        link_box = {"svgGroupId": "g6407", "linkTo": {"sheetId": "M317_Sk2"}}
        parent_link_boxes = [link_box]
        get_svg_data = mocker.Mock()
        mocker.patch(
            "unify_link_box_ids.find_matching_svg_files_by_class",
            return_value=[],
        )

        result = process_single_link_box("g6407", parent_link_boxes, "op25_WE", [], get_svg_data)

        assert result is False
        assert link_box in parent_link_boxes  # unchanged: nothing removed when no matches
        get_svg_data.assert_not_called()
        output = capsys.readouterr().out
        assert "not found in any relevant SVG files" in output

    def test_process_single_link_box_with_multiple_matching_files(self, mocker, capsys):
        """Test processing of a link box when multiple SVG files match — JSON is expanded."""
        link_box = {"svgGroupId": "g6407", "linkTo": {"sheetId": "M317_Sk2"}}
        parent_link_boxes = [link_box]
        svg_data_a = {"content": "<svg/>"}
        svg_data_b = {"content": "<svg/>"}
        get_svg_data = mocker.Mock(side_effect=[svg_data_a, svg_data_b])
        mocker.patch(
            "unify_link_box_ids.find_matching_svg_files_by_class",
            return_value=["a.svg", "b.svg"],
        )
        mocker.patch(
            "unify_link_box_ids.update_svg_id_by_class",
            return_value=("<updated/>", None),
        )

        result = process_single_link_box(
            "g6407",
            parent_link_boxes,
            "op25_WE",
            ["a.svg", "b.svg"],
            get_svg_data,
        )

        assert result is True
        assert link_box not in parent_link_boxes  # original removed
        assert len(parent_link_boxes) == 2  # two new entries added
        get_svg_data.assert_any_call("a.svg")
        get_svg_data.assert_any_call("b.svg")
        output = capsys.readouterr().out
        assert "MULTIPLE SVGs reference 'g6407'" in output
        assert "Expanding JSON entry to 2 distinct IDs" in output

    def test_process_single_link_box_with_missing_sheet_id(self, mocker, capsys):
        """Test processing of a link box when the linked sheetId is missing."""
        link_box = {"svgGroupId": "g6407", "linkTo": {}}
        parent_link_boxes = [link_box]
        get_svg_data = mocker.Mock()
        mocker.patch(
            "unify_link_box_ids.find_matching_svg_files_by_class",
            return_value=["sheet.svg"],
        )

        result = process_single_link_box(
            "g6407", parent_link_boxes, "op25_WE", ["sheet.svg"], get_svg_data
        )

        assert result is False
        assert link_box["svgGroupId"] == "g6407"
        get_svg_data.assert_not_called()
        output = capsys.readouterr().out
        assert "No target sheetId found in linkBox with svgGroupId 'g6407'" in output

    def test_process_single_link_box_with_svg_update_error(
        self, mocker, capsys, sample_svg_data
    ):
        """Test processing of a link box when the SVG update fails."""
        link_box = {"svgGroupId": "g6407", "linkTo": {"sheetId": "M317_Sk2"}}
        parent_link_boxes = [link_box]
        get_svg_data = mocker.Mock(return_value=sample_svg_data)
        mocker.patch(
            "unify_link_box_ids.find_matching_svg_files_by_class",
            return_value=["sheet.svg"],
        )
        mocker.patch(
            "unify_link_box_ids.update_svg_id_by_class",
            return_value=("<svg-content>", "Could not update id"),
        )

        result = process_single_link_box(
            "g6407", parent_link_boxes, "op25_WE", ["sheet.svg"], get_svg_data
        )

        expected_new_id = "awg-lb-op25_wex-to-m317_sk2"  # 'x' suffix: no -NvonM- pattern in 'sheet.svg'

        assert result is False
        # Original link_box is removed; a new entry with the updated ID is appended
        assert link_box not in parent_link_boxes
        assert any(lb.get("svgGroupId") == expected_new_id for lb in parent_link_boxes)
        output = capsys.readouterr().out
        assert "WARNING: Could not update id" in output

    def test_process_single_link_box_warns_on_self_reference(self, mocker, capsys, sample_svg_data):
        """When entry_id equals target_sheet_id, a self-reference warning is logged."""
        # Use a -1von1- filename so extract_id_suffix returns "" → entry_id = textcritics_entry_id
        # Set sheetId equal to textcritics_entry_id so entry_id == target_sheet_id
        link_box = {"svgGroupId": "g6407", "linkTo": {"sheetId": "M143_TF1"}}
        parent_link_boxes = [link_box]
        messages = []
        get_svg_data = mocker.Mock(return_value=sample_svg_data)
        mocker.patch(
            "unify_link_box_ids.find_matching_svg_files_by_class",
            return_value=["sheet-1von1-.svg"],
        )
        mocker.patch(
            "unify_link_box_ids.update_svg_id_by_class",
            return_value=("<updated/>", None),
        )

        result = process_single_link_box(
            "g6407", parent_link_boxes, "M143_TF1", ["sheet-1von1-.svg"], get_svg_data,
            messages=messages,
        )

        assert result is True
        assert any("self_reference" in m for m in messages)
        output = capsys.readouterr().out
        assert "Self-reference detected" in output


class TestProcessTextcriticsEntry:
    """Tests for process_textcritics_entry."""

    def test_process_textcritics_entry_returns_for_non_dict(self, mocker):
        """Test that process_textcritics_entry returns early when entry is not a dict."""
        extract_number_mock = mocker.patch(
            "unify_link_box_ids.extract_moldenhauer_number"
        )

        process_textcritics_entry("not-a-dict", ["a.svg"], mocker.Mock())

        extract_number_mock.assert_not_called()

    def test_process_textcritics_entry_returns_when_id_missing(self, mocker):
        """Test that process_textcritics_entry returns early when 'id' is missing."""
        extract_number_mock = mocker.patch(
            "unify_link_box_ids.extract_moldenhauer_number"
        )

        process_textcritics_entry({}, ["a.svg"], mocker.Mock())

        extract_number_mock.assert_not_called()

    def test_process_textcritics_entry_success_basic(self, mocker, capsys):
        """Test successful processing of a textcritics entry with valid link boxes."""
        entry = {"id": "M143_TF1"}
        all_svg_files = ["test1.svg", "test2.svg"]
        link_boxes = [
            {"svgGroupId": "g1", "linkTo": {"sheetId": "M143_Sk1"}},
            {"svgGroupId": "g2", "linkTo": {"sheetId": "M143_Sk2"}},
        ]
        get_svg_data = mocker.Mock()

        extract_number_mock = mocker.patch(
            "unify_link_box_ids.extract_moldenhauer_number", return_value="143"
        )
        find_relevant_mock = mocker.patch(
            "unify_link_box_ids.find_relevant_svg_files",
            return_value=["test1.svg", "test2.svg"],
        )
        extract_link_boxes_mock = mocker.patch(
            "unify_link_box_ids.extract_link_boxes", return_value=link_boxes
        )
        process_single_mock = mocker.patch(
            "unify_link_box_ids.process_single_link_box", return_value=True
        )

        process_textcritics_entry(entry, all_svg_files, get_svg_data)

        extract_number_mock.assert_called_once_with("M143_TF1")
        find_relevant_mock.assert_called_once_with("M143_TF1", all_svg_files, "143")
        extract_link_boxes_mock.assert_called_once_with(entry)
        assert process_single_mock.call_args_list == [
            call("g1", link_boxes, "M143_TF1", ["test1.svg", "test2.svg"], get_svg_data, None),
            call("g2", link_boxes, "M143_TF1", ["test1.svg", "test2.svg"], get_svg_data, None),
        ]

        output = capsys.readouterr().out
        assert "Processing textcritics entry ID: M143_TF1" in output
        assert "Standard anchor: M143_TF1" in output
        assert "Relevant SVGs (2): ['test1.svg', 'test2.svg']" in output
        assert "Found 2 linkBox(es)" in output

    def test_process_textcritics_entry_prints_skrt_anchor_and_no_link_boxes(
        self, mocker, capsys
    ):
        """Test that process_textcritics_entry identifies SkRT anchor and handles no link boxes."""
        entry = {"id": "M143_SkRT1"}
        all_svg_files = ["test1.svg"]
        get_svg_data = mocker.Mock()

        mocker.patch(
            "unify_link_box_ids.extract_moldenhauer_number", return_value="143"
        )
        mocker.patch(
            "unify_link_box_ids.find_relevant_svg_files",
            return_value=["test1.svg"],
        )
        mocker.patch("unify_link_box_ids.extract_link_boxes", return_value=[])
        find_matching_mock = mocker.patch(
            "unify_link_box_ids.find_matching_svg_files_by_class"
        )
        process_single_mock = mocker.patch(
            "unify_link_box_ids.process_single_link_box"
        )

        process_textcritics_entry(entry, all_svg_files, get_svg_data)

        find_matching_mock.assert_not_called()
        process_single_mock.assert_not_called()
        output = capsys.readouterr().out
        assert "No linkBoxes to process" in output

    def test_process_textcritics_entry_prints_skrt_anchor_with_link_boxes(
        self, mocker, capsys
    ):
        """Test that 'SkRT anchor detected' is printed when the entry has link boxes."""
        entry = {"id": "M143_SkRT1"}
        all_svg_files = ["test1.svg"]
        link_boxes = [{"svgGroupId": "g1", "linkTo": {"sheetId": "M143_Sk1"}}]
        get_svg_data = mocker.Mock()

        mocker.patch("unify_link_box_ids.extract_moldenhauer_number", return_value="143")
        mocker.patch("unify_link_box_ids.find_relevant_svg_files", return_value=["test1.svg"])
        mocker.patch("unify_link_box_ids.extract_link_boxes", return_value=link_boxes)
        mocker.patch("unify_link_box_ids.process_single_link_box", return_value=True)

        process_textcritics_entry(entry, all_svg_files, get_svg_data)

        output = capsys.readouterr().out
        assert "SkRT anchor detected: M143_SkRT1" in output
        self, mocker, capsys


    def test_process_single_link_box_with_missing_svg_group_id(self, mocker, capsys):
        """Test that process_textcritics_entry skips link boxes that are missing svgGroupId."""
        entry = {"id": "M143_TF1"}
        all_svg_files = ["sheet.svg"]
        link_boxes = [
            {"linkTo": {"sheetId": "M143_Sk1"}},
            {"svgGroupId": "g2", "linkTo": {"sheetId": "M143_Sk2"}},
        ]
        get_svg_data = mocker.Mock()

        mocker.patch(
            "unify_link_box_ids.extract_moldenhauer_number", return_value="143"
        )
        mocker.patch(
            "unify_link_box_ids.find_relevant_svg_files",
            return_value=["sheet.svg"],
        )
        mocker.patch("unify_link_box_ids.extract_link_boxes", return_value=link_boxes)
        process_single_mock = mocker.patch(
            "unify_link_box_ids.process_single_link_box", return_value=True
        )

        process_textcritics_entry(entry, all_svg_files, get_svg_data)

        process_single_mock.assert_called_once_with(
            "g2", link_boxes, "M143_TF1", ["sheet.svg"], get_svg_data, None
        )
        output = capsys.readouterr().out
        assert "[ERROR]" in output
        assert "linkBox without svgGroupId" in output


class TestUnifyLinkBoxIds:
    """Tests for unify_link_box_ids."""

    def test_unify_link_box_ids_processes_dict_textcritics(self, mocker, capsys):
        """
        Test that unify_link_box_ids processes textcritics when root is a dict
        with 'textcritics' key.
        """
        json_data = {"textcritics": [{"id": "A"}, {"id": "B"}]}
        all_svg_files = ["A.svg", "B.svg"]
        get_svg_data = mocker.Mock(name="get_svg_data")
        captured = {}

        load_mock = mocker.patch(
            "unify_link_box_ids.load_and_validate_inputs",
            return_value=(json_data, all_svg_files),
        )

        def _fake_create_svg_loader(svg_folder, svg_file_cache):
            captured["svg_folder"] = svg_folder
            captured["svg_file_cache"] = svg_file_cache
            return get_svg_data

        create_loader_mock = mocker.patch(
            "unify_link_box_ids.create_svg_loader",
            side_effect=_fake_create_svg_loader,
        )
        process_entry_mock = mocker.patch("unify_link_box_ids.process_textcritics_entry")
        save_results_mock = mocker.patch("unify_link_box_ids.save_results")

        result = unify_link_box_ids("textcritics.json", "img/")

        assert result is True
        load_mock.assert_called_once_with("textcritics.json", "img/")
        create_loader_mock.assert_called_once()
        assert captured["svg_folder"] == "img/"
        assert captured["svg_file_cache"] == {}
        assert process_entry_mock.call_count == 2
        first_call_args = process_entry_mock.call_args_list[0][0]
        second_call_args = process_entry_mock.call_args_list[1][0]
        assert first_call_args[0] == {"id": "A"}
        assert first_call_args[1] == all_svg_files
        assert first_call_args[2] is get_svg_data
        assert second_call_args[0] == {"id": "B"}
        save_results_mock.assert_called_once_with(
            json_data, captured["svg_file_cache"], "textcritics.json"
        )

        output = capsys.readouterr().out
        assert "--- Starting Link Box ID processing ---" in output
        assert "--- Link Box ID processing completed ---" in output

    def test_unify_link_box_ids_processes_list_root(self, mocker):
        """
        Test that unify_link_box_ids processes textcritics when root is a list
        (legacy format).
        """
        json_data = [{"id": "A"}, {"id": "B"}]
        all_svg_files = ["A.svg"]
        get_svg_data = mocker.Mock(name="get_svg_data")

        mocker.patch(
            "unify_link_box_ids.load_and_validate_inputs",
            return_value=(json_data, all_svg_files),
        )
        mocker.patch(
            "unify_link_box_ids.create_svg_loader",
            return_value=get_svg_data,
        )
        process_entry_mock = mocker.patch("unify_link_box_ids.process_textcritics_entry")
        save_results_mock = mocker.patch("unify_link_box_ids.save_results")

        result = unify_link_box_ids("textcritics.json", "img/")

        assert result is True
        assert process_entry_mock.call_count == 2
        assert process_entry_mock.call_args_list[0][0][0] == {"id": "A"}
        assert process_entry_mock.call_args_list[1][0][0] == {"id": "B"}
        save_results_mock.assert_called_once()
        assert save_results_mock.call_args[0][0] == json_data
        assert save_results_mock.call_args[0][2] == "textcritics.json"


class TestMain:
    """Tests for main."""

    def test_main_success_path(self, mocker, capsys):
        """Test the successful execution path of main."""
        process_mock = mocker.patch(
            "unify_link_box_ids.unify_link_box_ids", return_value=True
        )
        exit_mock = mocker.patch("sys.exit")

        main()

        process_mock.assert_called_once_with(
            "./tests/data/textcritics.json", "./tests/img/"
        )
        exit_mock.assert_not_called()
        output = capsys.readouterr().out
        assert "Finished!" in output

    def test_main_with_warnings(self, mocker, capsys):
        """Test main when unify_link_box_ids returns False indicating warnings."""
        process_mock = mocker.patch(
            "unify_link_box_ids.unify_link_box_ids", return_value=False
        )
        exit_mock = mocker.patch("sys.exit")

        main()

        process_mock.assert_called_once_with(
            "./tests/data/textcritics.json", "./tests/img/"
        )
        exit_mock.assert_not_called()
        output = capsys.readouterr().out
        assert "Processing completed with warnings." in output

    def test_main_handles_file_not_found(self, mocker, capsys):
        """Test main when unify_link_box_ids raises FileNotFoundError."""
        mocker.patch(
            "unify_link_box_ids.unify_link_box_ids",
            side_effect=FileNotFoundError("missing-file"),
        )
        exit_mock = mocker.patch("sys.exit")

        main()

        exit_mock.assert_called_once_with(1)
        output = capsys.readouterr().out
        assert "Error: missing-file" in output

    def test_main_handles_unexpected_error(self, mocker, capsys):
        """Test main when unify_link_box_ids raises an unexpected exception."""
        mocker.patch(
            "unify_link_box_ids.unify_link_box_ids",
            side_effect=ValueError("bad-config"),
        )
        exit_mock = mocker.patch("sys.exit")

        main()

        exit_mock.assert_called_once_with(1)
        output = capsys.readouterr().out
        assert "Unexpected error: bad-config" in output
