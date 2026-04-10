#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for svg_utils.py

Tests for SVG utility functions including:
- Finding matching SVG files
- Finding relevant SVG files
- Updating SVG IDs
"""

import unittest
import pytest

from utils.constants import LINKBOX, TKK
from utils.extraction_utils import extract_file_info_list
from utils.file_utils import _parse_svg_xml
from utils.svg_utils import (
    _find_elements_by_id_and_class,
    build_entry_id_index,
    build_id_to_file_index_by_class,
    find_relevant_svg_files,
    update_svg_id_by_class,
)


@pytest.mark.unit
class TestBuildIdToFileIndexByClass(unittest.TestCase):
    """Test cases for build_id_to_file_index_by_class."""

    def test_build_id_to_file_index_by_class_indexes_expected_ids(self):
        """Only IDs with the requested class should be indexed."""
        root1, _ = _parse_svg_xml(
            '<svg><g id="id-1" class="tkk"></g><g id="id-2" class="other"></g></svg>'
        )
        root2, _ = _parse_svg_xml('<svg><g id="id-1" class="tkk selected"></g></svg>')
        data = {
            "a.svg": {"svg_root": root1},
            "b.svg": {"svg_root": root2},
        }

        index = build_id_to_file_index_by_class(
            ["a.svg", "b.svg"],
            data.get,
            target_class=TKK.css_class,
        )

        self.assertEqual(index, {"id-1": ["a.svg", "b.svg"]})

    def test_build_id_to_file_index_by_class_skips_missing_svg_root(self):
        """Cache entries with missing parsed roots must be ignored."""
        root, _ = _parse_svg_xml('<svg><g id="id-1" class="tkk"></g></svg>')
        data = {
            "missing.svg": {"svg_root": None},
            "valid.svg": {"svg_root": root},
        }

        index = build_id_to_file_index_by_class(
            ["missing.svg", "valid.svg"],
            data.get,
            target_class=TKK.css_class,
        )

        self.assertEqual(index, {"id-1": ["valid.svg"]})

    def test_build_id_to_file_index_by_class_deduplicates_ids_within_file(self):
        """Duplicate IDs inside one file should only contribute one file entry."""
        root, _ = _parse_svg_xml(
            '<svg><g id="dup" class="tkk"></g><g id="dup" class="tkk"></g></svg>'
        )
        data = {"dup.svg": {"svg_root": root}}

        index = build_id_to_file_index_by_class(
            ["dup.svg"],
            data.get,
            target_class=TKK.css_class,
        )

        self.assertEqual(index, {"dup": ["dup.svg"]})


@pytest.mark.unit
class TestBuildEntryIdIndex(unittest.TestCase):
    """Test cases for build_entry_id_index."""

    def test_build_entry_id_index_logs_context_when_verbose(self):
        """Verbose mode should log entry context and always bump entries_seen."""
        entry_id = "M_143_TF1"
        file_info_list = [{"file_name": "a.svg", "mnr": "143", "is_rowtable": False}]
        svg_loader = unittest.mock.MagicMock(name="svg_loader")
        logger = unittest.mock.MagicMock(name="logger")
        logger.verbose = True

        with unittest.mock.patch(
            "utils.svg_utils.find_relevant_svg_files", return_value=["a.svg"]
        ) as mock_find_relevant, unittest.mock.patch(
            "utils.svg_utils.build_id_to_file_index_by_class",
            return_value={"id-1": ["a.svg"]},
        ) as mock_build_index:
            result = build_entry_id_index(
                entry_id,
                file_info_list,
                svg_loader,
                logger,
                TKK.css_class,
            )

        self.assertEqual(result, {"id-1": ["a.svg"]})
        mock_find_relevant.assert_called_once_with(entry_id, file_info_list)
        logger.bump_stats.assert_called_once_with("entries_seen")
        logger.log_processing_entry_context.assert_called_once_with(
            entry_id, ["a.svg"]
        )
        mock_build_index.assert_called_once_with(
            ["a.svg"], svg_loader, target_class=TKK.css_class
        )

    def test_build_entry_id_index_skips_context_log_when_not_verbose(self):
        """Non-verbose mode should skip entry-context logging but still build index."""
        entry_id = "M_143_TF1"
        file_info_list = [{"file_name": "a.svg", "mnr": "143", "is_rowtable": False}]
        svg_loader = unittest.mock.MagicMock(name="svg_loader")
        logger = unittest.mock.MagicMock(name="logger")
        logger.verbose = False

        with unittest.mock.patch(
            "utils.svg_utils.find_relevant_svg_files", return_value=["a.svg"]
        ), unittest.mock.patch(
            "utils.svg_utils.build_id_to_file_index_by_class",
            return_value={"id-1": ["a.svg"]},
        ):
            build_entry_id_index(
                entry_id,
                file_info_list,
                svg_loader,
                logger,
                TKK.css_class,
            )

        logger.bump_stats.assert_called_once_with("entries_seen")
        logger.log_processing_entry_context.assert_not_called()


@pytest.mark.unit
class TestFindRelevantSvgs(unittest.TestCase):
    """Test cases for the find_relevant_svg_files function"""

    def setUp(self):
        """Set up test fixtures"""
        all_svg_files = [
            "M143_Textfassung1-1von2-final.svg",
            "M143_Textfassung1-2von2-final.svg",
            "M143_Textfassung2-1von1-final.svg",
            "M143_Sk1-1von1-final.svg",
            "M143_Sk10-1von9-final.svg",
            "M143_Sk10-2von9-final.svg",
            "M143_Sk10-3von9-final.svg",
            "M143_Sk11-1von4-final.svg",
            "M143_Sk11-2von4-final.svg",
            "M143_Sk12-1von2-final.svg",
            "M143_Sk2_1-1von1-final.svg",
            "M143_Sk2_1_1_1-1von1-final.svg",
            "M143_Sk2_2-1von1-final.svg",
            "M143_Sk2-1von3-final.svg",
            "M143_Sk2-2von3-final.svg",
            "M143_Sk2-3von3-final.svg",
            "op25_C_Reihentabelle-1von1-final.svg",
            "M144_sheet1.svg",
            "M145_other.svg",
        ]
        self.file_info_list = extract_file_info_list(all_svg_files)

    def test_find_relevant_svg_files_for_tf1(self):
        """Test getting SVGs for for TF1 entries"""
        result = find_relevant_svg_files("M_143_TF1", self.file_info_list)
        # Should only get Textfassung1 files, not Textfassung2
        expected = [
            "M143_Textfassung1-1von2-final.svg",
            "M143_Textfassung1-2von2-final.svg",
        ]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_standard_for_tf2(self):
        """Test getting SVGs for TF2 entries"""
        result = find_relevant_svg_files("M_143_TF2", self.file_info_list)
        # Should only get Textfassung2 files
        expected = ["M143_Textfassung2-1von1-final.svg"]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_for_sk2(self):
        """Test getting SVGs for Sk2 entries"""
        result = find_relevant_svg_files("M_143_Sk2", self.file_info_list)
        # Should only get Sk2 files (not Sk2_1, Sk2_2, etc.)
        expected = [
            "M143_Sk2-1von3-final.svg",
            "M143_Sk2-2von3-final.svg",
            "M143_Sk2-3von3-final.svg",
        ]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_for_sk2_1(self):
        """Test getting SVGs for Sk2_1 entries (sub-numbered sketches)"""
        result = find_relevant_svg_files("M_143_Sk2_1", self.file_info_list)
        # Should only get Sk2_1 files
        expected = ["M143_Sk2_1-1von1-final.svg"]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_for_sk2_2(self):
        """Test getting SVGs for Sk2_2 entries"""
        result = find_relevant_svg_files("M_143_Sk2_2", self.file_info_list)
        # Should only get Sk2_2 files
        expected = ["M143_Sk2_2-1von1-final.svg"]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_for_sk2_1_1_1(self):
        """Test getting SVGs for Sk2_1_1_1 entries (sub-numbered sketches)"""
        result = find_relevant_svg_files("M_143_Sk2_1_1_1", self.file_info_list)
        # Should only get Sk2_1_1_1 files
        expected = ["M143_Sk2_1_1_1-1von1-final.svg"]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_for_sk1_exact_match(self):
        """Test that Sk1 only matches Sk1 files, not Sk10, Sk11, etc."""
        result = find_relevant_svg_files("M_143_Sk1", self.file_info_list)
        # Should only get Sk1 files, not Sk10, Sk11, Sk12
        expected = ["M143_Sk1-1von1-final.svg"]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_for_sk10_exact_match(self):
        """Test that Sk10 only matches Sk10 files, not Sk1 or other Sk1x files"""
        result = find_relevant_svg_files("M_143_Sk10", self.file_info_list)
        # Should only get Sk10 files
        expected = [
            "M143_Sk10-1von9-final.svg",
            "M143_Sk10-2von9-final.svg",
            "M143_Sk10-3von9-final.svg",
        ]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_for_sk11_exact_match(self):
        """Test that Sk11 only matches Sk11 files, not Sk1 or Sk1x files"""
        result = find_relevant_svg_files("M_143_Sk11", self.file_info_list)
        # Should only get Sk11 files
        expected = ["M143_Sk11-1von4-final.svg", "M143_Sk11-2von4-final.svg"]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_for_sk12_exact_match(self):
        """Test that Sk12 only matches Sk12 files"""
        result = find_relevant_svg_files("M_143_Sk12", self.file_info_list)
        # Should only get Sk12 files
        expected = ["M143_Sk12-1von2-final.svg"]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_with_no_id_specified(self):
        """Test getting SVGs when no TF or Sk is specified.
        Should get all non-rowtable files.
        """
        result = find_relevant_svg_files("M_143", self.file_info_list)
        # Should get all Textfassung files when no specific TF is mentioned
        expected = [
            "M143_Textfassung1-1von2-final.svg",
            "M143_Textfassung1-2von2-final.svg",
            "M143_Textfassung2-1von1-final.svg",
            "M143_Sk1-1von1-final.svg",
            "M143_Sk10-1von9-final.svg",
            "M143_Sk10-2von9-final.svg",
            "M143_Sk10-3von9-final.svg",
            "M143_Sk11-1von4-final.svg",
            "M143_Sk11-2von4-final.svg",
            "M143_Sk12-1von2-final.svg",
            "M143_Sk2_1-1von1-final.svg",
            "M143_Sk2_1_1_1-1von1-final.svg",
            "M143_Sk2_2-1von1-final.svg",
            "M143_Sk2-1von3-final.svg",
            "M143_Sk2-2von3-final.svg",
            "M143_Sk2-3von3-final.svg",
        ]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_with_skrt(self):
        """Test getting SVGs for SkRT entries"""
        result = find_relevant_svg_files("SkRT", self.file_info_list)
        expected = ["op25_C_Reihentabelle-1von1-final.svg"]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_with_no_matches(self):
        """Test getting SVGs when no matches exist"""
        result = find_relevant_svg_files("M_999", self.file_info_list)
        self.assertEqual(result, [])

    def test_find_relevant_svg_files_with_empty_file_list(self):
        """Test with empty SVG file list"""
        result = find_relevant_svg_files("M_143", [])
        self.assertEqual(result, [])


@pytest.mark.unit
class TestUpdateSvgIdByClass(unittest.TestCase):
    """Test cases for the update_svg_id_by_class function"""

    @staticmethod
    def _make_svg_data(svg_content):
        tree, _ = _parse_svg_xml(svg_content)
        return {
            "svg_root": tree,
            "path": "dummy.svg",
            "has_xml_declaration": False,
            "dirty": False,
        }

    def test_update_svg_id_by_class_with_tkk_target_class(self):
        """Test basic ID update when element has matching class 'tkk'"""
        svg_data = self._make_svg_data(
            '<svg><g class="tkk" id="old-id">content</g></svg>'
        )
        result, error = update_svg_id_by_class(
            svg_data, "old-id", "new-id", TKK.css_class
        )
        self.assertIsNone(error)
        self.assertTrue(result)
        self.assertTrue(svg_data["dirty"])
        self.assertEqual(svg_data["svg_root"].find(".//g").get("id"), "new-id")

    def test_update_svg_id_by_class_with_link_box_target_class(self):
        """Test basic ID update when element has matching class 'link-box'"""
        svg_data = self._make_svg_data(
            '<svg><g class="link-box" id="old-id">content</g></svg>'
        )
        result, error = update_svg_id_by_class(
            svg_data, "old-id", "new-id", LINKBOX.css_class
        )
        self.assertIsNone(error)
        self.assertTrue(result)
        self.assertEqual(svg_data["svg_root"].find(".//g").get("id"), "new-id")

    def test_update_svg_id_by_class_with_no_matching_class(self):
        """Test that IDs without target class are not updated and return an error"""
        svg_data = self._make_svg_data('<g class="other" id="old-id">content</g>')
        result, error = update_svg_id_by_class(
            svg_data, "old-id", "new-id", TKK.css_class
        )
        self.assertFalse(result)
        self.assertIsNotNone(error)
        self.assertIn("'old-id' with class containing 'tkk' not found", error)
        self.assertFalse(svg_data["dirty"])

    def test_update_svg_id_by_class_with_multiple_classes(self):
        """Test matching target class regardless of position in class list"""
        test_cases = [
            '<g class="tkk other-class" id="old-id">content</g>',  # tkk first
            '<g class="other-class tkk" id="old-id">content</g>',  # tkk last
            '<g class="active tkk selected" id="old-id">content</g>',  # tkk middle
        ]
        for svg_content in test_cases:
            svg_data = self._make_svg_data(svg_content)
            result, error = update_svg_id_by_class(
                svg_data, "old-id", "new-id", TKK.css_class
            )
            self.assertIsNone(error)
            self.assertTrue(result)
            self.assertEqual(svg_data["svg_root"].get("id"), "new-id")

    def test_update_svg_id_by_class_with_partial_class_name_no_match(self):
        """Test that partial matches of 'tkk' in class names are not updated"""
        svg_data = self._make_svg_data('<g class="tkkish" id="old-id">content</g>')
        result, error = update_svg_id_by_class(
            svg_data, "old-id", "new-id", TKK.css_class
        )
        self.assertFalse(result)
        self.assertIsNotNone(error)
        self.assertIn("'old-id' with class containing 'tkk' not found", error)

    def test_update_svg_id_by_class_already_updated_id(self):
        """Test no-op behavior when old and new IDs are equal."""
        svg_data = self._make_svg_data('<g class="tkk" id="new-id">content</g>')
        result, error = update_svg_id_by_class(
            svg_data, "new-id", "new-id", TKK.css_class
        )
        self.assertFalse(result)
        self.assertIsNone(error)
        self.assertFalse(svg_data["dirty"])

    def test_update_svg_id_by_class_with_multiple_occurrences(self):
        """Test that multiple class='tkk' elements with same ID cause an error"""
        svg_content = """<svg>
    <g class="tkk" id="old-id">content1</g>
    <g id="old-id" class="tkk other-class">content2</g>
    <g class="other" id="old-id">content3</g>
