# Testing Guide for create_glyph_subset

This directory contains tests for `create_glyph_subset.py` and its utility modules under `utils/`.

## Project Structure

```
create_glyph_subset/
├── create_glyph_subset.py    # Main script: orchestrates codepoints → font subset, manifest, license
├── fonts/
│   └── bravura-1.380/
│       ├── Bravura.woff2     # Source font (SMuFL)
│       └── OFL.txt           # License of the source font
├── utils/
│   ├── __init__.py
│   ├── codepoint_utils.py    # Reading codepoints from edition-glyphs.data.ts
│   ├── constants.py          # Font names, subset note, file names, default font path
│   ├── file_utils.py         # Writing the manifest, copying the license
│   └── font_utils.py         # Subsetting, renaming and saving the font
├── tests/
│   ├── data/
│   │   └── edition-glyphs.data.ts
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_codepoint_utils.py
│   ├── test_create_glyph_subset.py
│   ├── test_file_utils.py
│   └── test_font_utils.py
├── requirements.txt
└── pytest.ini
```

`tests/data/edition-glyphs.data.ts` is a copy of `awg-app/src/app/views/edition-view/data/edition-glyphs.data.ts`, so the tests run without a local awg-app checkout. Update it together with the expected codepoints in `conftest.py` when the glyph data changes.

## Setup

See the [Virtual Environments](../../README.md#virtual-environments) section in the repo-level README for how to create and activate a virtual environment.

Once the virtual environment is active, install dependencies:

```bash
pip install -r requirements.txt --require-hashes
```

## Running Tests

```bash
# Run all tests
pytest .

# Run with verbose output
pytest . -v

# Run a specific test module
pytest tests/test_font_utils.py -v
```

## Coverage

```bash
# Run with coverage (configured in pytest.ini)
pytest . --cov=utils --cov=create_glyph_subset --cov-report=html --cov-report=term
```

Coverage reports are generated in `htmlcov/`.

## Test Structure

Test modules are listed alphabetically.

---

### Shared Fixtures (`conftest.py`)

- `glyphs_data_path`: path to `tests/data/edition-glyphs.data.ts`.
- `expected_codepoints`: the 26 unique codepoints of `EDITION_GLYPHS_DATA`, sorted.
- `source_font_path`: path to the bundled `Bravura.woff2`.
- `subset_out_dir`: nested, initially missing output folder of one full `create_glyph_subset` run, shared by the whole session.

---

### Codepoint Utils Tests (`test_codepoint_utils.py`)

Tests for `CodepointUtils` in `utils/codepoint_utils.py`.

#### `TestReadCodepoints`

Tests for `read_codepoints(file_path)`:

- The codepoints of the data file match the expected sorted list exactly.
- Values with several escapes (`SUBITO_PIANO`, `NOTE_HALF_DOTTED`) add all their codepoints.
- Codepoints used in several values are listed only once.
- The literal space in `NOTE_HALF_DOTTED` is not added.
- An `OSError` is raised when the file does not exist.

#### `TestParseCodepoints`

Tests for `parse_codepoints(content)`:

- A single escape is parsed to its codepoint.
- Codepoints are sorted regardless of their order in the source.
- Lowercase hex digits are accepted.
- Values in double quotes or backticks are parsed as well.
- Escapes in comments or other properties than `hex` are ignored.
- A `ValueError` is raised when no `hex` value is found.
- A `ValueError` is raised when `hex` values contain no escape.

#### `TestFormatCodepoint`

Tests for `format_codepoint(codepoint)`:

- A codepoint is formatted as `U+XXXX` with uppercase digits.
- Small codepoints are zero-padded to four digits.

---

### Main Script Tests (`test_create_glyph_subset.py`)

Tests for the public functions in `create_glyph_subset.py`.

#### `TestParseArgs`

Tests for `parse_args(argv)`:

- The input path and output folder are parsed as paths.
- The bundled Bravura is the default source font, and the file exists.
- `--out` is required.

#### `TestCreateGlyphSubset`

Tests for `create_glyph_subset(glyphs_data_path, font_path, out_dir)`:

- Exactly the font, manifest and license are written to the output folder.
- The codepoints and written paths are returned.
- The manifest lists exactly the codepoints mapped in the font.
- A codepoint missing in the source font raises a `ValueError` before anything is written.
- A missing (nested) output folder is created.
- No font or manifest is written when `OFL.txt` is missing next to the source font.

#### `TestMain`

Tests for `main(argv)`:

- The number of codepoints and all written files are reported.
- A missing input file exits with code 1 and an error message.
- A source font that is not a font file exits with code 1 and an error message.
- An input without `\uXXXX` escapes exits with code 1 and an error message.

---

### File Utils Tests (`test_file_utils.py`)

Tests for `FileUtils` in `utils/file_utils.py`.

#### `TestCreateManifest`

Tests for `create_manifest(codepoints)`:

- The manifest names family, style, PostScript name, font file, license, source and note.
- Codepoints are listed as `U+XXXX` in the given order, together with their count.

#### `TestWriteManifest`

Tests for `write_manifest(manifest_path, codepoints)`:

- The written JSON equals the created manifest.
- The JSON uses a 4-space indent and ends with a newline.

#### `TestCopyLicense`

Tests for `copy_license(license_path, out_dir)`:

- The OFL is copied byte for byte into the output folder.
- The bundled license is the Bravura OFL with its Reserved Font Name.

---

### Font Utils Tests (`test_font_utils.py`)

Tests for `FontUtils` in `utils/font_utils.py`.

#### `TestLoadFont`

Tests for `load_font(font_path)`:

- The source font is loaded as a WOFF2 CFF font.
- Timestamp recalculation is disabled.

#### `TestCheckCodepoints`

Tests for `check_codepoints(font, codepoints)`:

- No error is raised when all codepoints are in the font.
- A `ValueError` names every missing codepoint.
- A font without a Unicode cmap reports all codepoints as missing.

#### `TestSubsetFont`

Tests for `subset_font(font, codepoints)`:

- The subset cmap contains exactly the requested codepoints.
- The original glyphs are kept.
- Trademark, designer, URL and license entries (name IDs 7–9, 11–14) are kept.
- The font object is subset in place.

#### `TestAddSubsetNote`

Tests for `add_subset_note(copyright_text)`:

- The note is inserted between the copyright statement and the license text.
- The note is appended when the copyright has a single paragraph.

#### `TestRenameFont`

Tests for `rename_font(font)` and `rename_cff(font)`:

- Family, style, full, PostScript name and description are set on all records.
- The unique ID combines the source version and the PostScript name, or falls back to the PostScript name.
- The version string is kept.
- "Bravura" is not used in name IDs 1, 2, 4, 6, 16 or 17.
- The Steinberg copyright and the OFL text are kept, and the subset note is added.
- Typographic names 16/17 are removed.
- The CFF font names are renamed.
- Fonts without a CFF table are renamed in the name table only.

#### `TestSaveFont`

Tests for `save_font(font, out_path)`:

- The saved font is a WOFF2.
- The subset is less than a tenth of the source font size.
- Two runs produce byte-identical files.
