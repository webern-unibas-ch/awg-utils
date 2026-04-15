# Testing Guide for convert_source_description

This directory contains the current tests for the `convert_source_description.py` project and its helper module.

## Project Structure

```
convert_source_description/
├── convert_source_description.py      # Main conversion script
├── constants.py                       # Shared parsing and string constants
├── default_objects.py                 # Default output object templates
├── file_utils.py                      # File loading and output helpers
├── paragraph_utils.py                 # Paragraph extraction helpers
├── replacement_utils.py               # Text replacement and formatting utilities
├── stripping_utils.py                 # HTML tag stripping and cleanup
├── textcritics_utils.py               # Textcritics table parsing
├── typed_classes.py                   # Typed helper classes
├── utils.py                           # Shared utility helpers
├── utils_helper.py                    # HTML parsing and extraction helpers
├── tests/
│   ├── __init__.py
│   ├── TEST_README.md
│   ├── conftest.py
│   ├── fixtures.py
│   ├── test_convert_source_description.py
│   ├── test_file_utils.py
│   ├── test_paragraph_utils.py
│   ├── test_replacement_utils.py
│   ├── test_stripping_utils.py
│   ├── test_textcritics_utils.py
│   └── test_utils_helper.py
├── requirements.txt
└── pytest.ini
```

## Setup

Install the project dependencies from the project root:

```bash
pip install --require-hashes -r requirements.txt
```

## Running Tests

Run the full test suite from the `convert_source_description` directory:

```bash
pytest tests/ -v
```

Run the helper-module tests only:

```bash
pytest tests/test_utils_helper.py -v
```

## Coverage

Run with coverage to see which parts of the code are tested:

```bash
# Full suite coverage (terminal + HTML)
pytest tests/ --cov=utils --cov=convert_source_description --cov-report=term --cov-report=html

# Coverage for helper-focused tests only
pytest tests/test_utils_helper.py tests/test_paragraph_utils.py tests/test_replacement_utils.py tests/test_stripping_utils.py --cov=utils --cov-report=term

# Coverage for a specific module
pytest tests/test_stripping_utils.py --cov=utils.stripping_utils --cov-report=term
```

Coverage reports are generated in `htmlcov/`.

## Test Structure

### Shared Test Fixtures

The current shared fixtures are defined in `fixtures.py`:
- `sample_soup`: provides representative parsed HTML
- `sample_soup_paras`: provides a reusable list of paragraph tags

Fixtures are auto-loaded for tests via `conftest.py`.

Additional fixture in `test_utils_helper.py`:
- `helper`: returns a `ConversionUtilsHelper` instance

### Main Script Tests (`test_convert_source_description.py`)

This file exists as a placeholder for future tests of `convert_source_description.py`.
It currently contains no active tests.

### File Utils Tests (`test_file_utils.py`)

Tests for `file_utils.py` currently cover:
- `read_html_from_word_file()` success and error handling
- `write_json()` file output and write-error handling

The test module uses monkeypatching to isolate Mammoth conversion behavior and I/O failure paths.

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

The test module validates text replacement behavior on various glyph types (accidentals, notes) and edge cases (partial matches, hyphen exclusions).

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

### Utils Helper Tests (`test_utils_helper.py`)

Tests for `utils_helper.py` currently cover:
- `find_siglum_indices()`: identifying siglum markers in paragraph lists
- `_get_item()`: extracting content item data from parsed paragraphs

The test module uses inline HTML fixtures built with BeautifulSoup to validate parser behavior against realistic source-description fragments.
