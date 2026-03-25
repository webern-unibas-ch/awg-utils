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
import xml.etree.ElementTree as ET
import pytest

# Import the functions we want to test
from utils.svg_utils import (
    _find_elements_by_id_and_class,
    _parse_svg_xml,
    _serialize_svg_xml,
    find_matching_svg_files_by_class,
    find_relevant_svg_files,
    update_svg_id_by_class
)

# Global constants for test cases
LINKBOX_CLASS = "link-box"
TKK_CLASS = "tkk"


@pytest.mark.unit
class TestFindMatchingSvgFilesByClass(unittest.TestCase):
    """Test cases for the find_matching_svg_files_by_class function"""

    def setUp(self):
        """Set up test fixtures"""
        self.relevant_svgs = [
            "file1.svg",
            "file2.svg",
            "file3.svg",
            "file4.svg"
        ]
        self.test_svg_content = {
            "file1.svg": {"content": '<g class="tkk" id="test-id-1">content</g>'},
            "file2.svg": {"content": '<g id="test-id-2" class="tkk">content</g>'},
            "file3.svg": {"content": '<g class="other" id="test-id-3">content</g>'},
            "file4.svg": {"content": '<g class="link-box" id="test-id-4">content</g>'}
        }

    def mock_get_svg_data(self, filename):
        """Mock function to simulate get_svg_data"""
        return self.test_svg_content.get(filename, {"content": ""})

    def test_find_matching_svg_files_with_default_target_class(self):
        """Test default target class ('tkk') when argument is omitted"""
        result = find_matching_svg_files_by_class(
            "test-id-1", self.relevant_svgs, self.mock_get_svg_data
        )
        expected = ["file1.svg"]
        self.assertEqual(result, expected)

    def test_find_matching_svg_files_with_tkk_target_class(self):
        """Test finding SVG files with explicit target class 'tkk'"""
        result = find_matching_svg_files_by_class(
            "test-id-1", self.relevant_svgs, self.mock_get_svg_data, TKK_CLASS
        )
        expected = ["file1.svg"]
        self.assertEqual(result, expected)

    def test_find_matching_svg_files_with_link_box_target_class(self):
        """Test finding SVG files with target class 'link-box'"""
        result = find_matching_svg_files_by_class(
            "test-id-4", self.relevant_svgs, self.mock_get_svg_data, LINKBOX_CLASS
        )
        expected = ["file4.svg"]
        self.assertEqual(result, expected)

    def test_find_matching_svg_files_with_multiple_matches(self):
        """Test finding SVG files with multiple matching IDs"""
        # Add test-id-1 to file2.svg as well
        self.test_svg_content["file2.svg"]["content"] = '<g class="tkk" id="test-id-1">content</g>'

        result = find_matching_svg_files_by_class(
            "test-id-1", self.relevant_svgs, self.mock_get_svg_data, TKK_CLASS
        )
        expected = ["file1.svg", "file2.svg"]
        self.assertEqual(result, expected)

    def test_find_matching_svg_files_with_no_matches(self):
        """Test finding SVG files when no matches exist"""
        result = find_matching_svg_files_by_class(
            "non-existent-id", self.relevant_svgs, self.mock_get_svg_data, TKK_CLASS
        )
        self.assertEqual(result, [])

    def test_find_matching_svg_files_with_no_tkk_class(self):
        """Test that IDs without tkk class are not matched"""
        result = find_matching_svg_files_by_class(
            "test-id-3", self.relevant_svgs, self.mock_get_svg_data, TKK_CLASS
        )
        # file3.svg has test-id-3 but no tkk class, so should not match
        self.assertEqual(result, [])

    def test_find_matching_svg_files_with_empty_relevant_svgs(self):
        """Test with empty relevant SVG list"""
        result = find_matching_svg_files_by_class(
            "test-id-1", [], self.mock_get_svg_data, TKK_CLASS
        )
        self.assertEqual(result, [])

    def test_find_matching_svg_files_with_multiple_classes(self):
        """Test matching IDs in elements with multiple CSS classes"""
        # Set up test content with multiple classes including tkk
        self.test_svg_content["file3.svg"]["content"] = (
            '<g class="other-class tkk selected" id="test-id-1">content</g>'
        )

        result = find_matching_svg_files_by_class(
            "test-id-1", self.relevant_svgs, self.mock_get_svg_data, TKK_CLASS
        )
        expected = ["file1.svg", "file3.svg"]
        self.assertEqual(result, expected)

    def test_find_matching_svg_files_when_get_svg_data_returns_none(self):
        """Test that files with None svg_data are skipped"""
        def mock_get_svg_data_with_none(filename):
            if filename == "file2.svg":
                return None
            return self.test_svg_content.get(filename, {"content": ""})

        result = find_matching_svg_files_by_class(
            "test-id-1", self.relevant_svgs, mock_get_svg_data_with_none, TKK_CLASS
        )
        # file2.svg returns None and should be skipped
        expected = ["file1.svg"]
        self.assertEqual(result, expected)

    def test_find_matching_svg_files_when_get_svg_data_returns_empty_dict(self):
        """Test that files with empty dict are skipped"""
        def mock_get_svg_data_with_empty(filename):
            if filename == "file2.svg":
                return {}  # Empty dict, no content key
            return self.test_svg_content.get(filename, {"content": ""})

        result = find_matching_svg_files_by_class(
            "test-id-1", self.relevant_svgs, mock_get_svg_data_with_empty, TKK_CLASS
        )
        # file2.svg returns empty dict, should still be processed (content key missing gives "")
        # but it won't have matching IDs, so still only file1.svg
        expected = ["file1.svg"]
        self.assertEqual(result, expected)

    def test_find_matching_svg_files_when_svg_parsing_fails(self):
        """Test that files with invalid SVG XML are skipped gracefully"""
        def mock_get_svg_data_with_invalid_xml(filename):
            if filename == "file2.svg":
                return {"content": "<svg><g></svg>"}  # Mismatched tags - invalid XML
            return self.test_svg_content.get(filename, {"content": ""})

        result = find_matching_svg_files_by_class(
            "test-id-1", self.relevant_svgs, mock_get_svg_data_with_invalid_xml, TKK_CLASS
        )
        # file2.svg has invalid XML and should be skipped
        expected = ["file1.svg"]
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
class TestUpdateSvgIdByClass(unittest.TestCase):
    """Test cases for the update_svg_id_by_class function"""

    def test_update_svg_id_by_class_with_tkk_target_class(self):
        """Test basic ID update when element has matching class 'tkk'"""
        svg_content = '<svg><g class="tkk" id="old-id">content</g></svg>'
        result, error = update_svg_id_by_class(svg_content, "old-id", "new-id", TKK_CLASS)
        self.assertIsNone(error)
        self.assertIn('id="new-id"', result)
        self.assertNotIn('id="old-id"', result)

    def test_update_svg_id_by_class_with_link_box_target_class(self):
        """Test basic ID update when element has matching class 'link-box'"""
        svg_content = '<svg><g class="link-box" id="old-id">content</g></svg>'
        result, error = update_svg_id_by_class(svg_content, "old-id", "new-id", LINKBOX_CLASS)
        self.assertIsNone(error)
        self.assertIn('id="new-id"', result)
        self.assertNotIn('id="old-id"', result)

    def test_update_svg_id_by_class_with_no_matching_class(self):
        """Test that IDs without target class are not updated and return an error"""
        svg_content = '<g class="other" id="old-id">content</g>'
        result, error = update_svg_id_by_class(svg_content, "old-id", "new-id", TKK_CLASS)
        self.assertEqual(result, svg_content)  # Should remain unchanged
        self.assertIsNotNone(error)
        self.assertIn("'old-id' with class containing 'tkk' not found", error)

    def test_update_svg_id_by_class_with_multiple_classes(self):
        """Test matching target class regardless of position in class list"""
        test_cases = [
            '<g class="tkk other-class" id="old-id">content</g>',  # tkk first
            '<g class="other-class tkk" id="old-id">content</g>',    # tkk last
            '<g class="active tkk selected" id="old-id">content</g>'  # tkk middle
        ]
        for svg_content in test_cases:
            result, error = update_svg_id_by_class(svg_content, "old-id", "new-id", TKK_CLASS)
            self.assertIsNone(error)
            self.assertIn('id="new-id"', result)

    def test_update_svg_id_by_class_with_partial_class_name_no_match(self):
        """Test that partial matches of 'tkk' in class names are not updated"""
        svg_content = '<g class="tkkish" id="old-id">content</g>'
        result, error = update_svg_id_by_class(svg_content, "old-id", "new-id", TKK_CLASS)
        self.assertEqual(result, svg_content)  # Should remain unchanged
        self.assertIsNotNone(error)
        self.assertIn("'old-id' with class containing 'tkk' not found", error)

    def test_update_svg_id_by_class_normalizes_output_format(self):
        """Test that output uses normalized XML format (double quotes, proper spacing)"""
        # Input with single quotes
        svg_content = "<g id='old-id' class='tkk'>content</g>"
        result, error = update_svg_id_by_class(svg_content, "old-id", "new-id", TKK_CLASS)
        self.assertIsNone(error)
        # Output should have double quotes (normalized by serializer)
        self.assertIn('id="new-id"', result)
        self.assertIn('class="tkk"', result)

    def test_update_svg_id_by_class_with_multiple_occurrences(self):
        """Test that multiple class='tkk' elements with same ID cause an error"""
        svg_content = '''<svg>
    <g class="tkk" id="old-id">content1</g>
    <g id="old-id" class="tkk other-class">content2</g>
    <g class="other" id="old-id">content3</g>
</svg>'''
        result, error = update_svg_id_by_class(svg_content, "old-id", "new-id", TKK_CLASS)

        # Should return unchanged content and error message
        self.assertEqual(result, svg_content)
        self.assertIsNotNone(error)
        self.assertIn("Multiple class='tkk' elements found with ID 'old-id'", error)
        self.assertIn("2 occurrences", error)  # Should find 2 tkk elements

    def test_update_svg_id_by_class_preserves_xml_declaration_state(self):
        """Test that XML declaration presence is preserved from input"""
        # Input WITHOUT declaration
        svg_no_decl = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<g class="tkk" id="old-id">x</g></svg>'
        )
        result, error = update_svg_id_by_class(svg_no_decl, "old-id", "new-id", TKK_CLASS)
        self.assertIsNone(error)
        self.assertFalse(result.lstrip().startswith('<?xml'))
        self.assertIn('id="new-id"', result)

        # Input WITH declaration should preserve it in output
        svg_with_decl = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<g class="tkk" id="old-id">x</g></svg>'
        )
        result, error = update_svg_id_by_class(svg_with_decl, "old-id", "new-id", TKK_CLASS)
        self.assertIsNone(error)
        self.assertTrue(result.startswith('<?xml'))
        self.assertIn('id="new-id"', result)

    def test_update_svg_id_by_class_with_invalid_xml(self):
        """Test that invalid SVG XML is handled gracefully with error message"""
        # Mismatched tags - invalid XML
        svg_content = '<svg><g class="tkk" id="old-id">content</svg>'  # missing </g>
        result, error = update_svg_id_by_class(svg_content, "old-id", "new-id", TKK_CLASS)

        # Should return unchanged content and error message
        self.assertEqual(result, svg_content)
        self.assertIsNotNone(error)
        self.assertIn("XML parse error", error)


