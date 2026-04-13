---
name: sync-tests-to-api
description: Update test files to match changed function signatures, renamed parameters, removed parameters, or changed return values in production code.
---

# Sync Tests to API

Use this skill whenever a production function's signature or observable behaviour changes and the existing tests need to be updated to match.

## Scope

This skill maintains:
- All test files under `tests/` that call the changed function(s)

This skill does **not** design new tests for new functionality; it only keeps existing tests correct after a production API change.

## Trigger Conditions

Run this skill when one or more of these happen:
- A function parameter is added, removed, or renamed.
- A parameter's type changes (e.g. two separate dicts merged into one).
- The argument order of a function changes.
- A return value's shape or type changes.
- A function is renamed or moved to a different module.
- Pylint reports `E1120` (no value for argument) or `E1121` (too many positional arguments).
- A test raises `TypeError` about unexpected or missing arguments.

## Required Outcomes

After running this skill, all test files must:
- Call every changed function with the correct number and order of arguments.
- Use the correct parameter names for keyword arguments.
- Assert against the correct return value shape/type.
- Import any new types or classes required by updated signatures.
- Pass `pylint` and `pytest` without errors attributable to the API change.

## Update Procedure

1. Identify the changed function(s)
   - Read the current production source to confirm the exact new signature.
   - Note every parameter: name, position, type, and whether it has a default.

2. Find all call sites in tests
   - Search all files under `tests/` for calls to the changed function.
   - Also search for any `patch` targets that reference the function by dotted path.

3. Fix each call site
   - Update positional arguments to the new order.
   - Add or remove arguments to match the new arity.
   - Replace old keyword argument names with new ones.
   - If a new required argument needs a value in tests, prefer:
     a. The relevant constant from `utils/constants.py` (e.g. `TKK.prefix`, `TKK.css_class`).
     b. A real instance of the required class with default construction (e.g. `Settings()`, `Stats()`).
     c. A `MagicMock()` only as a last resort when a real instance is impractical.

4. Fix assertions
   - Update assertions that reference old return value keys, shapes, or counts.
   - Remove assertions that tested behaviour that no longer exists.

5. Fix imports
   - Add imports for any new types referenced at call sites (e.g. `from utils.models import Settings`).
   - Remove imports that are no longer used.

6. Prefer constants over literals
   - Where a call site passes a hardcoded string that matches a constant (e.g. `"awg-tkk-"` == `TKK.prefix`), replace the literal with the constant.
   - This applies to `setUp` / `setUpClass` assignments as well as inline call arguments.
   - If a `setUp` method exists solely to assign a constant, remove the `setUp` method and reference the constant directly at each call site.

7. Validate
   - Ensure the Python environment is active before running checks.
   - Prefer explicit interpreter invocation when available (for example: `.venv/Scripts/python.exe -m pytest ...` on Windows, `.venv/bin/python -m pytest ...` on Unix).
   - If using shell activation, activate first and run checks in the same command/session.
   - Run `pylint tests/` and confirm no `E1120`/`E1121` errors remain for the changed function.
   - Run `pytest tests/` and confirm all tests that previously passed still pass.

## Content Rules

- Do not redesign tests; only update call sites to match the new API.
- Do not suppress pylint errors with `# pylint: disable` unless the error is unrelated to the API change (e.g. `R0902` too-many-instance-attributes caused by necessary setUp state).
- Do not add extra test attributes or mocks beyond what is needed for the updated signature.
- Keep `setUp` methods lean: if `setUp` only sets constants it should be removed and the constant used directly.

## Completion Checklist

Before finishing:
- Production function signature was read from source (not guessed).
- All test call sites for the changed function were found and updated.
- All imports are correct and unused imports removed.
- Hardcoded string literals that match constants have been replaced with the constant.
- Unnecessary `setUp` methods have been removed.
- Validation commands were run in the correct project environment (venv/poetry/conda as applicable).
- `pylint tests/` shows no argument-count or argument-order errors for the changed function(s).
- `pytest tests/` passes (or only fails on pre-existing unrelated failures).
