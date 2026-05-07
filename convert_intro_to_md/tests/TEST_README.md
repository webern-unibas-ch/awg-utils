# Testing Guide for convert_intro_to_md

This directory contains tests for `convert_intro_to_md.py` and its utility modules under `utils/`.

## Project Structure

```
convert_intro_to_md/
├── convert_intro_to_md.py    # Main script: orchestrates JSON → Markdown/TEI conversion
├── utils/
│   ├── __init__.py
│   ├── file_utils.py         # File I/O: reading JSON, writing output files
│   ├── html_parser.py        # HTML parser: converts JSON block content to IR nodes
│   ├── md_renderer.py        # Markdown renderer: renders IR nodes to GFM Markdown
│   ├── nodes.py              # IR node dataclasses (Text, Bold, Italic, Table, etc.)
│   ├── replacement_utils.py  # Markdown post-processing: whitespace and table separation
│   └── tei_renderer.py       # TEI renderer: renders IR nodes to TEI XML
├── tests/
│   ├── data/
│   │   ├── intro.json
│   │   ├── intro_de.md
│   │   ├── intro_de.tei
│   │   └── intro_en.md
│   ├── __init__.py
│   ├── test_convert_intro_to_md.py
│   ├── test_file_utils.py
│   ├── test_html_parser.py
│   ├── test_md_renderer.py
│   ├── test_replacement_utils.py
│   └── test_tei_renderer.py
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

```bash
# Run all tests
pytest .

# Run with verbose output
pytest . -v

# Run a specific test module
pytest tests/test_replacement_utils.py -v
```

## Coverage

```bash
# Run with coverage (configured in pytest.ini)
pytest . --cov=utils --cov=convert_intro_to_md --cov-report=html --cov-report=term
```

Coverage reports are generated in `htmlcov/`.

## Test Structure

Test modules are listed alphabetically.

---

### Main Script Tests (`test_convert_intro_to_md.py`)

Tests for the public functions in `convert_intro_to_md.py`.

#### `TestConvertIntroToMd`

Tests for `convert_intro_to_md(blocks, intro_locale)`:

- Delegates to `md_renderer.render`.
- The locale argument is forwarded unchanged to the renderer.

#### `TestConvertIntroToTei`

Tests for `convert_intro_to_tei(blocks, intro_id, intro_locale)`:

- Delegates to `tei_renderer.render`.
- `blocks`, `intro_id`, and `locale` are all forwarded to the renderer.

#### `TestGetIntroContext`

Tests for `get_intro_context(intro, output_path)`:

- The locale is extracted as the segment before the first hyphen in the id.
- The full intro id is returned unchanged.
- The output path has the locale appended before the file extension.
- An id with no hyphen is used directly as the locale.
- A missing id leaves the output path unchanged.
- The output file is placed in the same directory as the base path.

#### `TestMain`

Tests for `main()`:

- Exits with code 1 when no arguments are provided.
- Prints a usage example to stderr when no args are given.
- Exits when the JSON has no `intro` key.
- Prints an error message to stderr when the intro array is missing.
- Writes an output file for each intro entry.
- Writes one file per locale for multi-locale input.
- Prints `Converted:` and `Written:` lines for each processed intro.

---

### File Utils Tests (`test_file_utils.py`)

Tests for `FileUtils` in `utils/file_utils.py`.

#### `TestReadJson`

Tests for `read_json(file_path)`:

- A valid JSON file is read and returned as a dict.
- Nested JSON structures are parsed correctly.
- `sys.exit` is called when the file does not exist.
- `sys.exit` is called when the file contains invalid JSON.
- `sys.exit` is called when the top-level JSON value is not a dict.
- An error message is printed to stderr on file-not-found.
- An error message is printed to stderr on invalid JSON.
- An error message is printed to stderr when the JSON is not a dict.

#### `TestWriteFile`

Tests for `write_file(file_path, content)`:

- The given content is written to the specified file.
- Missing parent directories are created automatically.
- Writing to an existing file overwrites its content.
- An empty string can be written without error.
- Multiline content is written correctly.

---

### HTML Parser Tests (`test_html_parser.py`)

Tests for the public `parse_intro` function in `utils/html_parser.py`.

#### `TestParseIntro`

Tests for `parse_intro(intro)`:

- An intro with no content returns an empty list.
- One `Block` is produced for each entry in the content array.
- The `blockId` value is forwarded as the `Block` id.
- A missing `blockHeader` produces `heading=None`.
- A `blockHeader` string is parsed into IR nodes.
- Block content items are converted to IR nodes.
- Block notes are converted to `Note` nodes.
- Multiple blocks with all fields are assembled correctly.

---

### Markdown Renderer Tests (`test_md_renderer.py`)

Tests for the public `render` function in `utils/md_renderer.py`.

#### `TestRender`

Tests for `render(blocks, intro_locale)`:

- An empty block list returns a single newline.
- The output always ends with a newline.
- A block heading is rendered as a level-2 Markdown heading.
- A block with no heading produces no `##` line.
- Rendered block content appears in the output.
- A block rendering to an empty string is excluded from the output.
- Block notes appear as footnote definitions in the output.
- The locale is forwarded to the notes renderer.
- `ReplacementUtils.normalize_whitespace` is applied to the output.
- `ReplacementUtils.separate_adjacent_tables` is applied after normalization.

