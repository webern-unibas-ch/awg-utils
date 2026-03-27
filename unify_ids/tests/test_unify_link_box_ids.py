"""Tests for unify_link_box_ids.py."""

from io import StringIO
import unittest
from unittest.mock import call, patch, MagicMock
import pytest

from unify_link_box_ids import (
    main,
    process_single_link_box,
    process_textcritics_entry,
    unify_link_box_ids,
)
from utils.logger_utils import Logger


@pytest.mark.unit
class TestProcessSingleLinkBox(unittest.TestCase):  # pylint: disable=too-many-instance-attributes
    """Tests for process_single_link_box."""

    def setUp(self):
        self.textcritics_entry_id = "M143_TF1"
        self.svg_group_id = "g6407"
        self.svg_data = {"svg_root": MagicMock()}
        self.link_box = {
            "svgGroupId": self.svg_group_id,
            "linkTo": {"sheetId": "M317_Sk2"},
        }
        self.parent_link_boxes = [self.link_box]

        self.mock_get_svg_data = MagicMock(return_value=self.svg_data)

        self.update_svg_patcher = patch(
            "unify_link_box_ids.update_svg_id_by_class",
            return_value=(True, None),
        )
        self.mock_update_svg = self.update_svg_patcher.start()

        self._stdout = StringIO()
        self.stdout_patcher = patch("sys.stdout", self._stdout)
        self.stdout_patcher.start()

    def tearDown(self):
        self.update_svg_patcher.stop()
        self.stdout_patcher.stop()

    def test_process_single_link_box_with_success(self):
        """Test successful processing of a link box with valid inputs."""
        expected_new_id = "awg-lb-m143_tf1-to-m317_sk2"

        logger = Logger(verbose=True)
        result = process_single_link_box(
            self.textcritics_entry_id,
            self.svg_group_id,
            self.parent_link_boxes,
            ["sheet-1von1-final.svg"],
            self.mock_get_svg_data,
            logger,
        )

        self.assertTrue(result)
        self.assertNotIn(self.link_box, self.parent_link_boxes)
        self.assertTrue(
            any(
                lb.get("svgGroupId") == expected_new_id for lb in self.parent_link_boxes
            )
        )
        self.mock_get_svg_data.assert_called_once_with("sheet-1von1-final.svg")
        self.mock_update_svg.assert_called_once_with(
            self.svg_data,
            self.svg_group_id,
            expected_new_id,
            "link-box",
        )
        new_link_box = next(
            lb
            for lb in self.parent_link_boxes
            if lb.get("svgGroupId") == expected_new_id
        )
        self.assertEqual(new_link_box["linkTo"], {"sheetId": "M317_Sk2"})
        output = self._stdout.getvalue()
        self.assertIn(
            f"[JSON] Changing '{self.svg_group_id}' -> '{expected_new_id}'", output
        )
        self.assertIn(
            f"[SVG]  Changing '{self.svg_group_id}' -> '{expected_new_id}'"
            f" in sheet-1von1-final.svg",
            output,
        )

    def test_process_single_link_box_with_no_matching_files(self):
        """Test processing of a link box when no matching SVG files are found."""
        logger = Logger(verbose=True)
        result = process_single_link_box(
            self.textcritics_entry_id,
            self.svg_group_id,
            self.parent_link_boxes,
            [],
            self.mock_get_svg_data,
            logger,
        )

        self.assertFalse(result)
        self.assertIn(self.link_box, self.parent_link_boxes)
        self.mock_get_svg_data.assert_not_called()
        self.assertIn("not found in any relevant SVG files", self._stdout.getvalue())

    def test_process_single_link_box_with_multiple_matching_files(self):
        """Test processing of a link box when multiple SVG files match — JSON is expanded."""
        svg_data_a = {"svg_root": MagicMock()}
        svg_data_b = {"svg_root": MagicMock()}
        self.mock_get_svg_data.side_effect = [svg_data_a, svg_data_b]
        self.mock_update_svg.return_value = (True, None)

        logger = Logger(verbose=True)
        result = process_single_link_box(
            self.textcritics_entry_id,
            self.svg_group_id,
            self.parent_link_boxes,
            ["a.svg", "b.svg"],
            self.mock_get_svg_data,
            logger,
        )

        self.assertTrue(result)
        self.assertNotIn(self.link_box, self.parent_link_boxes)
        self.assertEqual(len(self.parent_link_boxes), 2)
        self.mock_get_svg_data.assert_any_call("a.svg")
        self.mock_get_svg_data.assert_any_call("b.svg")
        output = self._stdout.getvalue()
        self.assertIn(f"MULTIPLE SVGs reference '{self.svg_group_id}'", output)
        self.assertIn("Expanding JSON entry to 2 distinct IDs", output)

    def test_process_single_link_box_with_missing_sheet_id(self):
        """Test processing of a link box when the linked sheetId is missing."""
        self.link_box["linkTo"] = {}

        logger = Logger(verbose=True)
        result = process_single_link_box(
            self.textcritics_entry_id,
            self.svg_group_id,
            self.parent_link_boxes,
            ["sheet-1von1-final.svg"],
            self.mock_get_svg_data,
            logger,
        )

        self.assertFalse(result)
        self.assertEqual(self.link_box["svgGroupId"], self.svg_group_id)
        self.mock_get_svg_data.assert_not_called()
        self.assertIn(
            f"No target sheetId found in linkBox with svgGroupId '{self.svg_group_id}'",
            self._stdout.getvalue(),
        )

    def test_process_single_link_box_with_svg_update_error(self):
        """Test processing of a link box when the SVG update fails."""
        self.mock_update_svg.return_value = (False, "Could not update id")
        expected_new_id = "awg-lb-m143_tf1-to-m317_sk2"

        logger = Logger(verbose=True)
        result = process_single_link_box(
            self.textcritics_entry_id,
            self.svg_group_id,
            self.parent_link_boxes,
            ["sheet-1von1-final.svg"],
            self.mock_get_svg_data,
            logger,
        )

        self.assertFalse(result)
        self.assertNotIn(self.link_box, self.parent_link_boxes)
        self.assertTrue(
            any(
                lb.get("svgGroupId") == expected_new_id for lb in self.parent_link_boxes
            )
        )
        self.assertIn("WARNING: Could not update id", self._stdout.getvalue())

    def test_process_single_link_box_warns_on_self_reference(self):
        """When entry_id equals target_sheet_id, a self-reference warning is logged."""
        self.link_box["linkTo"] = {"sheetId": self.textcritics_entry_id}
        self.mock_update_svg.return_value = (True, None)

        logger = Logger(verbose=True)
        result = process_single_link_box(
            self.textcritics_entry_id,
            self.svg_group_id,
            self.parent_link_boxes,
            ["sheet-1von1-final.svg"],
            self.mock_get_svg_data,
            logger,
        )

        self.assertTrue(result)
        self.assertTrue(any("self_reference" in msg for msg in logger.messages))
        self.assertIn("Self-reference detected", self._stdout.getvalue())


