#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for validation_utils.py module

This test suite provides comprehensive testing for the validation utilities
used in TKK ID processing.

Test Categories:
- display_validation_report function tests (main validation reporting)
- validate_json_entries function tests 
- validate_svg_entries function tests
- Edge cases and error conditions

Usage:
    python -m pytest tests/test_validation_utils.py -v
    python -m pytest tests/test_validation_utils.py::TestDisplayValidationReport -v
"""

import unittest
import pytest
from unittest.mock import patch
from io import StringIO

# Import validation functions from validation_utils
from validation_utils import (
    display_validation_report,
    validate_json_entries,
    validate_svg_entries
)


@pytest.mark.unit 
class TestDisplayValidationReport(unittest.TestCase):
    """Test cases for the display_validation_report function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.prefix = "g-tkk-"
        
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_validation_report_with_no_errors(self, mock_stdout):
        """Test with all IDs correctly prefixed"""
        data = {
            "textcritics": [
                {
                    "id": "M_143",
                    "commentary": {
                        "comments": [
                            {
                                "blockComments": [
                                    {"svgGroupId": "g-tkk-1"},
                                    {"svgGroupId": "g-tkk-2"}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        
        loaded_svgs = {
            "test.svg": {
                "content": '<g class="tkk" id="g-tkk-1">content</g>'
            }
        }
        
        display_validation_report(data, self.prefix, loaded_svgs)
        output = mock_stdout.getvalue()
        self.assertIn("All JSON and SVG 'tkk' IDs successfully updated", output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_validation_report_with_json_errors(self, mock_stdout):
        """Test with unchanged JSON IDs"""
        data = {
            "textcritics": [
                {
                    "id": "M_143",
                    "commentary": {
                        "comments": [
                            {
                                "blockComments": [
                                    {"svgGroupId": "old-id-1"},
                                    {"svgGroupId": "g-tkk-2"}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        
        loaded_svgs = {}
        
        display_validation_report(data, self.prefix, loaded_svgs)
        output = mock_stdout.getvalue()
        self.assertIn("JSON ERROR: Unchanged ID 'old-id-1'", output)
        self.assertIn("Total issues found: 1", output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_validation_report_with_svg_orphans(self, mock_stdout):
        """Test with SVG IDs that weren't updated"""
        data = {"textcritics": []}
        
        loaded_svgs = {
            "test.svg": {
                "content": '<g class="tkk" id="old-svg-id">content</g>'
            }
        }
        
        display_validation_report(data, self.prefix, loaded_svgs)
        output = mock_stdout.getvalue()
        self.assertIn("SVG ORPHAN: ID 'old-svg-id'", output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_validation_report_with_todo_ignored(self, mock_stdout):
        """Test that TODO entries are ignored"""
        data = {
            "textcritics": [
                {
                    "id": "M_143",
                    "commentary": {
                        "comments": [
                            {
                                "blockComments": [
                                    {"svgGroupId": "TODO"},
                                    {"svgGroupId": "g-tkk-1"}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        
        loaded_svgs = {}
        
        display_validation_report(data, self.prefix, loaded_svgs)
        output = mock_stdout.getvalue()
        self.assertIn("All JSON and SVG 'tkk' IDs successfully updated", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_display_validation_report_with_empty_data(self, mock_stdout):
        """Test display_validation_report with empty data"""
        display_validation_report({}, "g-tkk-", {})
        output = mock_stdout.getvalue()
        self.assertIn("All JSON and SVG 'tkk' IDs successfully updated", output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_validation_report_with_malformed_json(self, mock_stdout):
        """Test display_validation_report with malformed JSON structure"""
        data = {
            "textcritics": [
                {
                    # Missing commentary structure
                    "id": "M_143"
                },
                {
                    "id": "M_144",
                    "commentary": {
                        # Missing comments
                    }
                }
            ]
        }
        
        display_validation_report(data, "g-tkk-", {})
        output = mock_stdout.getvalue()
        self.assertIn("All JSON and SVG 'tkk' IDs successfully updated", output)


@pytest.mark.unit
class TestValidateJsonEntries(unittest.TestCase):
    """Test cases for the validate_json_entries function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.prefix = "g-tkk-"
        
    def test_validate_json_entries_no_errors(self):
        """Test with all IDs correctly prefixed"""
        data = {
            "textcritics": [
                {
                    "id": "M_143",
                    "commentary": {
                        "comments": [
                            {
                                "blockComments": [
                                    {"svgGroupId": "g-tkk-1"},
                                    {"svgGroupId": "g-tkk-2"}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        
        errors = validate_json_entries(data, self.prefix)
        self.assertEqual(errors, 0)
    
    def test_validate_json_entries_with_errors(self):
        """Test with unchanged JSON IDs"""
        data = {
            "textcritics": [
                {
                    "id": "M_143",
                    "commentary": {
                        "comments": [
                            {
                                "blockComments": [
                                    {"svgGroupId": "old-id-1"},
                                    {"svgGroupId": "old-id-2"},
                                    {"svgGroupId": "g-tkk-1"}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        
        errors = validate_json_entries(data, self.prefix)
        self.assertEqual(errors, 2)
    
    def test_validate_json_entries_todo_ignored(self):
        """Test that TODO entries are ignored"""
        data = {
            "textcritics": [
                {
                    "id": "M_143",
                    "commentary": {
                        "comments": [
                            {
                                "blockComments": [
                                    {"svgGroupId": "TODO"},
                                    {"svgGroupId": "g-tkk-1"}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        
        errors = validate_json_entries(data, self.prefix)
        self.assertEqual(errors, 0)


@pytest.mark.unit
class TestValidateSvgEntries(unittest.TestCase):
    """Test cases for the validate_svg_entries function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.prefix = "g-tkk-"
        
    def test_validate_svg_entries_with_no_errors(self):
        """Test with all SVG IDs correctly prefixed"""
        loaded_svgs = {
            "test1.svg": {
                "content": '<g class="tkk" id="g-tkk-1">content</g>'
            },
            "test2.svg": {
                "content": '<rect class="tkk" id="g-tkk-2"/>'
            }
        }
        
        errors = validate_svg_entries(loaded_svgs, self.prefix)
        self.assertEqual(errors, 0)
    
    def test_validate_svg_entries_with_orphans(self):
        """Test with SVG IDs that weren't updated"""
        loaded_svgs = {
            "test1.svg": {
                "content": '<g class="tkk" id="old-svg-id">content</g>'
            },
            "test2.svg": {
                "content": '<rect class="tkk" id="another-old-id"/>'
            }
        }
        
        errors = validate_svg_entries(loaded_svgs, self.prefix)
        self.assertEqual(errors, 2)
    
    def test_validate_svg_entries_with_mixed_results(self):
        """Test with mix of updated and non-updated IDs"""
        loaded_svgs = {
            "test1.svg": {
                "content": '<g class="tkk" id="g-tkk-1">content</g><rect class="tkk" id="old-id"/>'
            }
        }
        
        errors = validate_svg_entries(loaded_svgs, self.prefix)
        self.assertEqual(errors, 1)


if __name__ == '__main__':
    unittest.main()