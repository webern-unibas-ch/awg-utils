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
from unittest.mock import patch
import pytest

# Import the functions we want to test
from utils.svg_utils import (
    find_matching_svg_files,
    find_relevant_svg_files,
    update_svg_id
)


@pytest.mark.unit
class TestFindMatchingSvgFiles(unittest.TestCase):
    """Test cases for the find_matching_svg_files function"""

    def setUp(self):
        """Set up test fixtures"""
        self.relevant_svgs = [
            "file1.svg",
            "file2.svg",
            "file3.svg"
        ]
        self.test_svg_content = {
            "file1.svg": {"content": '<g class="tkk" id="test-id-1">content</g>'},
            "file2.svg": {"content": '<g id="test-id-2" class="tkk">content</g>'},
            "file3.svg": {"content": '<g class="other" id="test-id-3">content</g>'}
        }

    def mock_get_svg_data(self, filename):
        """Mock function to simulate get_svg_data"""
        return self.test_svg_content.get(filename, {"content": ""})

    def test_find_matching_svg_files_with_single_match(self):
        """Test finding SVG files with single matching ID"""
        result = find_matching_svg_files("test-id-1", self.relevant_svgs, self.mock_get_svg_data)
        expected = ["file1.svg"]
        self.assertEqual(result, expected)

    def test_find_matching_svg_files_with_multiple_matches(self):
        """Test finding SVG files with multiple matching IDs"""
        # Add test-id-1 to file2.svg as well
        self.test_svg_content["file2.svg"]["content"] = '<g class="tkk" id="test-id-1">content</g>'

        result = find_matching_svg_files("test-id-1", self.relevant_svgs, self.mock_get_svg_data)
        expected = ["file1.svg", "file2.svg"]
        self.assertEqual(result, expected)

    def test_find_matching_svg_files_with_no_matches(self):
        """Test finding SVG files when no matches exist"""
        result = find_matching_svg_files(
            "nonexistent-id", self.relevant_svgs, self.mock_get_svg_data
        )
        self.assertEqual(result, [])

    def test_find_matching_svg_files_with_no_tkk_class(self):
        """Test that IDs without tkk class are not matched"""
        result = find_matching_svg_files("test-id-3", self.relevant_svgs, self.mock_get_svg_data)
        # file3.svg has test-id-3 but no tkk class, so should not match
        self.assertEqual(result, [])

    def test_find_matching_svg_files_with_empty_relevant_svgs(self):
        """Test with empty relevant SVG list"""
        result = find_matching_svg_files("test-id-1", [], self.mock_get_svg_data)
        self.assertEqual(result, [])

    def test_find_matching_svg_files_with_mixed_quote_styles(self):
        """Test matching IDs with different quote styles"""
        # Set up test content with single quotes
        self.test_svg_content["file2.svg"]["content"] = "<g id='test-id-1' class='tkk'>content</g>"

        result = find_matching_svg_files("test-id-1", self.relevant_svgs, self.mock_get_svg_data)
        expected = ["file1.svg", "file2.svg"]  # Both should match despite different quotes
        self.assertEqual(result, expected)

    def test_find_matching_svg_files_with_multiple_classes(self):
        """Test matching IDs in elements with multiple CSS classes"""
        # Set up test content with multiple classes including tkk
        self.test_svg_content["file3.svg"]["content"] = (
            '<g class="other-class tkk selected" id="test-id-1">content</g>'
        )

        result = find_matching_svg_files("test-id-1", self.relevant_svgs, self.mock_get_svg_data)
        expected = ["file1.svg", "file3.svg"]
        self.assertEqual(result, expected)

    @patch('utils.svg_utils.update_svg_id')
    def test_find_matching_svg_files_with_update_errors(self, mock_update_svg_id):
        """Test handling of update_svg_id errors"""
        # Mock update_svg_id to return error for file1.svg
        def mock_update_side_effect(content, _old_id, new_id):
            if "test-id-1" in content and new_id == "test":
                if "file1" in content:
                    return content, "Mock error"
                return content + "modified", None
            return content, None

        mock_update_svg_id.side_effect = mock_update_side_effect

        # Modify content to help distinguish files in the mock
        self.test_svg_content["file1.svg"]["content"] = (
            '<g class="tkk file1" id="test-id-1">content</g>'
        )
        self.test_svg_content["file2.svg"]["content"] = (
            '<g class="tkk file2" id="test-id-1">content</g>'
        )

        result = find_matching_svg_files("test-id-1", self.relevant_svgs, self.mock_get_svg_data)
        # Only file2.svg should match due to error in file1.svg
        expected = ["file2.svg"]
        self.assertEqual(result, expected)


