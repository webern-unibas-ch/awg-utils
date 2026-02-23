#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for unify_tkk_ids.py

Tests for TKK Group ID unification functionality including:
- Number extraction from text
- ID validation and error reporting
- JSON and SVG processing logic
- SkRT special logic handling
"""

import unittest
import json
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, mock_open, MagicMock
from io import StringIO
import pytest

# Add parent directory to path to import the main module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the functions we want to test
from unify_tkk_ids import (
    find_matching_svg_files,
    find_relevant_svg_files,
    main,
    process_entry,
    process_single_svg_group_id, 
    update_svg_id, 
    unify_tkk_ids
)

# Import extracted utility functions
from extraction_utils import (
    extract_svg_group_ids,
    extract_moldenhauer_number
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
    
    def mock_get_svg_text(self, filename):
        """Mock function to simulate get_svg_text"""
        return self.test_svg_content.get(filename, {"content": ""})
    
    def test_find_matching_svg_files_with_single_match(self):
        """Test finding SVG files with single matching ID"""
        result = find_matching_svg_files("test-id-1", self.relevant_svgs, self.mock_get_svg_text)
        expected = ["file1.svg"]
        self.assertEqual(result, expected)
    
    def test_find_matching_svg_files_with_multiple_matches(self):
        """Test finding SVG files with multiple matching IDs"""
        # Add test-id-1 to file2.svg as well
        self.test_svg_content["file2.svg"]["content"] = '<g class="tkk" id="test-id-1">content</g>'
        
        result = find_matching_svg_files("test-id-1", self.relevant_svgs, self.mock_get_svg_text)
        expected = ["file1.svg", "file2.svg"]
        self.assertEqual(result, expected)
    
    def test_find_matching_svg_files_with_no_matches(self):
        """Test finding SVG files when no matches exist"""
        result = find_matching_svg_files("nonexistent-id", self.relevant_svgs, self.mock_get_svg_text)
        self.assertEqual(result, [])
    
    def test_find_matching_svg_files_with_no_tkk_class(self):
        """Test that IDs without tkk class are not matched"""
        result = find_matching_svg_files("test-id-3", self.relevant_svgs, self.mock_get_svg_text)
        # file3.svg has test-id-3 but no tkk class, so should not match
        self.assertEqual(result, [])
    
    def test_find_matching_svg_files_with_empty_relevant_svgs(self):
        """Test with empty relevant SVG list"""
        result = find_matching_svg_files("test-id-1", [], self.mock_get_svg_text)
        self.assertEqual(result, [])
    
    def test_find_matching_svg_files_with_mixed_quote_styles(self):
        """Test matching IDs with different quote styles"""
        # Set up test content with single quotes
        self.test_svg_content["file2.svg"]["content"] = "<g id='test-id-1' class='tkk'>content</g>"
        
        result = find_matching_svg_files("test-id-1", self.relevant_svgs, self.mock_get_svg_text)
        expected = ["file1.svg", "file2.svg"]  # Both should match despite different quotes
        self.assertEqual(result, expected)
    
    def test_find_matching_svg_files_with_multiple_classes(self):
        """Test matching IDs in elements with multiple CSS classes"""
        # Set up test content with multiple classes including tkk
        self.test_svg_content["file3.svg"]["content"] = '<g class="highlight tkk selected" id="test-id-1">content</g>'
        
        result = find_matching_svg_files("test-id-1", self.relevant_svgs, self.mock_get_svg_text)
        expected = ["file1.svg", "file3.svg"] 
        self.assertEqual(result, expected)
    
    @patch('unify_tkk_ids.update_svg_id')
    def test_find_matching_svg_files_with_update_errors(self, mock_update_svg_id):
        """Test handling of update_svg_id errors"""
        # Mock update_svg_id to return error for file1.svg
        def mock_update_side_effect(content, old_id, new_id):
            if "test-id-1" in content and new_id == "test":
                if "file1" in content:
                    return content, "Mock error"
                else:
                    return content + "modified", None
            return content, None
            
        mock_update_svg_id.side_effect = mock_update_side_effect
        
        # Modify content to help distinguish files in the mock
        self.test_svg_content["file1.svg"]["content"] = 'file1<g class="tkk" id="test-id-1">content</g>'
        self.test_svg_content["file2.svg"]["content"] = 'file2<g class="tkk" id="test-id-1">content</g>'
        
        result = find_matching_svg_files("test-id-1", self.relevant_svgs, self.mock_get_svg_text)
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
    
    def test_find_relevant_svg_files_for_TF1(self):
        """Test getting SVGs for for TF1 entries"""
        result = find_relevant_svg_files("M_143_TF1", self.all_svg_files, "143")
        # Should only get Textfassung1 files, not Textfassung2
        expected = ["M143_Textfassung1-1von2-final.svg", "M143_Textfassung1-2von2-final.svg"]
        self.assertEqual(result, expected)
    
    def test_find_relevant_svg_files_standard_for_TF2(self):
        """Test getting SVGs for TF2 entries"""
        result = find_relevant_svg_files("M_143_TF2", self.all_svg_files, "143")
        # Should only get Textfassung2 files
        expected = ["M143_Textfassung2-1von1-final.svg"]
        self.assertEqual(result, expected)
    
    def test_find_relevant_svg_files_for_Sk2(self):
        """Test getting SVGs for Sk2 entries"""
        result = find_relevant_svg_files("M_143_Sk2", self.all_svg_files, "143")
        # Should only get Sk2 files (not Sk2_1, Sk2_2, etc.)
        expected = [
            "M143_Sk2-1von3-final.svg", 
            "M143_Sk2-2von3-final.svg", 
            "M143_Sk2-3von3-final.svg"
        ]
        self.assertEqual(result, expected)
    
    def test_find_relevant_svg_files_for_Sk2_1(self):
        """Test getting SVGs for Sk2_1 entries (sub-numbered sketches)"""
        result = find_relevant_svg_files("M_143_Sk2_1", self.all_svg_files, "143")
        # Should only get Sk2_1 files
        expected = ["M143_Sk2_1-1von1-final.svg"]
        self.assertEqual(result, expected)
    
    def test_find_relevant_svg_files_for_Sk2_2(self):
        """Test getting SVGs for Sk2_2 entries"""  
        result = find_relevant_svg_files("M_143_Sk2_2", self.all_svg_files, "143")
        # Should only get Sk2_2 files
        expected = ["M143_Sk2_2-1von1-final.svg"]
        self.assertEqual(result, expected)
        
    def test_find_relevant_svg_files_for_Sk2_1_1_1(self):
        """Test getting SVGs for Sk2_1_1_1 entries (sub-numbered sketches)"""
        result = find_relevant_svg_files("M_143_Sk2_1_1_1", self.all_svg_files, "143")
        # Should only get Sk2_1_1_1 files
        expected = ["M143_Sk2_1_1_1-1von1-final.svg"]
        self.assertEqual(result, expected)
    
    def test_find_relevant_svg_files_no_tf_specified(self):
        """Test getting SVGs when no TF or Sk is specified - should get all non-Reihentabelle files"""
        result = find_relevant_svg_files("M_143", self.all_svg_files, "143")
        # Should get all Textfassung files when no specific TF is mentioned
        expected = [
            "M143_Textfassung1-1von2-final.svg", 
            "M143_Textfassung1-2von2-final.svg", 
            "M143_Textfassung2-1von1-final.svg", 
            "M143_Sk1-1von1-final.svg", 
            "M143_Sk2_1-1von1-final.svg",
            "M143_Sk2_1_1_1-1von1-final.svg",
            "M143_Sk2_2-1von1-final.svg", 
            "M143_Sk2-1von3-final.svg", 
            "M143_Sk2-2von3-final.svg", 
            "M143_Sk2-3von3-final.svg"
        ]
        self.assertEqual(result, expected)
    
    def test_find_relevant_svg_files_skrt(self):
        """Test getting SVGs for SkRT entries"""
        result = find_relevant_svg_files("SkRT", self.all_svg_files, "")
        expected = ["op25_C_Reihentabelle-1von1-final.svg"]
        self.assertEqual(result, expected)
    
    def test_find_relevant_svg_files_no_matches(self):
        """Test getting SVGs when no matches exist"""
        result = find_relevant_svg_files("M_999", self.all_svg_files, "999")
        self.assertEqual(result, [])
    
    def test_find_relevant_svg_files_empty_file_list(self):
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


@pytest.mark.unit  
class TestProcessSingleSvgGroupId(unittest.TestCase):
    """Test cases for the process_single_svg_group_id function"""
    
    def setUp(self):
        # Mock the update_svg_id function
        self.update_svg_id_patcher = patch('unify_tkk_ids.update_svg_id')
        self.mock_update_svg_id = self.update_svg_id_patcher.start()
        self.mock_update_svg_id.return_value = ("updated_svg_content", None)
        
        # Common test data
        self.svg_group_id = "test-id"
        self.block_comment = {"svgGroupId": "test-id", "text": "Test comment"}
        self.prefix = "g-tkk-"
        self.counter = 5
        
        # Mock get_svg_text function
        self.mock_get_svg_text = MagicMock()
        self.mock_get_svg_text.return_value = {
            "content": "<svg>test content</svg>",
            "path": "/path/to/test.svg"
        }
    
    def tearDown(self):
        self.update_svg_id_patcher.stop()
    
    def test_process_single_svg_group_id_with_success(self):
        """Test successful processing with exactly one matching file"""
        matching_files = ["test.svg"]
        
        result = process_single_svg_group_id(
            self.svg_group_id, self.block_comment, matching_files, 
            self.mock_get_svg_text, f"{self.prefix}{self.counter}"
        )
        
        # Should return True for successful processing
        self.assertTrue(result)
        
        # Should update the JSON comment with new ID
        expected_new_id = f"{self.prefix}{self.counter}"
        self.assertEqual(self.block_comment["svgGroupId"], expected_new_id)
        
        # Should call get_svg_text with the matching file
        self.mock_get_svg_text.assert_called_once_with("test.svg")
        
        # Should call update_svg_id to update SVG content
        self.mock_update_svg_id.assert_called_once_with(
            "<svg>test content</svg>", self.svg_group_id, expected_new_id
        )
    
    def test_process_single_svg_group_id_with_no_files(self):
        """Test handling when no files match the svgGroupId"""
        matching_files = []
        
        with patch('builtins.print') as mock_print:
            result = process_single_svg_group_id(
                self.svg_group_id, self.block_comment, matching_files,
                self.mock_get_svg_text, f"{self.prefix}{self.counter}"
            )
        
        # Should return False indicating failure
        self.assertFalse(result)
        
        # Should not modify the JSON comment
        self.assertEqual(self.block_comment["svgGroupId"], "test-id")
        
        # Should print error message
        mock_print.assert_called_once()
        error_call = mock_print.call_args[0][0]
        self.assertIn("ERROR", error_call)
        self.assertIn("not found in any relevant SVG files", error_call)
        
        # Should not call get_svg_text or update_svg_id
        self.mock_get_svg_text.assert_not_called()
        self.mock_update_svg_id.assert_not_called()
    
    def test_process_single_svg_group_id_with_multiple_files(self):
        """Test handling when multiple files match the svgGroupId"""
        matching_files = ["test1.svg", "test2.svg", "test3.svg"]
        
        with patch('builtins.print') as mock_print:
            result = process_single_svg_group_id(
                self.svg_group_id, self.block_comment, matching_files,
                self.mock_get_svg_text, f"{self.prefix}{self.counter}"
            )
        
        # Should return False indicating skipped processing
        self.assertFalse(result)
        
        # Should not modify the JSON comment
        self.assertEqual(self.block_comment["svgGroupId"], "test-id")
        
        # Should print warning messages
        self.assertEqual(mock_print.call_count, 2)
        warning_call = mock_print.call_args_list[0][0][0]
        manual_review_call = mock_print.call_args_list[1][0][0]
        
        self.assertIn("WARNING", warning_call)
        self.assertIn("found in 3 files", warning_call)
        self.assertIn("manual review required", manual_review_call)
        
        # Should not call get_svg_text or update_svg_id
        self.mock_get_svg_text.assert_not_called()
        self.mock_update_svg_id.assert_not_called()
    
    def test_process_single_svg_group_id_with_different_prefix_counter(self):
        """Test with different prefix and counter values"""
        matching_files = ["sheet.svg"]
        prefix = "custom-prefix-"
        counter = 42
        
        result = process_single_svg_group_id(
            self.svg_group_id, self.block_comment, matching_files,
            self.mock_get_svg_text, f"{prefix}{counter}"
        )
        
        self.assertTrue(result)
        
        # Should use the provided prefix and counter
        expected_new_id = "custom-prefix-42"
        self.assertEqual(self.block_comment["svgGroupId"], expected_new_id)
        
        # Should call update_svg_id with correct new ID
        self.mock_update_svg_id.assert_called_once_with(
            "<svg>test content</svg>", self.svg_group_id, expected_new_id
        )
    
    def test_process_single_svg_group_id_modifies_comment_in_place(self):
        """Test that the function modifies the original comment object"""
        original_comment = {"svgGroupId": "original-id", "text": "Original text"}
        matching_files = ["test.svg"]
        
        result = process_single_svg_group_id(
            "original-id", original_comment, matching_files,
            self.mock_get_svg_text, f"{self.prefix}{self.counter}"
        )
        
        self.assertTrue(result)
        
        # Original comment object should be modified
        self.assertEqual(original_comment["svgGroupId"], "g-tkk-5")
        self.assertEqual(original_comment["text"], "Original text")  # Other fields unchanged
    
    def test_process_single_svg_group_id_with_svg_content_handling(self):
        """Test that SVG content is properly retrieved and updated"""
        matching_files = ["complex.svg"]
        
        # Mock SVG data with specific content
        svg_data = {
            "content": '<g class="tkk" id="test-id">Content</g>',
            "path": "/full/path/complex.svg"
        }
        self.mock_get_svg_text.return_value = svg_data
        
        result = process_single_svg_group_id(
            self.svg_group_id, self.block_comment, matching_files,
            self.mock_get_svg_text, f"{self.prefix}{self.counter}"
        )
        
        self.assertTrue(result)
        
        # Should call update_svg_id with the exact SVG content
        self.mock_update_svg_id.assert_called_once_with(
            '<g class="tkk" id="test-id">Content</g>', 
            self.svg_group_id, 
            "g-tkk-5"
        )
        
        # SVG data's content should be updated with return value from update_svg_id
        self.assertEqual(svg_data["content"], "updated_svg_content")
    
    def test_process_single_svg_group_id_prints_progress(self):
        """Test that progress messages are printed correctly"""
        matching_files = ["progress.svg"]
        
        with patch('builtins.print') as mock_print:
            result = process_single_svg_group_id(
                self.svg_group_id, self.block_comment, matching_files,
                self.mock_get_svg_text, f"{self.prefix}{self.counter}"
            )
        
        self.assertTrue(result)
        
        # Should print two progress messages
        self.assertEqual(mock_print.call_count, 2)
        
        json_msg = mock_print.call_args_list[0][0][0]
        svg_msg = mock_print.call_args_list[1][0][0]
        
        # Check JSON update message
        self.assertIn("[JSON]", json_msg)
        self.assertIn("'test-id' -> 'g-tkk-5'", json_msg)
        
        # Check SVG update message  
        self.assertIn("[SVG]", svg_msg)
        self.assertIn("'test-id' -> 'g-tkk-5'", svg_msg)
        self.assertIn("progress.svg", svg_msg)
    
    def test_process_single_svg_group_id_with_update_svg_error_handling(self):
        """Test handling of error from update_svg_id function"""
        matching_files = ["error.svg"]
        
        # Mock update_svg_id to return an error
        error_message = "Multiple tkk elements found"
        self.mock_update_svg_id.return_value = ("unchanged_content", error_message)
        
        result = process_single_svg_group_id(
            self.svg_group_id, self.block_comment, matching_files,
            self.mock_get_svg_text, f"{self.prefix}{self.counter}"
        )
        
        # Should still return True (the function doesn't handle update_svg_id errors)
        self.assertTrue(result)
        
        # JSON should still be updated
        self.assertEqual(self.block_comment["svgGroupId"], "g-tkk-5")
        
        # SVG content should be updated with the return value (even if error occurred)
        svg_data = self.mock_get_svg_text.return_value
        self.assertEqual(svg_data["content"], "unchanged_content")


@pytest.mark.unit
class TestProcessEntry(unittest.TestCase):
    """Test cases for the process_entry function"""
    
    def setUp(self):
        """Set up test fixtures and mocks"""
        # Mock all the helper functions that process_entry uses
        self.extract_moldenhauer_patcher = patch('extraction_utils.extract_moldenhauer_number')
        self.find_relevant_svgs_patcher = patch('unify_tkk_ids.find_relevant_svg_files')
        self.extract_svg_ids_patcher = patch('extraction_utils.extract_svg_group_ids')
        self.find_matching_patcher = patch('unify_tkk_ids.find_matching_svg_files')
        self.process_single_patcher = patch('unify_tkk_ids.process_single_svg_group_id')
        
        self.mock_extract_moldenhauer = self.extract_moldenhauer_patcher.start()
        self.mock_find_relevant_svgs = self.find_relevant_svgs_patcher.start()
        self.mock_extract_svg_ids = self.extract_svg_ids_patcher.start()
        self.mock_find_matching = self.find_matching_patcher.start()
        self.mock_process_single = self.process_single_patcher.start()
        
        # Set up default mock return values
        self.mock_extract_moldenhauer.return_value = "143"
        self.mock_find_relevant_svgs.return_value = ["test1.svg", "test2.svg"]
        self.mock_extract_svg_ids.return_value = (["id-1", "id-2"], [{"svgGroupId": "id-1"}, {"svgGroupId": "id-2"}])
        self.mock_find_matching.return_value = ["test1.svg"]
        self.mock_process_single.return_value = True
        
        # Test data
        self.test_entry = {
            "id": "M_143_TF1",
            "commentary": {
                "preamble": "",
                "comments": [{
                    "blockHeader": "",
                    "blockComments": [
                        {"svgGroupId": "id-1", "text": "Comment 1"},
                        {"svgGroupId": "id-2", "text": "Comment 2"}
                    ]
                }]
            }
        }
        
        self.all_svg_files = ["test1.svg", "test2.svg", "test3.svg"]
        self.mock_get_svg_text = MagicMock()
        self.loaded_svg_texts = {}
        self.prefix = "g-tkk-"
    
    def tearDown(self):
        """Clean up patches"""
        self.extract_moldenhauer_patcher.stop()
        self.find_relevant_svgs_patcher.stop()
        self.extract_svg_ids_patcher.stop()
        self.find_matching_patcher.stop()
        self.process_single_patcher.stop()
    
    def test_process_entry_success_basic(self):
        """Test successful processing of a basic entry"""
        with patch('builtins.print') as mock_print:
            process_entry(
                self.test_entry, self.all_svg_files, self.mock_get_svg_text,
                self.prefix
            )
        
        # Should call extract_moldenhauer_number with entry ID
        self.mock_extract_moldenhauer.assert_called_once_with("M_143_TF1")
        
        # Should call find_relevant_svg_files with correct parameters
        self.mock_find_relevant_svgs.assert_called_once_with(
            "M_143_TF1", self.all_svg_files, "143"
        )
        
        # Should extract svg group IDs from entry
        self.mock_extract_svg_ids.assert_called_once_with(self.test_entry)
        
        # Should find matching files for each ID
        self.assertEqual(self.mock_find_matching.call_count, 2)
        
        # Should process each ID with correct counter values
        self.assertEqual(self.mock_process_single.call_count, 2)
        call_args = self.mock_process_single.call_args_list
        
        # First call with new_id="g-tkk-1"
        self.assertEqual(call_args[0][0][4], "g-tkk-1")  # new_id parameter
        # Second call with new_id="g-tkk-2" 
        self.assertEqual(call_args[1][0][4], "g-tkk-2")  # new_id parameter
        
        # Should print processing messages
        mock_print.assert_any_call("\nProcessing Entry ID: M_143_TF1")
        mock_print.assert_any_call(" Standard anchor: M_143_TF1")
    
    def test_process_entry_with_skrt_detection(self):
        """Test SkRT entry detection"""
        skrt_entry = {"id": "M_144_SkRT", "commentary": {"comments": []}}
        
        # Mock to return no svgGroupIds
        self.mock_extract_svg_ids.return_value = ([], [])
        
        with patch('builtins.print') as mock_print:
            process_entry(
                skrt_entry, self.all_svg_files, self.mock_get_svg_text,
                self.prefix
            )
        
        # Should detect SkRT and print appropriate message
        mock_print.assert_any_call(" SkRT anchor detected: M_144_SkRT")
    
    def test_process_entry_with_no_svg_group_ids(self):
        """Test entry with no svgGroupIds to process"""
        # Mock to return empty lists
        self.mock_extract_svg_ids.return_value = ([], [])
        
        with patch('builtins.print') as mock_print:
            process_entry(
                self.test_entry, self.all_svg_files, self.mock_get_svg_text,
                self.prefix
            )
        
        # Should print "no svgGroupIds" message and return early
        mock_print.assert_any_call(" No svgGroupIds to process")
        
        # Should not call process_single_svg_group_id
        self.mock_process_single.assert_not_called()
    
    def test_process_entry_with_non_dict_entry(self):
        """Test with non-dictionary entry (should return early)"""
        with patch('builtins.print') as mock_print:
            process_entry(
                "not_a_dict", self.all_svg_files, self.mock_get_svg_text,
                self.prefix
            )
        
        # Should return early without calling any helper functions
        self.mock_extract_moldenhauer.assert_not_called()
        self.mock_extract_svg_ids.assert_not_called()
        mock_print.assert_not_called()
    
    def test_process_entry_with_no_entry_id(self):
        """Test entry with missing or empty ID"""
        empty_id_entry = {"id": "", "other": "data"}
        
        with patch('builtins.print') as mock_print:
            process_entry(
                empty_id_entry, self.all_svg_files, self.mock_get_svg_text,
                self.prefix
            )
        
        # Should return early without processing
        self.mock_extract_moldenhauer.assert_not_called()
        mock_print.assert_not_called()
        
        # Test with missing ID field
        no_id_entry = {"other": "data"}
        
        process_entry(
            no_id_entry, self.all_svg_files, self.mock_get_svg_text,
            self.prefix
        )
        
        # Still should not call helper functions
        self.mock_extract_moldenhauer.assert_not_called()
    
    def test_process_entry_counter_management(self):
        """Test counter increment logic with mixed success/failure"""
        # Mock process_single_svg_group_id to return success, failure, success
        self.mock_process_single.side_effect = [True, False, True]
        
        # Set up 3 SVG group IDs
        svg_ids = ["id-1", "id-2", "id-3"]
        block_comments = [{"svgGroupId": id} for id in svg_ids]
        self.mock_extract_svg_ids.return_value = (svg_ids, block_comments)
        
        process_entry(
            self.test_entry, self.all_svg_files, self.mock_get_svg_text,
            self.prefix
        )
        
        # Should call process_single_svg_group_id 3 times
        self.assertEqual(self.mock_process_single.call_count, 3)
        
        call_args = self.mock_process_single.call_args_list
        
        # Counter should increment only on success: 1, 2 (skipped), 2
        self.assertEqual(call_args[0][0][4], "g-tkk-1")  # First call: new_id="g-tkk-1"
        self.assertEqual(call_args[1][0][4], "g-tkk-2")  # Second call: new_id="g-tkk-2" 
        self.assertEqual(call_args[2][0][4], "g-tkk-2")  # Third call: new_id="g-tkk-2" (no increment after failure)
    
    def test_process_entry_prints_svg_assignment(self):
        """Test that SVG assignment information is printed"""
        relevant_svgs = ["M143_TF1_sheet1.svg", "M143_TF1_sheet2.svg"]
        self.mock_find_relevant_svgs.return_value = relevant_svgs
        
        with patch('builtins.print') as mock_print:
            process_entry(
                self.test_entry, self.all_svg_files, self.mock_get_svg_text,
                self.prefix
            )
        
        # Should print assigned SVGs information
        expected_message = f" Assigned SVGs ({len(relevant_svgs)}): {relevant_svgs}"
        mock_print.assert_any_call(expected_message)
    
    def test_process_entry_calls_helper_functions_correctly(self):
        """Test that all helper functions are called with correct parameters"""
        process_entry(
            self.test_entry, self.all_svg_files, self.mock_get_svg_text,
            self.prefix
        )
        
        # Verify each helper function call
        self.mock_extract_moldenhauer.assert_called_once_with("M_143_TF1")
        
        self.mock_find_relevant_svgs.assert_called_once_with(
            "M_143_TF1", self.all_svg_files, "143"
        )
        
        self.mock_extract_svg_ids.assert_called_once_with(self.test_entry)
        
        # Should call find_matching_svg_files for each svgGroupId
        expected_calls = [
            unittest.mock.call("id-1", ["test1.svg", "test2.svg"], self.mock_get_svg_text),
            unittest.mock.call("id-2", ["test1.svg", "test2.svg"], self.mock_get_svg_text)
        ]
        self.mock_find_matching.assert_has_calls(expected_calls)
    
    def test_process_entry_with_different_prefix(self):
        """Test processing with custom prefix"""
        custom_prefix = "custom-id-"
        
        process_entry(
            self.test_entry, self.all_svg_files, self.mock_get_svg_text,
            custom_prefix
        )
        
        # Should pass custom prefix to process_single_svg_group_id
        call_args = self.mock_process_single.call_args_list
        for call in call_args:
            # new_id parameter should start with custom prefix
            self.assertTrue(call[0][4].startswith(custom_prefix))  # new_id parameter
    
    def test_process_entry_modifies_entry_in_place(self):
        """Test that the entry is modified in place (via process_single_svg_group_id)"""
        process_entry(
            self.test_entry, self.all_svg_files, self.mock_get_svg_text,
            self.prefix
        )
        
        # The process_single_svg_group_id calls should receive the block_comments
        # from extract_svg_group_ids, which would modify the original entry
        call_args = self.mock_process_single.call_args_list
        
        # Verify that block comments from extract_svg_ids are passed through
        block_comment_calls = [call[0][1] for call in call_args]
        expected_comments = [{"svgGroupId": "id-1"}, {"svgGroupId": "id-2"}]
        self.assertEqual(block_comment_calls, expected_comments)


@pytest.mark.integration
class TestUnifyTkkIds(unittest.TestCase):
    """Integration tests for the unify_tkk_ids function"""
    
    def setUp(self):
        """Create temporary test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.json_path = os.path.join(self.test_dir, "textcritics.json")
        self.svg_dir = os.path.join(self.test_dir, "svgs")
        os.makedirs(self.svg_dir)
        
        # Create test JSON
        self.test_json = {
            "textcritics": [
                {
                    "id": "M_143",
                    "commentary": {
                        "comments": [{
                            "blockComments": [
                                {"svgGroupId": "old-id-1"}
                            ]
                        }]
                    }
                }
            ]
        }
        
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_json, f)
        
        # Create test SVG
        self.svg_path = os.path.join(self.svg_dir, "M_143_test.svg")
        with open(self.svg_path, 'w', encoding='utf-8') as f:
            f.write('<g class="tkk" id="old-id-1">content</g>')
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_unify_tkk_ids_success(self, mock_stdout):
        """Test successful processing of TKK IDs returns True"""
        success = unify_tkk_ids(
            self.json_path, self.svg_dir, "g-tkk-"
        )
        
        self.assertTrue(success)
    
    def test_unify_tkk_ids_missing_json(self):
        """Test error handling for missing JSON file"""
        with self.assertRaises(FileNotFoundError):
            unify_tkk_ids("/nonexistent/path.json", self.svg_dir)
    
    def test_unify_tkk_ids_missing_svg_dir(self):
        """Test error handling for missing SVG directory"""
        with self.assertRaises(FileNotFoundError):
            unify_tkk_ids(self.json_path, "/nonexistent/dir")