@pytest.mark.unit
class TestProcessTextcriticsEntry(unittest.TestCase):  # pylint: disable=too-many-instance-attributes
    """Tests for process_textcritics_entry."""

    def setUp(self):
        self.entry = {"id": "M143_TF1"}
        self.all_svg_files = ["test1.svg", "test2.svg"]
        self.mock_get_svg_data = MagicMock()

        self.extract_number_patcher = patch(
            "unify_link_box_ids.extract_moldenhauer_number", return_value="143"
        )
        self.mock_extract_number = self.extract_number_patcher.start()

        self.find_relevant_patcher = patch(
            "unify_link_box_ids.find_relevant_svg_files",
            return_value=self.all_svg_files,
        )
        self.mock_find_relevant = self.find_relevant_patcher.start()

        self.extract_link_boxes_patcher = patch(
            "unify_link_box_ids.extract_link_boxes", return_value=[]
        )
        self.mock_extract_link_boxes = self.extract_link_boxes_patcher.start()

        self.process_single_patcher = patch(
            "unify_link_box_ids.process_single_link_box", return_value=True
        )
        self.mock_process_single = self.process_single_patcher.start()

        self.mock_id_index = {"g1": ["test1.svg"], "g2": ["test2.svg"]}
        self.build_index_patcher = patch(
            "unify_link_box_ids.build_id_to_file_index_by_class",
            return_value=self.mock_id_index,
        )
        self.mock_build_index = self.build_index_patcher.start()

        self._stdout = StringIO()
        self.stdout_patcher = patch("sys.stdout", self._stdout)
        self.stdout_patcher.start()

    def tearDown(self):
        self.extract_number_patcher.stop()
        self.find_relevant_patcher.stop()
        self.extract_link_boxes_patcher.stop()
        self.process_single_patcher.stop()
        self.build_index_patcher.stop()
        self.stdout_patcher.stop()

    def test_process_textcritics_entry_returns_for_non_dict(self):
        """Test that process_textcritics_entry returns early when entry is not a dict."""

        logger = Logger(verbose=True)
        process_textcritics_entry(
            "not-a-dict", self.all_svg_files, self.mock_get_svg_data, logger
        )
        self.mock_extract_number.assert_not_called()

    def test_process_textcritics_entry_returns_when_id_missing(self):
        """Test that process_textcritics_entry returns early when 'id' is missing."""

        logger = Logger(verbose=True)
        process_textcritics_entry(
            {}, self.all_svg_files, self.mock_get_svg_data, logger
        )
        self.mock_extract_number.assert_not_called()

    def test_process_textcritics_entry_success_basic(self):
        """Test successful processing of a textcritics entry with valid link boxes."""
        link_boxes = [
            {"svgGroupId": "g1", "linkTo": {"sheetId": "M143_Sk1"}},
            {"svgGroupId": "g2", "linkTo": {"sheetId": "M143_Sk2"}},
        ]
        self.mock_extract_link_boxes.return_value = link_boxes

        logger = Logger(verbose=True)
        process_textcritics_entry(
            self.entry, self.all_svg_files, self.mock_get_svg_data, logger
        )

        self.mock_extract_number.assert_called_once_with("M143_TF1")
        self.mock_find_relevant.assert_called_once_with(
            "M143_TF1", self.all_svg_files, "143"
        )
        self.mock_extract_link_boxes.assert_called_once_with(self.entry)
        self.mock_build_index.assert_called_once_with(
            self.all_svg_files,
            self.mock_get_svg_data,
            target_class="link-box",
        )
        expected_calls = [
            call(
                "M143_TF1",
                "g1",
                link_boxes,
                ["test1.svg"],
                self.mock_get_svg_data,
                logger=logger,
            ),
            call(
                "M143_TF1",
                "g2",
                link_boxes,
                ["test2.svg"],
                self.mock_get_svg_data,
                logger=logger,
            ),
        ]
        self.assertEqual(self.mock_process_single.call_args_list, expected_calls)

        output = self._stdout.getvalue()
        self.assertIn("Processing textcritics entry ID: M143_TF1", output)
        self.assertIn("Standard anchor: M143_TF1", output)
        self.assertIn("Relevant SVGs (2): ['test1.svg', 'test2.svg']", output)
        self.assertIn("Found 2 linkBox(es)", output)

    def test_process_textcritics_entry_prints_skrt_anchor_and_no_link_boxes(self):
        """Test that process_textcritics_entry identifies SkRT anchor and handles no link boxes."""
        entry = {"id": "M143_SkRT1"}
        self.mock_find_relevant.return_value = ["test1.svg"]

        logger = Logger(verbose=True)
        process_textcritics_entry(entry, ["test1.svg"], self.mock_get_svg_data, logger)

        self.mock_process_single.assert_not_called()
        self.assertIn("No linkBoxes to process", self._stdout.getvalue())

    def test_process_textcritics_entry_prints_skrt_anchor_with_link_boxes(self):
        """Test that 'SkRT anchor detected' is printed when the entry has link boxes."""
        entry = {"id": "M143_SkRT1"}
        self.mock_extract_link_boxes.return_value = [
            {"svgGroupId": "g1", "linkTo": {"sheetId": "M143_Sk1"}}
        ]
        self.mock_find_relevant.return_value = ["test1.svg"]

        logger = Logger(verbose=True)
        process_textcritics_entry(entry, ["test1.svg"], self.mock_get_svg_data, logger)

        self.assertIn("SkRT anchor detected: M143_SkRT1", self._stdout.getvalue())

    def test_process_single_link_box_with_missing_svg_group_id(self):
        """Test that process_textcritics_entry skips link boxes that are missing svgGroupId."""
        link_boxes = [
            {"linkTo": {"sheetId": "M143_Sk1"}},
            {"svgGroupId": "g2", "linkTo": {"sheetId": "M143_Sk2"}},
        ]
        self.mock_extract_link_boxes.return_value = link_boxes
        self.mock_find_relevant.return_value = ["sheet.svg"]
        self.mock_build_index.return_value = {"g2": ["sheet.svg"]}

        logger = Logger(verbose=True)
        process_textcritics_entry(
            self.entry, ["sheet.svg"], self.mock_get_svg_data, logger
        )

        self.mock_process_single.assert_called_once_with(
            "M143_TF1",
            "g2",
            link_boxes,
            ["sheet.svg"],
            self.mock_get_svg_data,
            logger=logger,
        )
        output = self._stdout.getvalue()
        self.assertIn("[ERROR]", output)
        self.assertIn("linkBox without svgGroupId", output)