@pytest.mark.unit
class TestFindRelevantSvgs(unittest.TestCase):
    """Test cases for the find_relevant_svg_files function"""

    def setUp(self):
        """Set up test fixtures"""
        self.all_svg_files = [
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
            "M145_other.svg"
        ]

    def test_find_relevant_svg_files_for_tf1(self):
        """Test getting SVGs for for TF1 entries"""
        result = find_relevant_svg_files("M_143_TF1", self.all_svg_files, "143")
        # Should only get Textfassung1 files, not Textfassung2
        expected = ["M143_Textfassung1-1von2-final.svg", "M143_Textfassung1-2von2-final.svg"]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_standard_for_tf2(self):
        """Test getting SVGs for TF2 entries"""
        result = find_relevant_svg_files("M_143_TF2", self.all_svg_files, "143")
        # Should only get Textfassung2 files
        expected = ["M143_Textfassung2-1von1-final.svg"]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_for_sk2(self):
        """Test getting SVGs for Sk2 entries"""
        result = find_relevant_svg_files("M_143_Sk2", self.all_svg_files, "143")
        # Should only get Sk2 files (not Sk2_1, Sk2_2, etc.)
        expected = [
            "M143_Sk2-1von3-final.svg",
            "M143_Sk2-2von3-final.svg",
            "M143_Sk2-3von3-final.svg"
        ]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_for_sk2_1(self):
        """Test getting SVGs for Sk2_1 entries (sub-numbered sketches)"""
        result = find_relevant_svg_files("M_143_Sk2_1", self.all_svg_files, "143")
        # Should only get Sk2_1 files
        expected = ["M143_Sk2_1-1von1-final.svg"]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_for_sk2_2(self):
        """Test getting SVGs for Sk2_2 entries"""
        result = find_relevant_svg_files("M_143_Sk2_2", self.all_svg_files, "143")
        # Should only get Sk2_2 files
        expected = ["M143_Sk2_2-1von1-final.svg"]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_for_sk2_1_1_1(self):
        """Test getting SVGs for Sk2_1_1_1 entries (sub-numbered sketches)"""
        result = find_relevant_svg_files("M_143_Sk2_1_1_1", self.all_svg_files, "143")
        # Should only get Sk2_1_1_1 files
        expected = ["M143_Sk2_1_1_1-1von1-final.svg"]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_for_sk1_exact_match(self):
        """Test that Sk1 only matches Sk1 files, not Sk10, Sk11, etc."""
        result = find_relevant_svg_files("M_143_Sk1", self.all_svg_files, "143")
        # Should only get Sk1 files, not Sk10, Sk11, Sk12
        expected = ["M143_Sk1-1von1-final.svg"]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_for_sk10_exact_match(self):
        """Test that Sk10 only matches Sk10 files, not Sk1 or other Sk1x files"""
        result = find_relevant_svg_files("M_143_Sk10", self.all_svg_files, "143")
        # Should only get Sk10 files
        expected = [
            "M143_Sk10-1von9-final.svg",
            "M143_Sk10-2von9-final.svg",
            "M143_Sk10-3von9-final.svg"
        ]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_for_sk11_exact_match(self):
        """Test that Sk11 only matches Sk11 files, not Sk1 or Sk1x files"""
        result = find_relevant_svg_files("M_143_Sk11", self.all_svg_files, "143")
        # Should only get Sk11 files
        expected = [
            "M143_Sk11-1von4-final.svg",
            "M143_Sk11-2von4-final.svg"
        ]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_for_sk12_exact_match(self):
        """Test that Sk12 only matches Sk12 files"""
        result = find_relevant_svg_files("M_143_Sk12", self.all_svg_files, "143")
        # Should only get Sk12 files
        expected = ["M143_Sk12-1von2-final.svg"]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_with_no_id_specified(self):
        """Test getting SVGs when no TF or Sk is specified.
        Should get all non-rowtable files.
        """
        result = find_relevant_svg_files("M_143", self.all_svg_files, "143")
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
            "M143_Sk2-3von3-final.svg"
        ]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_with_skrt(self):
        """Test getting SVGs for SkRT entries"""
        result = find_relevant_svg_files("SkRT", self.all_svg_files, "")
        expected = ["op25_C_Reihentabelle-1von1-final.svg"]
        self.assertEqual(result, expected)

    def test_find_relevant_svg_files_with_no_matches(self):
        """Test getting SVGs when no matches exist"""
        result = find_relevant_svg_files("M_999", self.all_svg_files, "999")
        self.assertEqual(result, [])

    def test_find_relevant_svg_files_with_empty_file_list(self):
        """Test with empty SVG file list"""
        result = find_relevant_svg_files("M_143", [], "143")
        self.assertEqual(result, [])


