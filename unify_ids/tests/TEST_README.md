# Testing Guide for unify_tkk_ids

This directory contains comprehensive tests for the `unify_tkk_ids.py` script and its utility modules that unify TKK Group IDs in JSON textcritic files and corresponding SVG files.

## Project Structure

The project now uses a clean package structure:
```
unify_tkk_ids/
├── unify_tkk_ids.py          # Main script
├── utils/                    # Utility package
│   ├── __init__.py
│   ├── models.py             # Data models (dataclasses)
│   ├── constants.py          # Shared constants
│   ├── extraction_utils.py   # Data extraction functions
│   ├── file_utils.py         # File I/O operations
│   ├── stats_utils.py        # Processing statistics tracking
│   ├── svg_utils.py          # SVG processing functions
│   └── validation_utils.py   # Validation and reporting
├── tests/
│   ├── test_fixtures.py      # Shared test data and fixtures
│   ├── test_unify_tkk_ids.py # Main script tests
│   ├── test_extraction_utils.py
│   ├── test_file_utils.py
│   ├── test_stats_utils.py
│   ├── test_svg_utils.py
│   └── test_validation_utils.py
├── requirements.txt          # All dependencies (including test deps)
└── pytest.ini
```

## Setup

1. Install dependencies (including test dependencies):
```bash
pip install -r requirements.txt
```

2. Ensure you have Python 3.7+ installed.

## Running Tests

### Quick Start
```bash
# Run all tests
pytest tests/

# Run specific test module
pytest tests/test_validation_utils.py -v
```

## Coverage

Run with coverage to see which parts of the code are tested:
```bash
# Generate HTML and terminal coverage report
pytest tests/ --cov=utils --cov=unify_tkk_ids --cov-report=html --cov-report=term

# Coverage for specific module
pytest tests/test_validation_utils.py --cov=utils.validation_utils --cov-report=term
```

Coverage reports are generated in the `htmlcov/` directory and show line-by-line coverage for all utility modules.

### Test Categories

#### Unit Tests
Test individual functions in isolation by module:
```bash
# Test extraction utilities
pytest tests/test_extraction_utils.py -v

# Test file operations
pytest tests/test_file_utils.py -v

# Test SVG processing
pytest tests/test_svg_utils.py -v

# Test validation functions
pytest tests/test_validation_utils.py -v
```

#### Integration Tests  
Test the complete workflow:
```bash
# Main integration tests
pytest tests/test_unify_tkk_ids.py -v
```


## Test Structure

### Shared Test Fixtures (`test_fixtures.py`)
Centralized test data and helper functions used across all test modules:
- **JSON data structures**: Various prefixed/unprefixed ID configurations
- **SVG content samples**: Single/multiple files with different ID patterns  
- **Helper functions**: `_create_textcritic_entry()`, `_create_json_data()`
- **Organized sections**: Individual samples, JSON structures, SVG content

### Extraction Utils Tests (`test_extraction_utils.py`)
Tests for `utils/extraction_utils.py`:
- **`extract_moldenhauer_number()`**: Number extraction from various ID formats
- **`extract_svg_group_ids()`**: svgGroupId extraction from JSON structures
- Edge cases and different entry formats

### File Utils Tests (`test_file_utils.py`) 
Tests for `utils/file_utils.py`:
- **`load_and_validate_inputs()`**: JSON/SVG file loading and validation
- **`create_svg_loader()`**: SVG file caching system
- **`save_results()`**: File saving operations
- Error handling for missing files and permissions

### Stats Utils Tests (`test_stats_utils.py`)
Tests for `utils/stats_utils.py`:
- **`Stats` initialization**: Verify all counters initialize to 0
- **`bump()` method**: Test incrementing counters with default and custom amounts
- **`summary()` method**: Test formatted string output with various counter values
- Multiple increments and multi-counter operations

### SVG Utils Tests (`test_svg_utils.py`)
Tests for `utils/svg_utils.py`:
- **`find_matching_svg_files_by_class()`**: SVG file discovery with ID matching by class
- **`find_relevant_svg_files()`**: File filtering by entry type (TF, Sk, SkRT)
- **`update_svg_id()`**: ID replacement in SVG content with tkk class preservation
- Different quote styles, attribute orders, and CSS class combinations