@pytest.mark.unit
class TestUnifyLinkBoxIds(unittest.TestCase):  # pylint: disable=too-many-instance-attributes
    """Tests for unify_link_box_ids."""

    def setUp(self):
        self.mock_get_svg_data = MagicMock(name="get_svg_data")

        self.load_patcher = patch(
            "unify_link_box_ids.load_and_validate_inputs",
            return_value=({"textcritics": []}, []),
        )
        self.mock_load = self.load_patcher.start()

        self.create_loader_patcher = patch(
            "unify_link_box_ids.create_svg_loader",
            return_value=self.mock_get_svg_data,
        )
        self.mock_create_loader = self.create_loader_patcher.start()

        self.process_entry_patcher = patch(
            "unify_link_box_ids.process_textcritics_entry"
        )
        self.mock_process_entry = self.process_entry_patcher.start()

        self.save_results_patcher = patch("unify_link_box_ids.save_results")
        self.mock_save_results = self.save_results_patcher.start()

        self._stdout = StringIO()
        self.stdout_patcher = patch("sys.stdout", self._stdout)
        self.stdout_patcher.start()

    def tearDown(self):
        self.load_patcher.stop()
        self.create_loader_patcher.stop()
        self.process_entry_patcher.stop()
        self.save_results_patcher.stop()
        self.stdout_patcher.stop()

    def test_unify_link_box_ids_processes_dict_textcritics(self):
        """
        Test that unify_link_box_ids processes textcritics when root is a dict
        with 'textcritics' key.
        """
        json_data = {"textcritics": [{"id": "A"}, {"id": "B"}]}
        all_svg_files = ["A.svg", "B.svg"]
        captured = {}
        self.mock_load.return_value = (json_data, all_svg_files)

        def _fake_create_svg_loader(svg_folder, svg_file_cache):
            captured["svg_folder"] = svg_folder
            captured["svg_file_cache"] = svg_file_cache
            return self.mock_get_svg_data

        self.mock_create_loader.side_effect = _fake_create_svg_loader

        logger = Logger(dry_run=False, verbose=True)
        result = unify_link_box_ids("textcritics.json", "img/", logger)

        self.assertTrue(result)
        self.mock_load.assert_called_once_with("textcritics.json", "img/")
        self.mock_create_loader.assert_called_once()
        self.assertEqual(captured["svg_folder"], "img/")
        self.assertEqual(captured["svg_file_cache"], {})
        self.assertEqual(self.mock_process_entry.call_count, 2)
        first_call_args = self.mock_process_entry.call_args_list[0][0]
        second_call_args = self.mock_process_entry.call_args_list[1][0]
        self.assertEqual(first_call_args[0], {"id": "A"})
        self.assertEqual(first_call_args[1], all_svg_files)
        self.assertIs(first_call_args[2], self.mock_get_svg_data)
        self.assertEqual(second_call_args[0], {"id": "B"})
        self.mock_save_results.assert_called_once_with(
            json_data, captured["svg_file_cache"], "textcritics.json"
        )
        output = self._stdout.getvalue()
        self.assertIn("--- Starting Link Box ID processing ---", output)
        self.assertIn("--- Link Box ID processing completed ---", output)

    def test_unify_link_box_ids_processes_list_root(self):
        """
        Test that unify_link_box_ids processes textcritics when root is a list
        (legacy format).
        """
        json_data = [{"id": "A"}, {"id": "B"}]
        all_svg_files = ["A.svg"]
        self.mock_load.return_value = (json_data, all_svg_files)

        logger = Logger(dry_run=False, verbose=True)
        result = unify_link_box_ids("textcritics.json", "img/", logger)

        self.assertTrue(result)
        self.assertEqual(self.mock_process_entry.call_count, 2)
        self.assertEqual(self.mock_process_entry.call_args_list[0][0][0], {"id": "A"})
        self.assertEqual(self.mock_process_entry.call_args_list[1][0][0], {"id": "B"})
        self.mock_save_results.assert_called_once()
        self.assertEqual(self.mock_save_results.call_args[0][0], json_data)

    def test_unify_link_box_ids_dry_run(self):
        """
        Test that unify_link_box_ids in dry_run mode does not write files
        and prints dry-run message.
        """
        json_data = {"textcritics": [{"id": "A"}]}
        all_svg_files = ["A.svg"]
        self.mock_load.return_value = (json_data, all_svg_files)

        logger = Logger(dry_run=True, verbose=True)
        result = unify_link_box_ids("textcritics.json", "img/", logger)

        self.assertTrue(result)
        self.mock_process_entry.assert_called_once_with(
            {"id": "A"},
            all_svg_files,
            self.mock_get_svg_data,
            logger=unittest.mock.ANY,
        )

        self.mock_save_results.assert_not_called()
        output = self._stdout.getvalue()
        self.assertIn("[DRY-RUN] No files will be written.", output)
        self.assertIn("[DRY-RUN] Skipping write + validation report.", output)


