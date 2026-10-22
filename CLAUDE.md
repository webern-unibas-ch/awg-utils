# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git workflow

- Never push.
- Only commit when the user explicitly asks; they normally commit themselves. Instead, propose a commit message.
- Commit messages follow Conventional Commits with a scope, as in the history: `feat(utils): …`, `build(deps): …`, `lint(compare): …`, `docs(README): …`.

## Repository layout

Utility scripts for the Anton Webern Gesamtausgabe (AWG). Each top-level folder is an **independent Python project** with its own `requirements.in`/`requirements.txt`, virtual environment (`.venv`), and (where present) `pytest.ini`, `tests/` and `utils/` package. There is no root-level package or shared code between tools. All commands below must be run from inside the respective tool folder, because scripts and tests import via `from utils.… import …` relative to that folder.

Tested and linted in CI (`.github/workflows/pytest.yml`, `pylint.yml`, Python 3.12–3.14, only for changed folders):
- `convert_intro_to_md/`: AWG intro JSON (HTML `blockContent`) → Markdown + TEI XML, one file pair per locale.
- `convert_source_description/`: Word `.docx` → `<stem>_source-description.json` + `<stem>_textcritics.json`.
- `create_glyph_subset/`: awg-app `edition-glyphs.data.ts` → renamed WOFF2 subset of Bravura 1.380 (`AWGEditionGlyphs-Regular.woff2`) + manifest JSON + `OFL.txt`.
- `unify_ids/`: rewrites auto-generated SVG group IDs (e.g. `g6407`) to AWG convention IDs in textcritics JSON and SVG files.
- `compare_pdfs/`: lint only, no tests.

Work in progress lives on feature branches in the user's fork (`origin`), not on `main`: `feature/convert-pdf-to-svg` and `feature/create-svg-sheets-list`. When such a branch is merged into `main`, add its folder to this list, to the `directories` of the pip entry in `.github/dependabot.yml`, and (if it has tests and lint) to the path filters in `.github/workflows/pytest.yml` and `pylint.yml`.

## Commands

Setup per tool folder (Git Bash on Windows):

```bash
cd unify_ids                      # or any other tool folder
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt --require-hashes
```

Dependencies are pinned with hashes. Edit `requirements.in`, then regenerate:

```bash
pip install pip-tools
pip-compile --generate-hashes --strip-extras requirements.in
```

`unify_ids` has a second pair, `requirements-notebook.in`/`.txt`, for `unify_ids.ipynb`; it constrains itself with `-c requirements.txt`.

All projects at once, from the repo root, using the stdlib-only `update_venvs.py` (compiles each `requirements*.in`, then `pip-sync`s the `.venv`, runs pylint and pytest only if the sync changed an installed package, and ends with a summary table):

```bash
python update_venvs.py                  # all projects; keeps existing pins, picks up .in changes
python update_venvs.py unify_ids        # single project
python update_venvs.py --upgrade        # move all pins to newest versions
python update_venvs.py --no-compile     # only sync venvs to the existing lock files
```

Further flags: `--recreate` (rebuild `.venv` from scratch), `--force-checks` (run checks even without package changes), `--no-checks`, `--verbose`. `requirements.in` is the source of truth. Lock files are compiled both locally (Windows) and by Dependabot (Linux), so platform-specific transitive dependencies (`colorama`, `pexpect`) are listed explicitly in the `.in` files to keep both outputs identical. When a recompile adds or removes a package only on one platform, add it to the `.in` file the same way.

Tests (`pytest.ini` adds `-v`, coverage on the main script(s) plus `utils`, and an HTML report in `htmlcov/`):

```bash
pytest tests/ -v                                          # what CI runs
pytest tests/test_svg_utils.py                            # single file
pytest tests/test_svg_utils.py::TestClass::test_name      # single test
pytest -m "not slow"                                      # unify_ids only: markers unit/integration/slow (--strict-markers)
```

Lint (CI runs pylint per file and fails on anything below 10.00/10):

```bash
find . -name "*.py" -not -path "./.venv/*" -exec pylint {} \;
```

Running the tools:
- `python convert_intro_to_md.py <path>/intro.json`
- `python convert_source_description.py <path>/file.docx`
- `python compare_pdfs.py …` (argparse; see `--help`)
- `python create_glyph_subset.py <path>/edition-glyphs.data.ts --out <dir> [--font <path>/Bravura.woff2] [--preview]`
- `unify_ids`: the three scripts take **no CLI arguments**. The paths (`json_path`, `svg_folder`, or `complex_id` for `unify_kv_ids.py`) are hard-coded in `main()`, and their defaults point at `tests/data/` and `tests/img/`. Running a script with those defaults rewrites the test fixtures in place, so don't commit the result.

## Architecture

