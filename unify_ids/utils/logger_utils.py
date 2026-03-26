#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared processing statistics and logging for ID unification scripts.
"""


class Logger:
    """Centralized logger for reporting and statistics in ID unification scripts."""

    def __init__(self, verbose=True):
        self.messages = []
        self.verbose = verbose
        # Stats counters as a dictionary
        self.stats = {
            "entries_seen": 0,
            "ids_seen": 0,
            "ids_changed": 0,
            "ids_missing": 0,
            "ids_multiple": 0,
            "svg_errors": 0,
            "svg_unchanged": 0,
        }

    def bump_stats(self, key, amount=1):
        """Increment a stats counter."""
        if key in self.stats:
            self.stats[key] += amount
        else:
            raise KeyError(f"Logger has no stat '{key}'")

    def log(self, type_, code, entry_id, message):
        """Log a structured message."""
        entry_prefix = f"{entry_id}: " if entry_id else ""
        code_suffix = f" [{code}]" if code else ""
        msg = f" [{type_.upper()}] {entry_prefix}{message}{code_suffix}"
        self.messages.append(msg)
        if self.verbose:
            print(msg)

    def print_report(self):
        """Print a structured report from collected messages."""
        if self.messages:
            print("\n--- REPORT ---")
            error_warning_msgs = [
                msg
                for msg in self.messages
                if msg.startswith(" [ERROR]") or msg.startswith(" [WARNING]")
            ]
            info_msgs = [msg for msg in self.messages if msg.startswith(" [INFO]")]
            if error_warning_msgs:
                print("\n--- Errors and Warnings ---")
                for msg in error_warning_msgs:
                    print(msg)
            if info_msgs:
                print("\n--- Info Messages ---")
                for msg in info_msgs:
                    print(msg)
        else:
            print("\n [\u2713] All JSON and SVG IDs successfully updated.")

    def print_stats_summary(self):
        """Print a summary string of all counters."""
        # Map keys to display names for summary
        key_map = {
            "entries_seen": "entries",
            "ids_seen": "ids_seen",
            "ids_changed": "changed",
            "ids_missing": "missing",
            "ids_multiple": "multiple",
            "svg_errors": "svg_errors",
            "svg_unchanged": "svg_unchanged",
        }
        summary = ", ".join(f"{key_map.get(k, k)}={self.stats[k]}" for k in key_map)
        print(f"\n Summary: {summary}")
