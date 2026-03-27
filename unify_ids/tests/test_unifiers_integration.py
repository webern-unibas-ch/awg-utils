#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration tests for unifier scripts using temporary and scenario fixtures."""

from io import StringIO
import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

import pytest

from unify_link_box_ids import unify_link_box_ids
from unify_tkk_ids import unify_tkk_ids
from utils.logger_utils import Logger


class ScenarioFixtureBase(unittest.TestCase):
    """Shared fixture setup and file helpers for scenario-based integration tests."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.json_path = os.path.join(self.test_dir, "textcritics.json")
        self.svg_dir = os.path.join(self.test_dir, "svgs")
        os.makedirs(self.svg_dir)

        self.repo_root = os.path.dirname(os.path.dirname(__file__))
        self.scenario_data_dir = os.path.join(
            self.repo_root, "tests", "data", "scenarios"
        )
        self.scenario_img_dir = os.path.join(
            self.repo_root, "tests", "img", "scenarios"
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _copy_json_fixture(self, json_fixture):
        shutil.copyfile(
            os.path.join(self.scenario_data_dir, json_fixture),
            self.json_path,
        )

    def _copy_svg_fixture(self, svg_fixture):
        shutil.copyfile(
            os.path.join(self.scenario_img_dir, svg_fixture),
            os.path.join(self.svg_dir, svg_fixture),
        )

    def _prepare_scenario(self, json_fixture, *svg_fixtures):
        self._copy_json_fixture(json_fixture)
        for svg_fixture in svg_fixtures:
            self._copy_svg_fixture(svg_fixture)

    def _read_file_text(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _read_json(self):
        return json.loads(self._read_file_text(self.json_path))

    def _read_svg(self, svg_filename):
        return self._read_file_text(os.path.join(self.svg_dir, svg_filename))

    def _block_comments(self, json_data, textcritic_index=0, comment_index=0):
        return json_data["textcritics"][textcritic_index]["commentary"]["comments"][
            comment_index
        ]["blockComments"]

    def _link_boxes(self, json_data, textcritic_index=0):
        return json_data["textcritics"][textcritic_index]["linkBoxes"]

    @staticmethod
    def _logger(verbose=True, dry_run=False):
        return Logger(verbose=verbose, dry_run=dry_run)


@pytest.mark.integration
class TestScenarioFixturesTkkIntegration(ScenarioFixtureBase):
    """Integration tests using minimal scenario fixtures in tests/data|img/scenarios."""

    def test_scenario_single_success_updates_json_and_svg(self):
        """Test that a single textcritic's svgGroupId is updated in both JSON and SVG."""
        json_fixture = "tkk_single_success.json"
        svg_fixture = "M200_Textfassung1-1von1-tkk-single.svg"

        self._prepare_scenario(
            json_fixture,
            svg_fixture,
        )

        self.assertTrue(unify_tkk_ids(self.json_path, self.svg_dir, self._logger()))

        json_data = self._read_json()

        entry_id = json_data["textcritics"][0]["id"].lower()
        expected_id = f"awg-tkk-{entry_id}-001"
        block_comments = self._block_comments(json_data)
        updated_id = block_comments[0]["svgGroupId"]
        self.assertEqual(updated_id, expected_id)

        svg_content = self._read_svg(svg_fixture)
        self.assertIn(f'id="{expected_id}"', svg_content)
        self.assertNotIn('id="old-id-1"', svg_content)

    def test_scenario_missing_svg_id_keeps_json_unchanged(self):
        """Test that unmatched svgGroupId leaves JSON unchanged."""
        json_fixture = "tkk_missing_svg_id.json"
        svg_fixture = "M201_Sk1-1von1-tkk-no-match.svg"

        self._prepare_scenario(
            json_fixture,
            svg_fixture,
        )

        before_json_data = self._read_json()
        expected_unchanged_id = self._block_comments(before_json_data)[0]["svgGroupId"]

        self.assertTrue(unify_tkk_ids(self.json_path, self.svg_dir, self._logger()))

        after_json_data = self._read_json()
        unchanged_id = self._block_comments(after_json_data)[0]["svgGroupId"]
        self.assertEqual(unchanged_id, expected_unchanged_id)

    def test_scenario_single_success_dry_run_keeps_files_unchanged(self):
        """Test that dry-run mode does not modify JSON or SVG files."""
        json_fixture = "tkk_single_success.json"
        svg_fixture = "M200_Textfassung1-1von1-tkk-single.svg"

        self._prepare_scenario(
            json_fixture,
            svg_fixture,
        )

        json_before_data = self._read_file_text(self.json_path)
        svg_path = os.path.join(
            self.svg_dir,
            svg_fixture,
        )
        svg_before_data = self._read_file_text(svg_path)

        self.assertTrue(
            unify_tkk_ids(self.json_path, self.svg_dir, self._logger(dry_run=True))
        )

        json_after = self._read_file_text(self.json_path)
        svg_after = self._read_file_text(svg_path)

        self.assertEqual(json_before_data, json_after)
        self.assertEqual(svg_before_data, svg_after)

    def test_scenario_single_success_second_run_is_noop(self):
        """Test that a second run after success is a no-op."""
        json_fixture = "tkk_single_success.json"
        svg_fixture = "M200_Textfassung1-1von1-tkk-single.svg"

        self._prepare_scenario(
            json_fixture,
            svg_fixture,
        )

        self.assertTrue(unify_tkk_ids(self.json_path, self.svg_dir, self._logger()))

        json_after_data_first = self._read_file_text(self.json_path)
        svg_path = os.path.join(
            self.svg_dir,
            svg_fixture,
        )
        svg_after_first = self._read_file_text(svg_path)

        self.assertTrue(unify_tkk_ids(self.json_path, self.svg_dir, self._logger()))

        json_after_second = self._read_file_text(self.json_path)
        svg_after_second = self._read_file_text(svg_path)

        self.assertEqual(json_after_data_first, json_after_second)
        self.assertEqual(svg_after_first, svg_after_second)

    def test_scenario_no_svg_group_ids_prints_skip_message(self):
        """Test that no svgGroupId values trigger skip message and no changes."""
        json_fixture = "tkk_no_svg_group_ids.json"
        svg_fixture = "M201_Sk1-1von1-tkk-no-match.svg"

        self._prepare_scenario(
            json_fixture,
            svg_fixture,
        )

        with patch("sys.stdout", new_callable=StringIO) as captured:
            self.assertTrue(
                unify_tkk_ids(self.json_path, self.svg_dir, self._logger(verbose=True))
            )

        self.assertIn("No changes detected; skipping writes.", captured.getvalue())

    def test_unify_tkk_ids_missing_json_path_raises(self):
        """Test that missing JSON path raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            unify_tkk_ids("/nonexistent/path.json", self.svg_dir, self._logger())

    def test_unify_tkk_ids_missing_svg_dir_raises(self):
        """Test that missing SVG directory raises FileNotFoundError."""
        json_fixture = "tkk_single_success.json"
        svg_fixture = "M200_Textfassung1-1von1-tkk-single.svg"

        self._prepare_scenario(
            json_fixture,
            svg_fixture,
        )

        with self.assertRaises(FileNotFoundError):
            unify_tkk_ids(self.json_path, "/nonexistent/dir", self._logger())

    def test_scenario_todo_and_mixed_skips_todo_and_updates_valid_id(self):
        """Test that mixed TODO and valid IDs update only valid entries."""
        json_fixture = "tkk_todo_and_mixed.json"
        svg_fixture = "M220_Sk1-1von1-tkk-todo-mixed.svg"
        expected_id = "awg-tkk-m220_sk1-001"

        self._prepare_scenario(
            json_fixture,
            svg_fixture,
        )

        self.assertTrue(unify_tkk_ids(self.json_path, self.svg_dir, self._logger()))

        json_data = self._read_json()
        block_comments = self._block_comments(json_data)
        self.assertEqual(block_comments[0]["svgGroupId"], "TODO")
        self.assertEqual(block_comments[1]["svgGroupId"], expected_id)

        svg_content = self._read_svg(svg_fixture)
        self.assertIn(f'id="{expected_id}"', svg_content)
        self.assertNotIn('id="old-id-2"', svg_content)

    def test_scenario_skrt_updates_only_rowtable_svg(self):
        """Test that SkRT updates only the Reihentabelle SVG, not normal Sk SVG."""
        json_fixture = "tkk_skrt_rowtable_only.json"
        rowtable_svg_fixture = "M230_Reihentabelle-1von1-tkk-skrt-rowtable.svg"
        control_svg_fixture = "M230_Sk1-1von1-tkk-skrt-control.svg"
        expected_id = "awg-tkk-m230_skrt-001"

        self._prepare_scenario(
            json_fixture,
            rowtable_svg_fixture,
        )
        self._copy_svg_fixture(control_svg_fixture)

        normal_svg_path = os.path.join(
            self.svg_dir,
            control_svg_fixture,
        )
        normal_svg_before = self._read_file_text(normal_svg_path)

        self.assertTrue(unify_tkk_ids(self.json_path, self.svg_dir, self._logger()))

        json_data = self._read_json()
        self.assertEqual(self._block_comments(json_data)[0]["svgGroupId"], expected_id)

        rowtable_svg = self._read_svg(rowtable_svg_fixture)
        normal_svg = self._read_file_text(normal_svg_path)

        self.assertIn(f'id="{expected_id}"', rowtable_svg)
        self.assertNotIn('id="old-id-skrt-1"', rowtable_svg)
        self.assertEqual(normal_svg, normal_svg_before)

    def test_scenario_multi_ids_single_file_success_updates_all_ids(self):
        """Test that multiple IDs in one SVG are all updated in JSON and SVG."""
        json_fixture = "tkk_multi_ids_single_file_success.json"
        svg_fixture = "M240_Sk1-1von1-tkk-multi-ids.svg"
        expected_ids = [
            "awg-tkk-m240_sk1-001",
            "awg-tkk-m240_sk1-002",
            "awg-tkk-m240_sk1-003",
        ]
        self._prepare_scenario(
            json_fixture,
            svg_fixture,
        )

        self.assertTrue(unify_tkk_ids(self.json_path, self.svg_dir, self._logger()))

        json_data = self._read_json()

        block_comments = self._block_comments(json_data)
        self.assertEqual([c["svgGroupId"] for c in block_comments], expected_ids)

        svg_content = self._read_svg(svg_fixture)

        for expected_id in expected_ids:
            self.assertIn(f'id="{expected_id}"', svg_content)
        self.assertNotIn('id="old-id-a"', svg_content)
        self.assertNotIn('id="old-id-b"', svg_content)
        self.assertNotIn('id="old-id-c"', svg_content)

    def test_scenario_multi_file_success_updates_json_and_each_file(self):
        """Test that multiple IDs across files update JSON and each matching SVG."""
        json_fixture = "tkk_multi_file_success.json"
        svg_fixture_a = "M241_Sk1-1von2-tkk-multi-file-a.svg"
        svg_fixture_b = "M241_Sk1-2von2-tkk-multi-file-b.svg"
        expected_ids = ["awg-tkk-m241_sk1-001", "awg-tkk-m241_sk1-002"]

        self._prepare_scenario(
            json_fixture,
            svg_fixture_a,
        )
        self._copy_svg_fixture(svg_fixture_b)

        self.assertTrue(unify_tkk_ids(self.json_path, self.svg_dir, self._logger()))

        json_data = self._read_json()

        block_comments = self._block_comments(json_data)
        self.assertEqual(
            [c["svgGroupId"] for c in block_comments],
            expected_ids,
        )

        svg_one = self._read_svg(svg_fixture_a)
        svg_two = self._read_svg(svg_fixture_b)

        self.assertIn(f'id="{expected_ids[0]}"', svg_one)
        self.assertIn(f'id="{expected_ids[1]}"', svg_two)
        self.assertNotIn('id="old-id-mf-1"', svg_one)
        self.assertNotIn('id="old-id-mf-2"', svg_two)

    def test_scenario_mixed_entry_types_success_updates_sk_and_skrt(self):
        """Test that mixed Sk and SkRT entries update the correct IDs and SVGs."""
        json_fixture = "tkk_mixed_entry_types_success.json"
        svg_fixtures = [
            "M242_Sk1-1von1-tkk-mixed-sk-primary.svg",
            "M243_Sk2-1von1-tkk-mixed-sk.svg",
            "M244_Reihentabelle-1von1-tkk-mixed-skrt-rowtable.svg",
            "M244_Sk1-1von1-tkk-mixed-skrt-control.svg",
        ]
        expected_ids = [
            "awg-tkk-m242_sk1-001",
            "awg-tkk-m243_sk2-001",
            "awg-tkk-m244_skrt-001",
        ]

        self._prepare_scenario(
            json_fixture,
            svg_fixtures[0],
        )
        self._copy_svg_fixture(svg_fixtures[1])
        self._copy_svg_fixture(svg_fixtures[2])
        self._copy_svg_fixture(svg_fixtures[3])

        self.assertTrue(unify_tkk_ids(self.json_path, self.svg_dir, self._logger()))

        json_data = self._read_json()

        self.assertEqual(
            self._block_comments(json_data, textcritic_index=0)[0]["svgGroupId"],
            expected_ids[0],
        )
        self.assertEqual(
            self._block_comments(json_data, textcritic_index=1)[0]["svgGroupId"],
            expected_ids[1],
        )
        self.assertEqual(
            self._block_comments(json_data, textcritic_index=2)[0]["svgGroupId"],
            expected_ids[2],
        )

        self.assertIn(f'id="{expected_ids[0]}"', self._read_svg(svg_fixtures[0]))
        self.assertIn(f'id="{expected_ids[1]}"', self._read_svg(svg_fixtures[1]))
        self.assertIn(f'id="{expected_ids[2]}"', self._read_svg(svg_fixtures[2]))
        self.assertIn('id="old-id-mix-skrt-normal"', self._read_svg(svg_fixtures[3]))
        self.assertNotIn(f'id="{expected_ids[2]}"', self._read_svg(svg_fixtures[3]))

    def test_scenario_mx_high_number_success_updates_json_and_svg(self):
        """Test that high Moldenhauer numbers (for example Mx430) format IDs correctly."""
        json_fixture = "tkk_mx_high_number_success.json"
        svg_fixture = "Mx430_Sk1-1von1-tkk-mx-high-number.svg"
        expected_id = "awg-tkk-mx430_sk1-001"

        self._prepare_scenario(
            json_fixture,
            svg_fixture,
        )

        self.assertTrue(unify_tkk_ids(self.json_path, self.svg_dir, self._logger()))

        json_data = self._read_json()
        self.assertEqual(self._block_comments(json_data)[0]["svgGroupId"], expected_id)

        svg_content = self._read_svg(svg_fixture)
        self.assertIn(f'id="{expected_id}"', svg_content)
        self.assertNotIn('id="old-id-mx-1"', svg_content)


@pytest.mark.integration
class TestScenarioFixturesLinkBoxIntegration(ScenarioFixtureBase):
    """Integration tests using minimal scenario fixtures in tests/data|img/scenarios."""

    def test_scenario_single_success_updates_json_and_svg(self):
        """Test that single linkBox svgGroupId is updated in both JSON and SVG."""
        json_fixture = "linkbox_single_success.json"
        svg_fixture_name = "M300_Sk1-1von1-linkbox-single.svg"

        self._prepare_scenario(json_fixture, svg_fixture_name)

        before_json_data = self._read_json()
        entry_id = before_json_data["textcritics"][0]["id"].lower()
        target_sheet_id = self._link_boxes(before_json_data)[0]["linkTo"][
            "sheetId"
        ].lower()
        expected_id = f"awg-lb-{entry_id}-to-{target_sheet_id}"

        self.assertTrue(unify_link_box_ids(self.json_path, self.svg_dir, self._logger()))

        json_data = self._read_json()
        link_boxes = self._link_boxes(json_data)
        updated_id = link_boxes[0]["svgGroupId"]
        self.assertEqual(updated_id, expected_id)

        svg_content = self._read_svg(svg_fixture_name)
        self.assertIn(f'id="{expected_id}"', svg_content)
        self.assertNotIn('id="lb-old-1"', svg_content)

    def test_scenario_multi_match_expands_json_and_updates_each_svg(self):
        """Test that multi-match linkBoxes expand JSON and update each matching SVG."""
        json_fixture = "linkbox_multi_match_expand.json"
        svg_1 = "M310_Sk1-1von2-linkbox-multi-a.svg"
        svg_2 = "M310_Sk1-2von2-linkbox-multi-b.svg"
        expected_ids = sorted(
            [
                "awg-lb-m310_sk1a-to-m311_sk2",
                "awg-lb-m310_sk1b-to-m311_sk2",
            ]
        )

        self._prepare_scenario(json_fixture, svg_1, svg_2)

        self.assertTrue(unify_link_box_ids(self.json_path, self.svg_dir, self._logger()))

        json_data = self._read_json()

        actual_ids = sorted(lb["svgGroupId"] for lb in self._link_boxes(json_data))
        self.assertEqual(actual_ids, expected_ids)

        svg_1_content = self._read_svg(svg_1)
        svg_2_content = self._read_svg(svg_2)

        self.assertIn(f'id="{expected_ids[0]}"', svg_1_content)
        self.assertIn(f'id="{expected_ids[1]}"', svg_2_content)
        self.assertNotIn('id="lb-dup-1"', svg_1_content)
        self.assertNotIn('id="lb-dup-1"', svg_2_content)

    def test_scenario_missing_sheetid_keeps_json_and_svg_unchanged(self):
        """Test that missing linkTo.sheetId keeps JSON and SVG unchanged."""
        json_fixture = "linkbox_missing_sheetid.json"
        svg_fixture_name = "M320_Sk1-1von1-linkbox-missing-sheetid.svg"

        self._prepare_scenario(json_fixture, svg_fixture_name)

        json_before = self._read_file_text(self.json_path)
        svg_before = self._read_svg(svg_fixture_name)

        self.assertTrue(unify_link_box_ids(self.json_path, self.svg_dir, self._logger()))

        json_after = self._read_file_text(self.json_path)
        svg_after = self._read_svg(svg_fixture_name)

        self.assertEqual(json_before, json_after)
        self.assertEqual(svg_before, svg_after)


@pytest.mark.integration
class TestScenarioFixturesCombinedIntegration(ScenarioFixtureBase):
    """Integration tests that run both unifiers against one shared scenario."""

    def test_scenario_combined_tkk_and_linkbox_success(self):
        """Test that combined scenario updates both TKK and link-box IDs correctly."""
        json_fixture = "combined_tkk_linkbox_success.json"
        svg_fixture = "M245_Sk1-1von1-combined-tkk-linkbox.svg"
        expected_tkk_id = "awg-tkk-m245_sk1-001"
        expected_linkbox_id = "awg-lb-m245_sk1-to-m246_sk2"

        self._prepare_scenario(
            json_fixture,
            svg_fixture,
        )

        self.assertTrue(unify_tkk_ids(self.json_path, self.svg_dir, self._logger()))
        self.assertTrue(unify_link_box_ids(self.json_path, self.svg_dir, self._logger()))

        json_data = self._read_json()
        block_comments = self._block_comments(json_data)
        link_boxes = self._link_boxes(json_data)

        self.assertEqual(
            block_comments[0]["svgGroupId"],
            expected_tkk_id,
        )
        self.assertEqual(link_boxes[0]["svgGroupId"], expected_linkbox_id)

        svg_content = self._read_svg(svg_fixture)

        self.assertIn(f'id="{expected_tkk_id}"', svg_content)
        self.assertIn(f'id="{expected_linkbox_id}"', svg_content)
        self.assertNotIn('id="old-id-tkk-1"', svg_content)
        self.assertNotIn('id="lb-old-mix-1"', svg_content)