@pytest.mark.unit
class TestFindElementsByIdAndClass(unittest.TestCase):
    """Test cases for the _find_elements_by_id_and_class helper function"""

    def test_find_elements_with_matching_id_and_class_tkk(self):
        """Test finding element with matching ID and class 'tkk'"""
        svg_content = '<svg><g id="test-id" class="tkk">content</g></svg>'
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", TKK_CLASS)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get('id'), "test-id")

    def test_find_elements_with_matching_id_and_class_link_box(self):
        """Test finding element with matching ID and class 'link-box'"""
        svg_content = '<svg><g id="test-id" class="link-box">content</g></svg>'
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", LINKBOX_CLASS)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get('id'), "test-id")

    def test_find_elements_with_no_matching_id(self):
        """Test that no elements are found when ID doesn't match"""
        svg_content = '<svg><g id="other-id" class="tkk">content</g></svg>'
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", TKK_CLASS)
        self.assertEqual(result, [])

    def test_find_elements_with_no_matching_class(self):
        """Test that no elements are found when class doesn't match"""
        svg_content = '<svg><g id="test-id" class="other">content</g></svg>'
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", TKK_CLASS)
        self.assertEqual(result, [])

    def test_find_elements_with_multiple_matching_elements(self):
        """Test finding multiple elements with matching ID and class"""
        svg_content = '''<svg>
    <g id="test-id" class="tkk">content1</g>
    <g id="test-id" class="tkk">content2</g>
    <g id="test-id" class="other">content3</g>
</svg>'''
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", TKK_CLASS)
        self.assertEqual(len(result), 2)
        for elem in result:
            self.assertEqual(elem.get('id'), "test-id")
            self.assertIn("tkk", elem.get('class', '').split())

    def test_find_elements_with_multiple_classes_target_at_start(self):
        """Test class matching when target class is first in list"""
        svg_content = '<svg><g id="test-id" class="tkk other">content</g></svg>'
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", TKK_CLASS)
        self.assertEqual(len(result), 1)

    def test_find_elements_with_multiple_classes_target_at_end(self):
        """Test class matching when target class is last in list"""
        svg_content = '<svg><g id="test-id" class="other tkk">content</g></svg>'
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", TKK_CLASS)
        self.assertEqual(len(result), 1)

    def test_find_elements_with_multiple_classes_target_in_middle(self):
        """Test class matching when target class is in middle"""
        svg_content = '<svg><g id="test-id" class="first tkk last">content</g></svg>'
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", TKK_CLASS)
        self.assertEqual(len(result), 1)

    def test_find_elements_partial_class_name_no_match(self):
        """Test that partial class matches don't match"""
        svg_content = '<svg><g id="test-id" class="tkkish">content</g></svg>'
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", TKK_CLASS)
        self.assertEqual(result, [])

    def test_find_elements_with_no_class_attribute(self):
        """Test that elements without class attribute don't match"""
        svg_content = '<svg><g id="test-id">content</g></svg>'
        root, _ = _parse_svg_xml(svg_content)
        result = _find_elements_by_id_and_class(root, "test-id", TKK_CLASS)
        self.assertEqual(result, [])


