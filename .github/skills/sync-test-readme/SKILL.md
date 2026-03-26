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

1. Identify test changes
- Compare current repository test files against README references.
- Detect additions, removals, renames, and semantic coverage shifts.

2. Update structure overview
- Adjust the `tests/` tree listing to include current files.
- Remove obsolete file entries.

3. Update test category sections
- Add or revise sections like `Stats Utils Tests` when needed.
- Ensure section titles match real filenames.
- Keep descriptions concise and behavior-focused.

4. Remove outdated content
- Delete stale references to old function names, modules, or assumptions.
- Remove claims about test counts/coverage that are no longer true, unless revalidated.

5. Validate consistency
- File names in prose must exist in the repo.
- Mentioned module paths should match current package layout.
- No contradictory statements between project structure and detailed sections.

## Content Rules

- Keep wording factual and implementation-aligned.
- Prefer stable descriptions over brittle details.
- Avoid hardcoded numeric claims (`50+ tests`, exact coverage percentages) unless freshly confirmed.
- Preserve existing README style and formatting.

## Completion Checklist

Before finishing:
- `tests/TEST_README.md` includes all active core test modules.
- Removed/renamed tests are no longer documented.
- Newly added test files have matching section(s) if they represent a distinct category.
- No stale references remain.

## Example Delta

If `tests/test_stats_utils.py` is added:
- Add it to the structure tree.
- Add a `Stats Utils Tests (test_stats_utils.py)` section.
- Summarize `Stats` initialization, `bump()`, and `summary()` expectations.