### convert_intro_to_md
Pipeline with an intermediate representation: `utils/html_parser.parse_intro()` turns the HTML block content into a format-neutral tree of dataclasses (`utils/nodes.py`: block nodes like `Paragraph`/`Blockquote`, inline nodes like `Italic`/`FootnoteRef`/`Ref`). `utils/md_renderer.render()` and `utils/tei_renderer.render()` both consume that same tree. New HTML constructs therefore need a node type, parser support, **and** handling in both renderers.

### convert_source_description
`mammoth` converts `.docx` → HTML (`FileUtils.read_html_from_word_file`), BeautifulSoup parses it, then `SourcesUtils.create_source_list()` and `TextcriticsUtils.create_textcritics()` build the two output objects. Utilities are classes (`SourcesUtils`, `TextcriticsUtils`, `ParagraphUtils`, etc.), and output shapes are defined in `utils/typed_classes.py` / `utils/default_objects.py`. The script's module docstring documents the Word structure the parser expects. `how_to/word-formatting.md` documents the authoring conventions. Shared test fixtures are loaded through `tests/conftest.py` (`pytest_plugins = ("tests.test_fixtures",)`).

### create_glyph_subset
`CodepointUtils.read_codepoints()` collects the `\uXXXX` escapes inside `hex` string values only (any quote style; deduplicated, sorted; literal characters like the space in `NOTE_HALF_DOTTED` are skipped). `FontUtils` then checks them against the cmap, subsets with fontTools, and renames the font. "Bravura" is an OFL Reserved Font Name, so the rename covers name IDs 1/2/3/4/6 on all records, removes 16/17, and also renames the CFF `fontNames`/`FamilyName`/`FullName`. The subset note is inserted after the copyright statement in ID 0 (which carries the full OFL text) and set as ID 10. `subset_font` sets `options.name_IDs = ["*"]` (the fontTools default keeps only IDs 0–6), so designer, trademark and license entries survive; renaming runs after subsetting. Fonts are loaded with `recalcTimestamp=False`, so the output is byte-reproducible. `--preview` adds `AWGEditionGlyphs-preview.html` via `utils/preview_utils.py`: it parses the entries and section comments of the data file into `GlyphGroup`/`GlyphEntry` dataclasses (reusing the regexes from `codepoint_utils`), re-reads the **written** subset, and fills `utils/preview_template.html` (`string.Template`, `$placeholders`) with the font embedded as a base64 data URI. The source font and `OFL.txt` are committed in `fonts/bravura-1.380/`. Tests use `tests/data/edition-glyphs.data.ts`, a copy of the awg-app file. When the app file changes, update the copy together with `EXPECTED_CODEPOINTS` in `tests/conftest.py`.

### unify_ids
Three entry scripts share a functional `utils/` package (plain functions, unlike the class-based utils elsewhere):
- `unify_tkk_ids.py` → `awg-tkk-<entryId>-NNN` (textcritical comments, SVG class `tkk`)
- `unify_link_box_ids.py` → `awg-lb-<entryId>-to-<sheetId>`, with an optional per-SVG suffix derived from `-NvonM-` in the filename
- `unify_kv_ids.py` → `awg-kv-<complexId><corrSuffix>-NNN`. JSON only, no SVGs touched.

Common flow (TKK/link-box): `file_utils.load_and_validate_inputs` → `extraction_utils.extract_file_info_list` (parse SVG filenames once) → `create_svg_loader` (lazy loader backed by an in-memory `svg_file_cache` dict) → per textcritics entry, `svg_utils` finds the relevant SVGs and indexes IDs by CSS class, then the ID is replaced in the JSON and the cached SVG → `save_results` writes JSON plus every cached SVG → `validation_utils.display_validation_report`. `Logger` (`utils/logger_utils.py`) carries the `dry_run`/`verbose` flags and the stats counters. Writes are skipped when `dry_run` is set or `stats["ids_changed"] == 0`. Per-ID context is passed via small dataclasses in `utils/models.py` (`ContextHelpers`, `SvgGroupIdContext`, …). ID prefixes and CSS classes live in `utils/constants.py`.

## Conventions

Code style rules come from `.github/skills/check-consistency/SKILL.md`. Read the full file before larger edits. Key points:
- Module and function docstrings have the summary on the same line as the opening `"""`.
- Google-style `Args:` entries as `name (Type): Description.` and `Returns:` as `Type: Description.`. Omit `Returns:` for `-> None`.
- Class docstrings (class-based utils) start with `"A class that contains utility functions for ..."`.
- Pylint must stay at 10.00/10. If a disable is unavoidable, put a per-file `# pylint: disable=…` on line 1 (e.g. `protected-access` in tests) rather than inline.
- Mark `if __name__ == "__main__":` blocks with `# pragma: no cover`.

Related workflows in `.github/skills/`:
- `sync-test-readme`: each tested tool has a `tests/TEST_README.md` that must list the current test files and describe what each covers. Update it when test files are added, removed, or renamed.
- `sync-tests-to-api`: when a production function signature or return shape changes, update every calling test to match.

Formatting for non-Python files follows `.prettierrc` (4-space indent, single quotes, 120 print width, SVGs parsed as HTML).