@pytest.mark.unit
class TestSerializeSvgXML(unittest.TestCase):
    """Test cases for the _serialize_svg_xml helper."""

    def test_serialize_svg_xml_with_xml_declaration_and_newline(self):
        """Test that serialized SVG includes declaration and EOF newline by default."""
        root = ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg"><g/></svg>')

        result = _serialize_svg_xml(root)

        self.assertTrue(result.startswith('<?xml version="1.0" encoding="UTF-8"?>'))
        self.assertTrue(result.endswith('\n'))

    def test_serialize_svg_xml_without_xml_declaration(self):
        """Test that serialized SVG omits XML declaration when not requested."""
        root = ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg"><g/></svg>')

        result = _serialize_svg_xml(root, include_xml_declaration=False)

        self.assertFalse(result.lstrip().startswith('<?xml'))
        self.assertTrue(result.endswith('\n'))

    def test_serialize_svg_xml_normalizes_declaration_quotes_and_encoding_case(self):
        """Test that XML declaration uses double quotes and UTF-8 casing."""
        root = ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg"><g/></svg>')

        result = _serialize_svg_xml(root)

        declaration = result.split('?>', 1)[0] + '?>'
        self.assertIn('version="1.0"', declaration)
        self.assertIn('encoding="UTF-8"', declaration)
        self.assertNotIn("'", declaration)

    def test_serialize_svg_xml_removes_whitespace_before_self_closing_tags(self):
        """Test that self-closing tags do not have a space before '/>'."""
        root = ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg"><g /></svg>')

        result = _serialize_svg_xml(root)

        self.assertNotIn(' />', result)