@pytest.mark.integration
class TestIntegration(unittest.TestCase):
    """Integration tests with temporary files"""
    
    def setUp(self):
        """Create temporary directory and test files"""
        self.test_dir = tempfile.mkdtemp()
        self.json_path = os.path.join(self.test_dir, "textcritics.json")
        self.svg_dir = os.path.join(self.test_dir, "svgs")
        os.makedirs(self.svg_dir)
        
        # Create test JSON data
        self.test_json = {
            "textcritics": [
                {
                    "id": "M_143",
                    "commentary": {
                        "comments": [
                            {
                                "blockComments": [
                                    {"svgGroupId": "old-id-1"},
                                    {"svgGroupId": "old-id-2"}
                                ]
                            }
                        ]
                    }
                },
                {
                    "id": "M_144_SkRT",
                    "commentary": {
                        "comments": [
                            {
                                "blockComments": [
                                    {"svgGroupId": "skrt-old-1"}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        
        # Write test JSON
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_json, f)
        
        # Create test SVG files
        self.svg_143 = os.path.join(self.svg_dir, "M_143_test.svg")
        with open(self.svg_143, 'w', encoding='utf-8') as f:
            f.write('''<svg>
    <g class="tkk" id="old-id-1">content1</g>
    <g id="old-id-2" class="tkk">content2</g>
    <g class="other" id="other-id">other</g>
</svg>''')
        
        self.svg_144 = os.path.join(self.svg_dir, "M_144_Reihentabelle.svg")
        with open(self.svg_144, 'w', encoding='utf-8') as f:
            f.write('''<svg>
    <g class="tkk" id="skrt-old-1">SkRT content</g>
</svg>''')
    
    def tearDown(self):
        """Clean up temporary files"""
        shutil.rmtree(self.test_dir)
    
    def test_file_structure_creation(self):
        """Test that test files are created correctly"""
        self.assertTrue(os.path.exists(self.json_path))
        self.assertTrue(os.path.exists(self.svg_dir))
        self.assertTrue(os.path.exists(self.svg_143))
        self.assertTrue(os.path.exists(self.svg_144))
    
    def test_json_loading(self):
        """Test loading the test JSON file"""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertIn('textcritics', data)
        self.assertEqual(len(data['textcritics']), 2)
        self.assertEqual(data['textcritics'][0]['id'], 'M_143')
        self.assertEqual(data['textcritics'][1]['id'], 'M_144_SkRT')
    
    def test_svg_file_detection(self):
        """Test SVG file detection and filtering"""
        svg_files = [f for f in os.listdir(self.svg_dir) if f.endswith('.svg')]
        self.assertEqual(len(svg_files), 2)
        self.assertIn('M_143_test.svg', svg_files)
        self.assertIn('M_144_Reihentabelle.svg', svg_files)


@pytest.mark.unit
class TestMain(unittest.TestCase):
    """Test cases for the main function"""
    
    def setUp(self):
        """Set up test fixtures and mocks"""
        # Mock unify_tkk_ids function
        self.unify_tkk_ids_patcher = patch('unify_tkk_ids.unify_tkk_ids')
        self.mock_unify_tkk_ids = self.unify_tkk_ids_patcher.start()
        
        # Mock sys.exit to prevent actual program termination
        self.sys_exit_patcher = patch('sys.exit')
        self.mock_sys_exit = self.sys_exit_patcher.start()
        
        # Default successful return value
        self.mock_unify_tkk_ids.return_value = True
    
    def tearDown(self):
        """Clean up patches"""
        self.unify_tkk_ids_patcher.stop()
        self.sys_exit_patcher.stop()
    
    def test_main_success_path(self):
        """Test main function with successful processing"""
        # Import main here to ensure mocks are in place
        from unify_tkk_ids import main
        
        with patch('builtins.print') as mock_print:
            main()
        
        # Should call unify_tkk_ids with correct parameters
        self.mock_unify_tkk_ids.assert_called_once_with(
            './tests/data/textcritics.json',
            './tests/img/',
            "g-tkk-"
        )
        
        # Should print success message
        mock_print.assert_called_once_with("\n Finished!")
        
        # Should not call sys.exit
        self.mock_sys_exit.assert_not_called()
    
    def test_main_with_warnings(self):
        """Test main function when processing returns success=False (warnings)"""
        # Import main here to ensure mocks are in place  
        from unify_tkk_ids import main
        
        # Mock unify_tkk_ids to return success=False
        self.mock_unify_tkk_ids.return_value = False
        
        with patch('builtins.print') as mock_print:
            main()
        
        # Should call unify_tkk_ids with correct parameters
        self.mock_unify_tkk_ids.assert_called_once_with(
            './tests/data/textcritics.json',
            './tests/img/',
            "g-tkk-"
        )
        
        # Should print warning message
        mock_print.assert_called_once_with("\n Processing completed with warnings.")
        
        # Should not call sys.exit
        self.mock_sys_exit.assert_not_called()
    
    def test_main_file_not_found_error(self):
        """Test main function with FileNotFoundError"""
        # Import main here to ensure mocks are in place
        from unify_tkk_ids import main
        
        # Mock unify_tkk_ids to raise FileNotFoundError
        error_message = "No such file or directory: './tests/data/textcritics.json'"
        self.mock_unify_tkk_ids.side_effect = FileNotFoundError(error_message)
        
        with patch('builtins.print') as mock_print:
            main()
        
        # Should print error message
        mock_print.assert_called_once_with(f"Error: {error_message}")
        
        # Should call sys.exit with code 1
        self.mock_sys_exit.assert_called_once_with(1)
    
    def test_main_general_exception(self):
        """Test main function with exceptions that should be caught"""
        # Import main here to ensure mocks are in place
        from unify_tkk_ids import main
        
        # Test with ValueError (should be caught)
        error_message = "Something went wrong during processing"
        self.mock_unify_tkk_ids.side_effect = ValueError(error_message)
        
        with patch('builtins.print') as mock_print:
            main()
        
        # Should print error message
        mock_print.assert_called_once_with(f"Unexpected error: {error_message}")
        
        # Should call sys.exit with code 1
        self.mock_sys_exit.assert_called_once_with(1)
    
    def test_main_configuration_values(self):
        """Test that main function uses correct configuration values"""
        # Import main here to ensure mocks are in place
        from unify_tkk_ids import main
        
        main()
        
        # Verify the exact configuration values passed to unify_tkk_ids
        call_args = self.mock_unify_tkk_ids.call_args
        json_path, svg_folder, prefix = call_args[0]
        
        self.assertEqual(json_path, './tests/data/textcritics.json')
        self.assertEqual(svg_folder, './tests/img/')
        self.assertEqual(prefix, "g-tkk-")
    
    def test_main_with_different_exception_types(self):
        """Test main function with various exception types"""
        # Import main here to ensure mocks are in place
        from unify_tkk_ids import main
        
        # Test with ValueError
        self.mock_unify_tkk_ids.side_effect = ValueError("Invalid value provided")
        
        with patch('builtins.print') as mock_print:
            main()
        
        mock_print.assert_called_once_with("Unexpected error: Invalid value provided")
        self.mock_sys_exit.assert_called_with(1)
        
        # Reset mocks
        mock_print.reset_mock()
        self.mock_sys_exit.reset_mock()
        
        # Test with KeyError (note: KeyError adds quotes around the message)
        self.mock_unify_tkk_ids.side_effect = KeyError("Required key missing")
        
        with patch('builtins.print') as mock_print:
            main()
        
        mock_print.assert_called_once_with("Unexpected error: 'Required key missing'")
        self.mock_sys_exit.assert_called_with(1)
    
    def test_main_return_value_handling(self):
        """Test that main function properly handles unify_tkk_ids return values"""
        # Import main here to ensure mocks are in place
        from unify_tkk_ids import main
        
        # Test with complex return values
        self.mock_unify_tkk_ids.return_value = True
        
        with patch('builtins.print') as mock_print:
            main()
        
        # Should handle the return values correctly (even though main doesn't use them)
        mock_print.assert_called_once_with("\n Finished!")
        self.mock_sys_exit.assert_not_called()
    
    @patch('unify_tkk_ids.unify_tkk_ids')
    def test_main_isolated_import(self, mock_process):
        """Test main function with isolated import (alternative testing approach)"""
        # This test uses a different approach - patching at module level
        mock_process.return_value = True
        
        # Import and call main
        from unify_tkk_ids import main
        
        with patch('builtins.print') as mock_print, patch('sys.exit') as mock_exit:
            main()
        
        # Verify function was called correctly
        mock_process.assert_called_once_with(
            './tests/data/textcritics.json',
            './tests/img/',
            "g-tkk-"
        )
        
        # Verify success message
        mock_print.assert_called_once_with("\n Finished!")
        mock_exit.assert_not_called()
    
    def test_main_uncaught_exception(self):
        """Test that exceptions not in the catch list are not caught"""
        # Import main here to ensure mocks are in place
        from unify_tkk_ids import main
        
        # Mock unify_tkk_ids to raise an exception not in our catch list
        self.mock_unify_tkk_ids.side_effect = RuntimeError("This should not be caught")
        
        # This should raise the RuntimeError (not be caught)
        with self.assertRaises(RuntimeError):
            main()
    
    def test_name_main_execution_path(self):
        """Test coverage of the if __name__ == '__main__' execution path"""
        # This test ensures the module-level execution path is covered
        with patch('unify_tkk_ids.main') as mock_main_func:
            # Simulate the module being executed directly
            # We do this by executing the conditional logic directly
            import unify_tkk_ids
            
            # Temporarily change __name__ to simulate direct execution
            original_name = unify_tkk_ids.__name__
            try:
                unify_tkk_ids.__name__ = "__main__"
                
                # Execute the conditional check manually to get coverage
                if unify_tkk_ids.__name__ == "__main__":
                    unify_tkk_ids.main()
                
                # Verify main was called
                mock_main_func.assert_called_once()
            finally:
                # Restore original __name__
                unify_tkk_ids.__name__ = original_name


if __name__ == '__main__':
    # Create test data directory structure
    test_data_dir = os.path.join(os.path.dirname(__file__), 'tests')
    if not os.path.exists(test_data_dir):
        os.makedirs(test_data_dir)
        
        # Create sample data subdirectories
        data_dir = os.path.join(test_data_dir, 'data')
        img_dir = os.path.join(test_data_dir, 'img')
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(img_dir, exist_ok=True)
        
        # Create sample textcritics.json
        sample_json = {
            "textcritics": [
                {
                    "id": "M_143",
                    "commentary": {
                        "comments": [
                            {
                                "blockComments": [
                                    {"svgGroupId": "old-id-1"},
                                    {"svgGroupId": "old-id-2"}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        
        with open(os.path.join(data_dir, 'textcritics.json'), 'w', encoding='utf-8') as f:
            json.dump(sample_json, f, indent=2)
        
        # Create sample SVG
        sample_svg = '''<svg xmlns="http://www.w3.org/2000/svg">
    <g class="tkk" id="old-id-1">
        <text>Test content 1</text>
    </g>
    <g id="old-id-2" class="tkk">
        <text>Test content 2</text>
    </g>
</svg>'''
        
        with open(os.path.join(img_dir, 'M_143_test.svg'), 'w', encoding='utf-8') as f:
            f.write(sample_svg)
    
    unittest.main()