@pytest.mark.unit
class TestUpdateSvgId(unittest.TestCase):
    """Test cases for the update_svg_id function"""

    def test_update_svg_id_with_class_before_id(self):
        """Test updating SVG with class before id attribute"""
        svg_content = '<g class="tkk" id="old-id">content</g>'
        result, error = update_svg_id(svg_content, "old-id", "new-id")
        expected = '<g class="tkk" id="new-id">content</g>'
        self.assertEqual(result, expected)
        self.assertIsNone(error)

    def test_update_svg_id_with_id_before_class(self):
        """Test updating SVG with id before class attribute"""
        svg_content = '<g id="old-id" class="tkk">content</g>'
        result, error = update_svg_id(svg_content, "old-id", "new-id")
        expected = '<g id="new-id" class="tkk">content</g>'
        self.assertEqual(result, expected)
        self.assertIsNone(error)

    def test_update_svg_id_with_single_quotes(self):
        """Test updating SVG with single quotes"""
        svg_content = "<g class='tkk' id='old-id'>content</g>"
        result, error = update_svg_id(svg_content, "old-id", "new-id")
        expected = "<g class='tkk' id='new-id'>content</g>"
        self.assertEqual(result, expected)
        self.assertIsNone(error)

    def test_update_svg_id_with_no_class_tkk(self):
        """Test that IDs without class='tkk' are not updated"""
        svg_content = '<g class="other" id="old-id">content</g>'
        result, error = update_svg_id(svg_content, "old-id", "new-id")
        self.assertEqual(result, svg_content)  # Should remain unchanged
        self.assertIsNone(error)

    def test_update_svg_id_with_multiple_classes_tkk_first(self):
        """Test updating SVG with multiple classes where tkk is first"""
        svg_content = '<g class="tkk other-class" id="old-id">content</g>'
        result, error = update_svg_id(svg_content, "old-id", "new-id")
        expected = '<g class="tkk other-class" id="new-id">content</g>'
        self.assertEqual(result, expected)
        self.assertIsNone(error)

    def test_update_svg_id_with_multiple_classes_tkk_last(self):
        """Test updating SVG with multiple classes where tkk is last"""
        svg_content = '<g id="old-id" class="other-class tkk">content</g>'
        result, error = update_svg_id(svg_content, "old-id", "new-id")
        expected = '<g id="new-id" class="other-class tkk">content</g>'
        self.assertEqual(result, expected)
        self.assertIsNone(error)

    def test_update_svg_id_with_multiple_classes_tkk_middle(self):
        """Test updating SVG with multiple classes where tkk is in the middle"""
        svg_content = '<g class="active tkk selected" id="old-id">content</g>'
        result, error = update_svg_id(svg_content, "old-id", "new-id")
        expected = '<g class="active tkk selected" id="new-id">content</g>'
        self.assertEqual(result, expected)
        self.assertIsNone(error)

    def test_update_svg_id_with_partial_class_name_no_match(self):
        """Test that partial matches of 'tkk' in class names are not updated"""
        svg_content = '<g class="tkkish" id="old-id">content</g>'
        result, error = update_svg_id(svg_content, "old-id", "new-id")
        self.assertEqual(result, svg_content)  # Should remain unchanged
        self.assertIsNone(error)

    def test_update_svg_id_with_mixed_quotes_multiple_classes(self):
        """Test updating SVG with single quotes and multiple classes"""
        svg_content = "<g id='old-id' class='other-class tkk active'>content</g>"
        result, error = update_svg_id(svg_content, "old-id", "new-id")
        expected = "<g id='new-id' class='other-class tkk active'>content</g>"
        self.assertEqual(result, expected)
        self.assertIsNone(error)

    def test_update_svg_id_with_multiple_occurrences(self):
        """Test that multiple class='tkk' elements with same ID cause an error"""
        svg_content = '''<svg>
    <g class="tkk" id="old-id">content1</g>
    <g id="old-id" class="tkk other-class">content2</g>
    <g class="other" id="old-id">content3</g>
</svg>'''
        result, error = update_svg_id(svg_content, "old-id", "new-id")

        # Should return unchanged content and error message
        self.assertEqual(result, svg_content)
        self.assertIsNotNone(error)
        self.assertIn("Multiple class='tkk' elements found with ID 'old-id'", error)
        self.assertIn("2 occurrences", error)  # Should find 2 tkk elements