@pytest.mark.unit
class TestParseSvgXML(unittest.TestCase):
    """Test cases for the _parse_svg_xml helper."""

    def test_parse_svg_xml_valid_xml_returns_root_and_no_error(self):
        """Test that valid SVG returns a root element and no error."""
        svg_content = '<svg xmlns="http://www.w3.org/2000/svg"><g/></svg>'

        root, error = _parse_svg_xml(svg_content)

        self.assertIsNotNone(root)
        self.assertIsNone(error)
        self.assertTrue(root.tag.endswith('svg'))

    def test_parse_svg_xml_invalid_xml_returns_error(self):
        """Test that invalid XML returns no root and a parse error message."""
        svg_content = '<svg><g></svg>'

        root, error = _parse_svg_xml(svg_content)

        self.assertIsNone(root)
        self.assertIsNotNone(error)
        self.assertTrue(error.startswith('XML parse error:'))

    def test_parse_svg_xml_with_declaration_and_leading_whitespace(self):
        """Test that declaration after leading whitespace is rejected."""
        svg_content = (
            ' \n\t<?xml version="1.0" encoding="UTF-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg"><g/></svg>'
        )

        root, error = _parse_svg_xml(svg_content)

        self.assertIsNone(root)
        self.assertIsNotNone(error)
        self.assertTrue(error.startswith('XML parse error:'))


if __name__ == '__main__':
    unittest.main()
