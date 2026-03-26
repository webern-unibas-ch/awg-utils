#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Models for ID Unification

This module contains dataclasses used for configuration and data structures
in the ID unification workflows.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class IdMapping:
    """Pair a CSS class with the ID prefix used for rewritten identifiers."""

    css_class: str
    prefix: str


@dataclass
class Settings:
    """Configuration for ID unification runs."""

    dry_run: bool = False
    verbose: bool = True
