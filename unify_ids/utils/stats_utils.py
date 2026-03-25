#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared processing statistics for ID unification scripts.
"""


class Stats:
    """Accumulates counters during an ID unification run."""

    def __init__(self):
        self.entries_seen = 0
        self.ids_seen = 0
        self.ids_changed = 0
        self.ids_missing = 0
        self.ids_multiple = 0
        self.svg_errors = 0
        self.svg_unchanged = 0

    def bump(self, key, amount=1):
        setattr(self, key, getattr(self, key) + amount)

    def summary(self):
        return (
            f"entries={self.entries_seen}, "
            f"ids_seen={self.ids_seen}, "
            f"changed={self.ids_changed}, "
            f"missing={self.ids_missing}, "
            f"multiple={self.ids_multiple}, "
            f"svg_errors={self.svg_errors}, "
            f"svg_unchanged={self.svg_unchanged}"
        )


class Settings:
    """Configuration for ID unification runs."""

    def __init__(self, dry_run=False, verbose=True):
        self.dry_run = dry_run
        self.verbose = verbose
