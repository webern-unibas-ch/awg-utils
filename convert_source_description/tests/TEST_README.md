# Testing Guide for convert_source_description

This directory contains the current tests for the `convert_source_description.py` project and its helper module.

## Project Structure

```
convert_source_description/
├── convert_source_description.py      # Main conversion script
├── default_objects.py                 # Default output object templates
├── file_utils.py                      # File loading and output helpers
├── typed_classes.py                   # Typed helper classes
├── utils.py                           # Shared utility helpers
├── utils_helper.py                    # HTML parsing and extraction helpers
├── tests/
│   ├── __init__.py
│   ├── TEST_README.md
│   ├── test_convert_source_description.py
│   ├── test_stripping_utils.py
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

## Test Structure

### Shared Test Fixtures

The current fixtures are defined inside `test_utils_helper.py`:
- `helper`: returns a `ConversionUtilsHelper` instance
- `sample_soup`: provides representative parsed HTML
- `sample_soup_paras`: provides a reusable list of paragraph tags

### Main Script Tests (`test_convert_source_description.py`)

This file exists as a placeholder for future tests of `convert_source_description.py`.
It currently contains no active tests.

### Stripping Utils Tests (`test_stripping_utils.py`)

Tests for `stripping_utils.py` currently cover:
- `strip_by_delimiter()`
- `strip_tag_and_clean()`
- `strip_tag()`

The test module validates delimiter handling, tag removal behavior, and paragraph cleanup handling for malformed and nested HTML snippets.

### Utils Helper Tests (`test_utils_helper.py`)

Tests for `utils_helper.py` currently cover:
- `find_siglum_indices()`
- paragraph-label lookup behavior
- paragraph-content extraction behavior
- paragraph-index lookup behavior
- glyph replacement behavior

The test module uses inline HTML fixtures built with BeautifulSoup to validate parser behavior against realistic source-description fragments.
