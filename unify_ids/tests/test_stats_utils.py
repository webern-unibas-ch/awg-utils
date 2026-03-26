#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for stats_utils.py

Tests for Stats utility class including:
- Stats initialization tests (all counters start at 0)
- bump() method tests (incrementing counters with various amounts)
- summary() method tests (formatted string output)
"""

import unittest

from utils.stats_utils import Stats


class TestStatsInitialization(unittest.TestCase):
    """Test Stats class initialization."""

    def test_all_counters_initialized_to_zero(self):
        """Test that all counters are initialized to 0."""
        stats = Stats()
        self.assertEqual(stats.entries_seen, 0)
        self.assertEqual(stats.ids_seen, 0)
        self.assertEqual(stats.ids_changed, 0)
        self.assertEqual(stats.ids_missing, 0)
        self.assertEqual(stats.ids_multiple, 0)
        self.assertEqual(stats.svg_errors, 0)
        self.assertEqual(stats.svg_unchanged, 0)


class TestStatsBump(unittest.TestCase):
    """Test Stats.bump() method for incrementing counters."""

    def setUp(self):
        """Test that a fresh Stats instance is created for each test."""
        self.stats = Stats()

    def test_bump_single_counter_default_amount(self):
        """Test bumping a single counter with default amount (1)."""
        self.stats.bump("entries_seen")
        self.assertEqual(self.stats.entries_seen, 1)

    def test_bump_single_counter_custom_amount(self):
        """Test bumping a single counter with custom amount."""
        self.stats.bump("ids_changed", 5)
        self.assertEqual(self.stats.ids_changed, 5)

    def test_bump_multiple_times(self):
        """Test bumping the same counter multiple times."""
        self.stats.bump("ids_seen")
        self.stats.bump("ids_seen")
        self.stats.bump("ids_seen", 3)
        self.assertEqual(self.stats.ids_seen, 5)

    def test_bump_multiple_counters(self):
        """Test bumping different counters."""
        self.stats.bump("entries_seen", 2)
        self.stats.bump("ids_changed", 3)
        self.stats.bump("svg_errors", 1)
        self.assertEqual(self.stats.entries_seen, 2)
        self.assertEqual(self.stats.ids_changed, 3)
        self.assertEqual(self.stats.svg_errors, 1)
        self.assertEqual(self.stats.ids_seen, 0)  # unchanged


class TestStatsSummary(unittest.TestCase):
    """Test Stats.summary() method for formatted output."""

    def test_summary_all_zeros(self):
        """Test summary string when all counters are 0."""
        stats = Stats()
        expected = (
            "entries=0, ids_seen=0, changed=0, missing=0, multiple=0, "
            "svg_errors=0, svg_unchanged=0"
        )
        self.assertEqual(stats.summary(), expected)

    def test_summary_with_values(self):
        """Test summary string with various counter values."""
        stats = Stats()
        stats.bump("entries_seen", 10)
        stats.bump("ids_seen", 25)
        stats.bump("ids_changed", 5)
        stats.bump("ids_missing", 2)
        stats.bump("svg_errors", 1)
        expected = (
            "entries=10, ids_seen=25, changed=5, missing=2, multiple=0, "
            "svg_errors=1, svg_unchanged=0"
        )
        self.assertEqual(stats.summary(), expected)

    def test_summary_format_consistency(self):
        """Test that summary format contains all counter fields."""
        stats = Stats()
        summary = stats.summary()
        assert "entries=" in summary
        assert "ids_seen=" in summary
        assert "changed=" in summary
        assert "missing=" in summary
        assert "multiple=" in summary
        assert "svg_errors=" in summary
        assert "svg_unchanged=" in summary


if __name__ == "__main__":
    unittest.main()