if __name__ == '__main__':
    unittest.main()

# ---- shared utility coverage: TKK + LinkBox ----
import inspect
import pytest
import utils.svg_utils as _svg_utils


def _invoke_with_required_class(fn, args, required_class):
    sig = inspect.signature(fn)
    for name in ("required_class", "class_name", "target_class"):
        if name in sig.parameters:
            return fn(*args, **{name: required_class})
    if len(sig.parameters) > len(args):
        return fn(*args, required_class)
    if required_class != "tkk":
        pytest.fail(f"{fn.__name__} must support class filtering for LinkBox.")
    return fn(*args)


@pytest.mark.parametrize("required_class", ["tkk", "link-box"], ids=["tkk", "linkbox"])
def test_shared_find_matching_svg_files_supports_tkk_and_linkbox(required_class):
    find_fn = getattr(_svg_utils, "find_matching_svg_files_by_class", None)
    if find_fn is None:
        find_fn = getattr(_svg_utils, "find_matching_svg_files")

    store = {
        "match.svg": {"content": f"<g id='old-id' class='x {required_class} y'></g>"},
        "skip.svg": {"content": "<g id='old-id' class='other'></g>"},
    }

    def _get_svg_data(name):
        return store[name]

    result = _invoke_with_required_class(
        find_fn,
        ("old-id", ["match.svg", "skip.svg"], _get_svg_data),
        required_class,
    )
    assert "match.svg" in result
    assert "skip.svg" not in result


@pytest.mark.parametrize("required_class", ["tkk", "link-box"], ids=["tkk", "linkbox"])
def test_shared_update_svg_id_supports_tkk_and_linkbox(required_class):
    update_fn = getattr(_svg_utils, "update_svg_id_by_class", None)
    if update_fn is None:
        update_fn = getattr(_svg_utils, "update_svg_id")

    source = f"<svg><g id='old-id' class='a {required_class} b'></g></svg>"
    result = _invoke_with_required_class(update_fn, (source, "old-id", "new-id"), required_class)
    updated = result[0] if isinstance(result, tuple) else result

    assert "new-id" in updated
    assert "old-id" not in updated