@pytest.mark.unit
class TestMain(unittest.TestCase):
    """Tests for main."""

    def setUp(self):
        self.process_patcher = patch(
            "unify_link_box_ids.unify_link_box_ids", return_value=True
        )
        self.mock_process = self.process_patcher.start()

        self.exit_patcher = patch("sys.exit")
        self.mock_exit = self.exit_patcher.start()

        self._stdout = StringIO()
        self.stdout_patcher = patch("sys.stdout", self._stdout)
        self.stdout_patcher.start()

    def tearDown(self):
        self.process_patcher.stop()
        self.exit_patcher.stop()
        self.stdout_patcher.stop()

    def test_main_success_path(self):
        """Test the successful execution path of main."""
        main()
        self.mock_process.assert_called_once()
        _, _, logger = self.mock_process.call_args[0]
        self.assertIsInstance(logger, Logger)
        self.assertFalse(logger.dry_run)
        self.assertTrue(logger.verbose)
        self.mock_exit.assert_not_called()
        self.assertIn("Finished!", self._stdout.getvalue())

    def test_main_with_warnings(self):
        """Test main when unify_link_box_ids returns False indicating warnings."""
        self.mock_process.return_value = False

        main()
        self.mock_process.assert_called_once()
        _, _, logger = self.mock_process.call_args[0]
        self.assertIsInstance(logger, Logger)
        self.assertFalse(logger.dry_run)
        self.assertTrue(logger.verbose)
        self.mock_exit.assert_not_called()
        self.assertIn("Processing completed with warnings.", self._stdout.getvalue())

    def test_main_handles_file_not_found(self):
        """Test main when unify_link_box_ids raises FileNotFoundError."""
        self.mock_process.side_effect = FileNotFoundError("missing-file")

        main()

        self.mock_exit.assert_called_once_with(1)
        self.assertIn("Error: missing-file", self._stdout.getvalue())

    def test_main_handles_unexpected_error(self):
        """Test main when unify_link_box_ids raises an unexpected exception."""
        self.mock_process.side_effect = ValueError("bad-config")

        main()

        self.mock_exit.assert_called_once_with(1)
        self.assertIn("Unexpected error: bad-config", self._stdout.getvalue())
