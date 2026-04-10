#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Models for ID Unification

This module contains dataclasses used for configuration and data structures
in the ID unification workflows.
"""

from dataclasses import dataclass
from typing import Any, Callable

from utils.logger_utils import Logger


@dataclass(frozen=True)
class IdMapping:
    """Pair a CSS class with the ID prefix used for rewritten identifiers."""

    css_class: str
    prefix: str


@dataclass
class ContextHelpers:
    """Shared context helpers."""

    svg_loader: Callable[[str], Any]
    logger: Logger


@dataclass
class TextcriticalComments:
    """Data shared while processing a single textcritics entry."""

    svg_group_ids: list
    block_comments: list


@dataclass
class SvgGroupIdContext:
    """Data shared while processing one svgGroupId within an entry."""

    svg_group_id: str
    block_comment: dict
    matching_files: list
    new_id: str