### Validation Utils Tests (`test_validation_utils.py`)
Tests for `utils/validation_utils.py`:
- **`display_validation_report()`**: Comprehensive validation reporting (7 test scenarios)
- **`validate_json_entries()`**: JSON ID validation with TODO handling
- **`validate_svg_entries()`**: SVG orphan detection
- Error reporting and success scenarios

### Main Script Tests (`test_unify_tkk_ids.py`)
Integration tests for the main `unify_tkk_ids.py` script:
- **`process_single_svg_group_id()`**: Single ID processing workflow
- **`process_textcritics_entry()`**: Entry-level processing
- **`unify_tkk_ids()`**: Complete unification workflow
- Error handling and edge cases

## Test Data & Fixtures

The test suite uses a centralized fixture system in `test_fixtures.py`:

### JSON Test Data
- **`JSON_DATA_WITH_SINGLE_PREFIXED_ID`**: Single correctly updated ID
- **`JSON_DATA_WITH_2_PREFIXED_IDS`**: Two correctly updated IDs  
- **`JSON_DATA_WITH_4_PREFIXED_IDS`**: Four correctly updated IDs
- **`JSON_DATA_WITH_TODO`**: Contains TODO entries (should be ignored)
- **`JSON_DATA_WITH_MIXED_IDS`**: Mix of updated and unchanged IDs
- **`JSON_DATA_EMPTY`**: Empty data structure
- **`JSON_DATA_MALFORMED`**: Invalid JSON for error testing

### SVG Test Content  
- **Single file samples**: `SAMPLE_SVG_WITH_SINGLE_PREFIXED_ID`, `SAMPLE_SVG_WITH_SINGLE_UNPREFIXED_ID`
- **Multiple ID samples**: `SAMPLE_SVG_WITH_MULTIPLE_PREFIXED_IDS`, `SAMPLE_SVG_WITH_MULTIPLE_UNPREFIXED_IDS`
- **Multi-file samples**: `SAMPLE_MULTIPLE_SVG_WITH_PREFIXED_IDS`, `SAMPLE_MULTIPLE_SVG_WITH_UNPREFIXED_IDS`
- **Mixed scenarios**: `SAMPLE_SVG_WITH_MIXED_IDS`, `SAMPLE_MULTIPLE_SVG_WITH_MIXED_IDS`

All test data is generated programmatically using helper functions to ensure consistency and easy maintenance.

## Continuous Integration

The test suite is designed to:
- Run in isolated environments with proper package imports
- Use centralized fixtures to avoid code duplication
- Clean up temporary files automatically
- Provide clear error messages with specific assertions
- Support parallel execution via pytest-xdist

## Adding New Tests

When adding new functionality:

1. **Add fixtures** to `test_fixtures.py` if creating shared test data
2. **Create unit tests** in the appropriate `test_<module>.py` file
3. **Add integration tests** to `test_unify_tkk_ids.py` for end-to-end workflows  
4. **Include edge cases** and error conditions
5. **Update this README** with new test descriptions
6. **Use helper functions** from fixtures for consistent data generation

## Example Test Run Output

```
$ pytest tests/ --cov=utils --cov=unify_tkk_ids --cov-report=term

======== test session starts ========
collected 50+ items

tests/test_extraction_utils.py::TestExtractMoldenhauerNumber::test_extract_moldenhauer_number_standard PASSED
tests/test_file_utils.py::TestLoadAndValidateInputs::test_load_and_validate_inputs_success PASSED  
tests/test_svg_utils.py::TestUpdateSvgId::test_update_svg_id_basic_replacement PASSED
tests/test_validation_utils.py::TestDisplayValidationReport::test_display_validation_report_no_errors PASSED
tests/test_unify_tkk_ids.py::TestProcessSingleSvgGroupId::test_process_single_svg_group_id_success PASSED
...

======== 50+ passed in 3.45s ========

Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
unify_tkk_ids.py                145     8    95%   187-190, 23-25
utils/__init__.py                13     0   100%
utils/extraction_utils.py        35     2    94%   45-46
utils/file_utils.py              67     3    96%   78-80
utils/svg_utils.py               89     4    96%   134-137
utils/validation_utils.py        45     1    98%   67
-----------------------------------------------------------
TOTAL                           394    18    95%
```

## Key Improvements

- **Eliminated duplicate code** through centralized fixtures
- **Organized by functionality** with separate test modules per utility
- **Comprehensive coverage** with 7 validation scenarios and multiple edge cases  
- **Clean package structure** following Python best practices
- **Maintainable test data** using programmatic generation instead of inline constants
