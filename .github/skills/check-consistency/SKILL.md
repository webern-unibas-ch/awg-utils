---
name: check-consistency
description: Audit and fix consistency across a Python project. Use for checking docstring style, class/module docstring conventions, type annotations in Args/Returns, pylint compliance, and naming consistency across all source and test files.
---

# Consistency Check

Use this skill when asked to check, audit, or fix consistency across source files — including docstrings, naming conventions, and code style.

## Scope

This skill covers:
- Module-level docstrings
- Class-level docstrings
- Method/function docstrings (summary line, `Args:`, `Returns:`)
- Type annotations in `Args` and `Returns` sections
- pylint compliance (target: 10.00/10)
- Naming consistency across methods and parameters

## Trigger Conditions

Run this skill when:
- Asked to "check consistency", "audit docstrings", or "standardize style"
- A new utility module is added and needs to match existing conventions
- A method is renamed and all docstrings referencing it need updating
- pylint score drops below 10.00/10

## Conventions for This Project

### Module docstrings
- Summary on the **same line** as the opening `"""`:
  ```python
  """Utility functions for handling HTML content in intro processing."""
  ```

### Class docstrings
- Must start with `"A class that contains utility functions for ..."`:
  ```python
  class HTMLUtils:
      """A class that contains utility functions for handling HTML content in intro processing."""
  ```

### Method/function docstrings
- Summary on the **same line** as the opening `"""`.
- Blank line before `Args:` and `Returns:` sections.
- `Args:` entries use `param_name (Type): Description.` format.
- `Returns:` entries use `Type: Description.` format.
- Omit `Returns:` section entirely for `-> None` methods (do NOT write `Returns: None`).
- Example:
  ```python
  def html_to_md(html: str) -> str:
      """Convert an HTML string to Markdown.

      Args:
          html (str): The HTML string to convert.

      Returns:
          str: The converted Markdown string, or an empty string if the input is
          empty or not a string.
      """
  ```

### pylint
- All files must score **10.00/10**.
- Use per-file `# pylint: disable=<code>` at line 1 only when unavoidable (e.g. `protected-access` in test files).
- Never use `# pylint: disable` inline unless the rule cannot be satisfied correctly.

## Audit Procedure

1. **Read all source files** under `utils/` and the main script in parallel.
2. **Check module docstrings** — summary on first line, no multi-line `"""\n...\n"""` style.
3. **Check class docstrings** — start with `"A class that contains utility functions for ..."`.
4. **Check method docstrings** for each method:
   - Summary on first `"""` line.
   - `Args:` entries include `(Type)`.
   - `Returns:` entries include `Type:` prefix.
   - No `Returns: None` on `-> None` methods.
5. **Check naming** — method names use verbs; private helpers are prefixed `_`.
6. **Run pylint** and resolve any warnings before marking done.

## Fix Procedure

- Apply all fixes with `multi_replace_string_in_file` in a single call per file where possible.
- After all edits, run pylint to confirm 10.00/10.
- Run pytest to confirm no regressions.