---

### Replacement Utils Tests (`test_replacement_utils.py`)

Tests for `ReplacementUtils` in `utils/replacement_utils.py`.

#### `TestNormalizeWhitespace`

Tests for `normalize_whitespace(text)`:

- Non-breaking spaces (`\xa0`) are replaced with regular spaces.
- Three or more consecutive newlines are collapsed to two.
- Exactly two consecutive newlines are left unchanged.
- Leading and trailing whitespace is stripped.
- Plain text with no special whitespace is returned unchanged.

#### `TestParseNoteRefId`

Tests for `parse_note_ref_id(anchor_id)`:

- A valid `note-ref-N` id returns its integer note number.
- A multi-digit number is parsed correctly.
- A string not matching the pattern returns `None`.
- An empty string returns `None`.
- A string with extra characters returns `None`.

#### `TestReplaceCrossrefs`

Tests for `replace_crossrefs(html)`:

- A cross-reference anchor is replaced by a synthetic `<awg-crossref>` tag.
- Multiple cross-reference anchors are all replaced.
- Anchors with `id="note-ref-N"` are not replaced.
- Plain text without anchors is returned unchanged.

#### `TestSeparateAdjacentTables`

Tests for `separate_adjacent_tables(text)`:

- A blank line is inserted between two adjacent Markdown tables.
- A blank line is inserted for each adjacent table pair in a sequence.
- Tables already separated by two blank lines are left unchanged.
- Plain text without tables is returned unchanged.
- A single table with no successor is returned unchanged.

#### `TestStripAngularBindings`

Tests for `strip_angular_bindings(html)`:

- A `(click)="..."` attribute is removed from an element.
- Multiple Angular event bindings are all removed.
- HTML without Angular bindings is returned unchanged.
- Plain text is returned unchanged.

---

### TEI Renderer Tests (`test_tei_renderer.py`)

Tests for the public `render` function in `utils/tei_renderer.py`.

#### `TestRender`

Tests for `render(blocks, intro_id, intro_locale)`:

- Returns a `str`.
- The output begins with an XML declaration.
- The root element is `<TEI>` in the TEI namespace.
- The blocks list is forwarded to the notes lookup builder.
- `intro_id` and `intro_locale` are forwarded to the TEI header builder.
- The blocks list and locale are forwarded to the TEI body builder.
- The notes lookup is reset to an empty dict after render completes.

## Example Test Run Output

```
========================= test session starts ==========================
platform ...
collected N items

tests/test_convert_intro_to_md.py ....
tests/test_file_utils.py .............
tests/test_html_parser.py ....................................................
tests/test_md_renderer.py ......
tests/test_replacement_utils.py ..............................
tests/test_tei_renderer.py .............

========================== N passed in Xs ============================
```
