#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for logger_utils.py

Tests for:
- log_report_message: message formatting, list appending, and printing
- Stats initialization tests (all counters start at 0)
- bump() method tests (incrementing counters with various amounts)
- summary() method tests (formatted string output)
"""

import unittest

from utils.logger_utils import Logger


class TestLogger(unittest.TestCase):
    """Tests for Logger class."""

    def setUp(self):
        """Set up a Logger instance for testing."""
        self.logger = Logger(verbose=False)

    def test_logger_initial_stats(self):
        """Test that all stats counters are initialized to 0."""
        expected = {
            "entries_seen": 0,
            "ids_seen": 0,
            "ids_changed": 0,
            "ids_missing": 0,
            "ids_multiple": 0,
            "svg_errors": 0,
            "svg_unchanged": 0,
        }
        self.assertEqual(self.logger.stats, expected)

    def test_log_appends_and_prints(self):
        """Test that log() appends formatted message to messages list and prints it."""
        self.logger.verbose = True

        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.log("error", "E001", "M143_TF1", "Something went wrong")
            expected = " [ERROR] M143_TF1: Something went wrong [E001]"
            self.assertIn(expected, self.logger.messages)
            mock_print.assert_called_with(expected)

    def test_log_without_entry_id_and_code(self):
        """Test log() behavior when entry_id and code are empty."""
        self.logger.log("warning", "", "", "something happened")
        expected = " [WARNING] something happened"
        self.assertIn(expected, self.logger.messages)

    def test_print_report_success(self):
        """Test that print_report() prints success message when no messages are logged."""
        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.print_report()
            mock_print.assert_any_call(
                "\n [\u2713] All JSON and SVG IDs successfully updated."
            )

    def test_print_report_with_errors_and_info(self):
        """Test that print_report() correctly categorizes and prints messages."""
        self.logger.log("error", "E001", "ID1", "Error message")
        self.logger.log("info", "I001", "ID2", "Info message")

        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.print_report()
            calls = [c[0][0] for c in mock_print.call_args_list]
            self.assertTrue(
                any("--- Errors and Warnings ---" in call for call in calls)
            )
            self.assertTrue(any("--- Info Messages ---" in call for call in calls))

    def test_bump_stats_and_summary(self):
        """Test that bump_stats() increments counters and summary() prints correct string."""
        self.logger.bump_stats("entries_seen")
        self.logger.bump_stats("ids_changed", 5)
        self.logger.bump_stats("svg_errors", 2)

        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.print_stats_summary()
            printed = mock_print.call_args[0][0]
            self.assertIn("Summary:", printed)
            self.assertIn("entries=1", printed)
            self.assertIn("changed=5", printed)
            self.assertIn("svg_errors=2", printed)

    def test_bump_stats_invalid_key(self):
        """Test that bump_stats() raises KeyError for invalid stat key."""
        with self.assertRaises(KeyError):
            self.logger.bump_stats("not_a_stat")

    def test_print_stats_summary(self):
        """Test that print_stats_summary prints the labeled summary string."""
        self.logger.bump_stats("entries_seen", 2)
        self.logger.bump_stats("ids_missing", 3)

        with unittest.mock.patch("builtins.print") as mock_print:
            self.logger.print_stats_summary()
            # The first argument to print should contain the label
            printed = mock_print.call_args[0][0]
            self.assertIn("Summary:", printed)
            self.assertIn("entries=2", printed)
            self.assertIn("missing=3", printed)


if __name__ == "__main__":
    unittest.main()
