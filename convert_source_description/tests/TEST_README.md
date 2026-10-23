# Testing Guide for convert_source_description

This directory contains the current tests for the `convert_source_description.py` project and its helper module.

## Project Structure

```
convert_source_description/
├── convert_source_description.py      # Main conversion script
├── utils/
│   ├── constants.py                   # Shared parsing and string constants
│   ├── default_objects.py             # Default output object templates
│   ├── file_utils.py                  # File loading and output helpers
│   ├── glyph_utils.py                 # Glyph names and CSS classes from awg-app glyph data
│   ├── index_utils.py                 # Paragraph index lookup helpers
│   ├── paragraph_utils.py             # Paragraph extraction helpers
│   ├── replacement_utils.py           # Text replacement and formatting utilities
│   ├── sources_utils.py               # Source description parsing and conversion helpers
│   ├── stripping_utils.py             # HTML tag stripping and cleanup
│   ├── textcritics_utils.py           # Textcritics table parsing
│   └── typed_classes.py               # Typed helper classes
├── tests/
│   ├── __init__.py
│   ├── TEST_README.md
│   ├── conftest.py
│   ├── data/
│   │   └── edition-glyphs.data.ts     # Trimmed copy of the awg-app glyph data
│   ├── test_convert_source_description.py
│   ├── test_file_utils.py
│   ├── test_fixtures.py
│   ├── test_glyph_utils.py
│   ├── test_index_utils.py
│   ├── test_paragraph_utils.py
│   ├── test_replacement_utils.py
│   ├── test_sources_utils.py
│   ├── test_sources_utils_folios.py
│   ├── test_stripping_utils.py
│   └── test_textcritics_utils.py
├── requirements.txt
└── pytest.ini
```

## Setup

See the [Virtual Environments](../../README.md#virtual-environments) section in the repo-level README for how to create and activate a virtual environment.

Once the virtual environment is active, install dependencies:

```bash
pip install -r requirements.txt --require-hashes
```

## Running Tests

Run the full test suite from the `convert_source_description` directory:

```bash
pytest tests/ -v
```

Run the sources utils tests only:

```bash
pytest tests/test_sources_utils.py -v
```

## Coverage

Run with coverage to see which parts of the code are tested:

```bash
# Full suite coverage (terminal + HTML)
pytest tests/ --cov=utils --cov=convert_source_description --cov-report=term --cov-report=html

# Coverage for helper-focused tests only
pytest tests/test_sources_utils.py tests/test_paragraph_utils.py tests/test_replacement_utils.py tests/test_stripping_utils.py --cov=utils --cov-report=term

# Coverage for a specific module
pytest tests/test_stripping_utils.py --cov=utils.stripping_utils --cov-report=term
```

Coverage reports are generated in `htmlcov/`.

## Test Structure

### Shared Test Fixtures

The current shared fixtures are defined in `test_fixtures.py`:
- `sample_soup`: provides representative parsed HTML
- `sample_soup_paras`: provides a reusable list of paragraph tags
- `glyphs`: provides the glyph names and CSS classes read from `data/edition-glyphs.data.ts` (path also exported as `GLYPHS_DATA_PATH`)

`data/edition-glyphs.data.ts` is a trimmed copy of the awg-app file `edition-glyphs.data.ts` (17 entries, all five sections), so the tests do not need a local awg-app.

Fixtures are auto-loaded for tests via `conftest.py`.

Additional fixture in `test_sources_utils.py`:
- `helper`: returns a `SourcesUtils` instance

### Main Script Tests (`test_convert_source_description.py`)

Tests for `convert_source_description.py` currently cover:
- `check_file_path()`: `.docx` extension validation
- `convert_source_description()`: extension validation, glyph forwarding to `TextcriticsUtils`, file path forwarding, collaborator call behavior, and JSON output path naming
- `main()`: argument parsing (incl. `--glyphs-data` and its default path), delegation to `convert_source_description()`, error exit (code 1) for missing glyph data and wrong file extensions before converting, and uncaught errors during the conversion

The test module uses mock patching to isolate all collaborators (`GlyphUtils`, `FileUtils`, `SourcesUtils`, `TextcriticsUtils`).

### Glyph Utils Tests (`test_glyph_utils.py`)

Tests for `glyph_utils.py` currently cover:
- `parse_glyphs()`: glyph names (`alt` values incl. brackets) and CSS classes per section (`ACCIDENTALS` → `glyph accid`, `NOTE VALUES` → `glyph note`, others → `glyph`), unknown sections, entries before the first section, quote styles, entries without `alt`, and empty content
- `read_glyphs()`: reading the test glyph data in source order, missing file, and file without entries

The test module uses the trimmed glyph data in `data/` and small inline TypeScript snippets.

### File Utils Tests (`test_file_utils.py`)

Tests for `file_utils.py` currently cover:
- `read_html_from_word_file()` success and error handling
- `write_json()` file output (with LF line endings) and write-error handling

The test module uses monkeypatching to isolate Mammoth conversion behavior and I/O failure paths.

### Index Utils Tests (`test_index_utils.py`)

Tests for `index_utils.py` currently cover:
- `find_siglum_indices()`: locating siglum paragraph positions within flat paragraph lists, including single-letter sigla, bracket-wrapped sigla, and optional superscript additions
- `find_contents_indices()`: detecting the start and end boundaries of a contents block, including cases where no contents label or no comments label is found

The test module validates index detection against small inline fixtures and the shared representative paragraph fixture.

### Paragraph Utils Tests (`test_paragraph_utils.py`)

Tests for `paragraph_utils.py` currently cover:
- `get_paragraph_content_by_label()`: paragraph label discovery and content extraction with punctuation stripping
- `get_paragraph_index_by_label()`: finding the index of paragraphs by label

The test module validates label discovery, basic content extraction, and sibling-chain processing on both small fixtures and representative parsed HTML.

### Replacement Utils Tests (`test_replacement_utils.py`)

Tests for `replacement_utils.py` currently cover:
- `add_report_fragment_links()`: adding report navigation anchors to bold text
- `escape_curly_brackets()`: escaping curly brackets for template rendering
- `replace_glyphs()`: replacing musical notation glyphs with styled span elements

The test module validates text replacement behavior with the shared `glyphs` fixture on various glyph types (accidentals, notes, dynamics) and edge cases (HTML-escaped names like `[&gt;]`, partial matches, hyphen exclusions, names missing from the glyph data, empty glyph data).

### Sources Utils Tests (`test_sources_utils.py`)

Tests for `sources_utils.py` covering source list and item processing currently cover:
- `create_source_list()`: full source list construction, duplicate detection, and warning output

The module defines a local `helper` fixture returning a `SourcesUtils` instance.

### Sources Utils Folios Tests (`test_sources_utils_folios.py`)

Tests for `sources_utils.py` covering folio and system processing. Currently no public methods.

The module defines its own local `helper` fixture returning a `SourcesUtils` instance.

### Stripping Utils Tests (`test_stripping_utils.py`)

Tests for `stripping_utils.py` currently cover:
- `strip_by_delimiter()`
- `strip_tag_and_clean()`
- `strip_tag()`

The test module validates delimiter handling, tag removal behavior, and paragraph cleanup handling for malformed and nested HTML snippets.

### Textcritics Utils Tests (`test_textcritics_utils.py`)

Tests for `textcritics_utils.py` currently cover:
- `create_textcritics()`: empty input behavior, normal table parsing, and corrections routing

The test module also validates helper behavior for block parsing, comment extraction/transformation, and corrections-specific field cleanup.
