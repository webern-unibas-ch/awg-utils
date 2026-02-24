#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for extraction_utils.py module

This test suite provides comprehensive testing for the extraction utilities
used in TKK ID processing. The extraction_utils module handles extraction
and parsing of various identifiers and data structures.

Test Categories:
- extract_moldenhauer_number function tests (catalog number extraction)
- extract_svg_group_ids function tests (SVG group ID collection from entries)
- Edge cases and error conditions for extraction operations

Usage:
    python -m pytest tests/test_extraction_utils.py -v
    python -m pytest tests/test_extraction_utils.py::TestExtractMoldenhauerNumber -v
    python -m pytest tests/test_extraction_utils.py::TestExtractSvgGroupIds -v
"""

import unittest
import pytest

# Import extraction functions from extraction_utils
from extraction_utils import (
    extract_moldenhauer_number,
    extract_svg_group_ids
)


@pytest.mark.unit
class TestExtractMoldenhauerNumber(unittest.TestCase):
    """Test cases for the extract_moldenhauer_number function"""

    def test_extract_moldenhauer_number_from_simple_id(self):
        """Test extracting Moldenhauer numbers from simple ID strings"""
        self.assertEqual(extract_moldenhauer_number("M_143"), "143")
        self.assertEqual(extract_moldenhauer_number("Mx_123"), "123")

    def test_extract_moldenhauer_number_from_structured_id(self):
        """Test extracting Moldenhauer number from structured ID strings"""
        self.assertEqual(extract_moldenhauer_number("M_143_TF5"), "143")
        self.assertEqual(extract_moldenhauer_number("Mx_123_Sk456"), "123")
        self.assertEqual(extract_moldenhauer_number("M_789_op1_test2"), "789")

    def test_extract_moldenhauer_number_from_filename_without_underscore(self):
        """Test extracting numbers from filename patterns without underscore after M/Mx"""
        self.assertEqual(extract_moldenhauer_number("M143_Textfassung1"), "143")
        self.assertEqual(extract_moldenhauer_number("Mx136_Sk1"), "136")
        self.assertEqual(extract_moldenhauer_number("M789_file"), "789")
        self.assertEqual(extract_moldenhauer_number("M14_test"), "14")
        # Mixed patterns - should still work with existing underscore patterns
        self.assertEqual(extract_moldenhauer_number("M_143_TF1"), "143")
        self.assertEqual(extract_moldenhauer_number("M143TF1"), "143")

    def test_extract_moldenhauer_number_with_no_moldenhauer_pattern(self):
        """Test ID strings with no M/Mx pattern"""
        self.assertEqual(extract_moldenhauer_number("no_pattern_here"), "")
        self.assertEqual(extract_moldenhauer_number("abc_def"), "")
        self.assertEqual(extract_moldenhauer_number(""), "")
        self.assertEqual(extract_moldenhauer_number("123456"), "")  # No M/Mx prefix

    def test_extract_moldenhauer_number_with_none_input(self):
        """Test with None input (converted to string)"""
        self.assertEqual(extract_moldenhauer_number(None), "")

    def test_extract_moldenhauer_number_with_special_characters(self):
        """Test extract_moldenhauer_numbers with special characters"""
        self.assertEqual(extract_moldenhauer_number("M_143-op5.2"), "143")
        self.assertEqual(extract_moldenhauer_number("Mx_123#test456$"), "123")
        self.assertEqual(extract_moldenhauer_number("M_789_测试_123"), "789")


@pytest.mark.unit
class TestExtractSvgGroupIds(unittest.TestCase):
    """Test cases for the extract_svg_group_ids function"""

    def test_extract_svg_group_ids_basic(self):
        """Test extracting svgGroupIds from a basic entry structure"""
        entry = {
            "id": "M_143_TF1",
            "commentary": {
                "preamble": "",
                "comments": [
                    {
                        "blockHeader": "",
                        "blockComments": [
                            {"svgGroupId": "test-id-1", "text": "Comment 1"},
                            {"svgGroupId": "test-id-2", "text": "Comment 2"}
                        ]
                    }
                ]
            }
        }

        svg_group_ids, block_comments = extract_svg_group_ids(entry)

        expected_ids = ["test-id-1", "test-id-2"]
        self.assertEqual(svg_group_ids, expected_ids)
        self.assertEqual(len(block_comments), 2)
        self.assertEqual(block_comments[0]["svgGroupId"], "test-id-1")
        self.assertEqual(block_comments[1]["svgGroupId"], "test-id-2")

    def test_extract_svg_group_ids_with_multiple_comment_groups(self):
        """Test extracting svgGroupIds from multiple comment groups"""
        entry = {
            "id": "M_143_TF1",
            "commentary": {
                "preamble": "",
                "comments": [
                    {
                        "blockHeader": "",
                        "blockComments": [
                            {"svgGroupId": "id-1", "text": "Comment 1"},
                            {"svgGroupId": "id-2", "text": "Comment 2"}
                        ]
                    },
                    {
                        "blockHeader": "",
                        "blockComments": [
                            {"svgGroupId": "id-3", "text": "Comment 3"}
                        ]
                    }
                ]
            }
        }

        svg_group_ids, block_comments = extract_svg_group_ids(entry)

        expected_ids = ["id-1", "id-2", "id-3"]
        self.assertEqual(svg_group_ids, expected_ids)
        self.assertEqual(len(block_comments), 3)

    def test_extract_svg_group_ids_with_todo_entries(self):
        """Test that TODO entries are filtered out"""
        entry = {
            "id": "M_143_TF1",
            "commentary": {
                "preamble": "",
                "comments": [
                    {
                        "blockHeader": "",
                        "blockComments": [
                            {"svgGroupId": "test-id-1", "text": "Comment 1"},
                            {"svgGroupId": "TODO", "text": "TODO Comment"},
                            {"svgGroupId": "test-id-2", "text": "Comment 2"}
                        ]
                    }
                ]
            }
        }

        svg_group_ids, block_comments = extract_svg_group_ids(entry)

        # The TODO entries should be filtered out
        expected_ids = ["test-id-1", "test-id-2"]
        self.assertEqual(svg_group_ids, expected_ids)
        self.assertEqual(len(block_comments), 2)

        # Verify that TODO block comment is not included
        for comment in block_comments:
            self.assertNotEqual(comment["svgGroupId"], "TODO")

    def test_extract_svg_group_ids_with_empty_ids(self):
        """Test that empty or None svgGroupId entries are filtered out"""
        entry = {
            "id": "M_143_TF1",
            "commentary": {
                "preamble": "",
                "comments": [
                    {
                        "blockHeader": "",
                        "blockComments": [
                            {"svgGroupId": "test-id-1", "text": "Comment 1"},
                            {"svgGroupId": "", "text": "Empty ID"},
                            {"svgGroupId": None, "text": "None ID"},
                            {"text": "No svgGroupId field"},
                            {"svgGroupId": "test-id-2", "text": "Comment 2"}
                        ]
                    }
                ]
            }
        }

        svg_group_ids, block_comments = extract_svg_group_ids(entry)

        # Only valid IDs should be included
        expected_ids = ["test-id-1", "test-id-2"]
        self.assertEqual(svg_group_ids, expected_ids)
        self.assertEqual(len(block_comments), 2)

    def test_extract_svg_group_ids_with_no_commentary(self):
        """Test entry with no commentary section"""
        entry = {"id": "M_143_TF1"}

        svg_group_ids, block_comments = extract_svg_group_ids(entry)

        self.assertEqual(svg_group_ids, [])
        self.assertEqual(block_comments, [])

    def test_extract_svg_group_ids_with_no_comments(self):
        """Test entry with commentary but no comments"""
        entry = {
            "id": "M_143_TF1",
            "commentary": {"preamble": "", "comments": []}
        }

        svg_group_ids, block_comments = extract_svg_group_ids(entry)

        self.assertEqual(svg_group_ids, [])
        self.assertEqual(block_comments, [])

    def test_extract_svg_group_ids_with_no_block_comments(self):
        """Test entry with comments but no blockComments"""
        entry = {
            "id": "M_143_TF1",
            "commentary": {
                "preamble": "",
                "comments": [
                    {"blockHeader": "", "blockComments": []},
                    {"blockHeader": "", "otherField": "value"}
                ]
            }
        }

        svg_group_ids, block_comments = extract_svg_group_ids(entry)

        self.assertEqual(svg_group_ids, [])
        self.assertEqual(block_comments, [])

    def test_extract_svg_group_ids_preserves_order(self):
        """Test that the order of svgGroupIds is preserved"""
        entry = {
            "id": "M_143_TF1",
            "commentary": {
                "preamble": "",
                "comments": [
                    {
                        "blockHeader": "",
                        "blockComments": [
                            {"svgGroupId": "z-last", "text": "Should be first"},
                            {"svgGroupId": "a-first", "text": "Should be second"},
                            {"svgGroupId": "m-middle", "text": "Should be third"}
                        ]
                    }
                ]
            }
        }

        svg_group_ids, block_comments = extract_svg_group_ids(entry)

        # Should preserve original order, not alphabetical
        expected_ids = ["z-last", "a-first", "m-middle"]
        self.assertEqual(svg_group_ids, expected_ids)

        # Block comments should be in same order
        self.assertEqual(block_comments[0]["svgGroupId"], "z-last")
        self.assertEqual(block_comments[1]["svgGroupId"], "a-first")
        self.assertEqual(block_comments[2]["svgGroupId"], "m-middle")

    def test_extract_svg_group_ids_returns_references(self):
        """Test that returned block_comments are references to original objects"""
        original_comment = {"svgGroupId": "test-id", "text": "Original"}
        entry = {
            "id": "M_143_TF1",
            "commentary": {
                "preamble": "",
                "comments": [
                    {"blockHeader": "", "blockComments": [original_comment]}
                ]
            }
        }

        _, block_comments = extract_svg_group_ids(entry)

        # Modify the returned comment
        block_comments[0]["text"] = "Modified"

        # Original should also be modified (same object reference)
        self.assertEqual(original_comment["text"], "Modified")


if __name__ == '__main__':
    unittest.main()
