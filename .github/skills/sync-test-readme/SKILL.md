---
name: sync-test-readme
description: Keep tests/TEST_README.md aligned with added, removed, renamed, or fundamentally changed test files, including removal of outdated documentation.
---

# Test README Sync

Use this skill whenever test files are added, removed, renamed, or significantly refactored.

## Scope

This skill maintains:
- `tests/TEST_README.md`

This skill does **not** replace test implementation work; it only keeps test documentation accurate.

## Trigger Conditions

Run this skill when one or more of these happen:
- A new test file is added (for example `tests/test_stats_utils.py`).
- A test file is removed or renamed.
- A test module changes purpose or coverage significantly.
- Utility or module structure changes in a way that affects test documentation sections.

## Required Outcomes

After running this skill, `tests/TEST_README.md` must:
- List current test files in project structure snippets.
- Include a section for each relevant test module category.
- Describe what each test module validates at a high level.
- Remove references to deleted or obsolete test files/functions/scenarios.
- Keep examples and coverage narrative consistent with current module names.

## Update Procedure

1. Recheck project structure first
- Re-list current folders/files before editing documentation.
- Confirm actual filenames in `tests/` and relevant modules under `utils/`.

2. Identify test changes
- Compare current repository test files against README references.
- Detect additions, removals, renames, and semantic coverage shifts.

3. Update structure overview
- Adjust the `tests/` tree listing to include current files.
- Remove obsolete file entries.

4. Update test category sections
- Add or revise sections like `Stats Utils Tests` when needed.
- Ensure section titles match real filenames.
- Keep descriptions concise and behavior-focused.
- Required order under `## Test Structure`: Shared Test Fixtures first, then test modules alphabetically by test filename.

5. Remove outdated content
- Delete stale references to old function names, modules, or assumptions.
- Remove claims about test counts/coverage that are no longer true, unless revalidated.

6. Validate consistency
- File names in prose must exist in the repo.
- Mentioned module paths should match current package layout.
- No contradictory statements between project structure and detailed sections.

## Content Rules

- Keep wording factual and implementation-aligned.
- Prefer stable descriptions over brittle details.
- Avoid hardcoded numeric claims (`50+ tests`, exact coverage percentages) unless freshly confirmed.
- Preserve existing README style and formatting.
- Do **not** document private functions (names starting with `_`) in test section bullet lists; only document public API functions.
- When documenting what a test class covers beyond function names (e.g. edge cases), verify those scenarios actually exist in the test file before writing them down. Remove or replace any inherited descriptions that no longer match the actual tests.

## Completion Checklist

Before finishing:
- Project structure was rechecked immediately before doc sync.
- `tests/TEST_README.md` includes all active core test modules.
- Removed/renamed tests are no longer documented.
- Newly added test files have matching section(s) if they represent a distinct category.
- No stale references remain.
- No private functions (`_name`) are listed in any test section.
- Scenario/edge-case descriptions in each section were verified against actual test code, not carried over from a previous version.

## Example Delta

If `tests/test_stats_utils.py` is added:
- Add it to the structure tree.
- Add a `Stats Utils Tests (test_stats_utils.py)` section.
- Summarize `Stats` initialization, `bump()`, and `summary()` expectations.