</svg>"""
        svg_data = self._make_svg_data(svg_content)
        result, error = update_svg_id_by_class(
            svg_data, "old-id", "new-id", TKK.css_class
        )

        self.assertFalse(result)
        self.assertIsNotNone(error)
        self.assertIn("Multiple class='tkk' elements found with ID 'old-id'", error)
        self.assertIn("2 occurrences", error)  # Should find 2 tkk elements

    def test_update_svg_id_by_class_marks_dirty(self):
        """Test that successful updates mark the cache entry as dirty."""
        svg_data = self._make_svg_data('<svg><g class="tkk" id="old-id">x</g></svg>')
        result, error = update_svg_id_by_class(
            svg_data, "old-id", "new-id", TKK.css_class
        )
        self.assertTrue(result)
        self.assertIsNone(error)
        self.assertTrue(svg_data["dirty"])

    def test_update_svg_id_by_class_with_invalid_xml(self):
        """Test handling of missing/invalid parsed tree in svg_data."""
        svg_data = {
            "svg_root": None,
            "path": "broken.svg",
            "has_xml_declaration": False,
            "dirty": False,
        }
        result, error = update_svg_id_by_class(
            svg_data, "old-id", "new-id", TKK.css_class
        )

        self.assertFalse(result)
        self.assertIsNotNone(error)
        self.assertIn("No parsed svg_root available", error)


@pytest.mark.unit
class TestFindElementsByIdAndClass(unittest.TestCase):
    """Test cases for the _find_elements_by_id_and_class helper function"""

    def test_find_elements_with_matching_id_and_class_tkk(self):
        """Test finding element with matching ID and class 'tkk'"""
        svg_content = '<svg><g id="test-id" class="tkk">content</g></svg>'
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", TKK.css_class)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get("id"), "test-id")

    def test_find_elements_with_matching_id_and_class_link_box(self):
        """Test finding element with matching ID and class 'link-box'"""
        svg_content = '<svg><g id="test-id" class="link-box">content</g></svg>'
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", LINKBOX.css_class)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get("id"), "test-id")

    def test_find_elements_with_no_matching_id(self):
        """Test that no elements are found when ID doesn't match"""
        svg_content = '<svg><g id="other-id" class="tkk">content</g></svg>'
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", TKK.css_class)
        self.assertEqual(result, [])

    def test_find_elements_with_no_matching_class(self):
        """Test that no elements are found when class doesn't match"""
        svg_content = '<svg><g id="test-id" class="other">content</g></svg>'
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", TKK.css_class)
        self.assertEqual(result, [])

    def test_find_elements_with_multiple_matching_elements(self):
        """Test finding multiple elements with matching ID and class"""
        svg_content = """<svg>
    <g id="test-id" class="tkk">content1</g>
    <g id="test-id" class="tkk">content2</g>
    <g id="test-id" class="other">content3</g>
</svg>"""
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", TKK.css_class)
        self.assertEqual(len(result), 2)
        for elem in result:
            self.assertEqual(elem.get("id"), "test-id")
            self.assertIn("tkk", elem.get("class", "").split())

    def test_find_elements_with_multiple_classes_target_at_start(self):
        """Test class matching when target class is first in list"""
        svg_content = '<svg><g id="test-id" class="tkk other">content</g></svg>'
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", TKK.css_class)
        self.assertEqual(len(result), 1)

    def test_find_elements_with_multiple_classes_target_at_end(self):
        """Test class matching when target class is last in list"""
        svg_content = '<svg><g id="test-id" class="other tkk">content</g></svg>'
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", TKK.css_class)
        self.assertEqual(len(result), 1)

    def test_find_elements_with_multiple_classes_target_in_middle(self):
        """Test class matching when target class is in middle"""
        svg_content = '<svg><g id="test-id" class="first tkk last">content</g></svg>'
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", TKK.css_class)
        self.assertEqual(len(result), 1)

    def test_find_elements_partial_class_name_no_match(self):
        """Test that partial class matches don't match"""
        svg_content = '<svg><g id="test-id" class="tkkish">content</g></svg>'
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", TKK.css_class)
        self.assertEqual(result, [])

    def test_find_elements_with_no_class_attribute(self):
        """Test that elements without class attribute don't match"""
        svg_content = '<svg><g id="test-id">content</g></svg>'
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", TKK.css_class)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
