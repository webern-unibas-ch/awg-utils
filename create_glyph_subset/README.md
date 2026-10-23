# HOW TO ... create the glyph font subset for the AWG Online Edition?

## WHY?

The edition view of the AWG Online Edition (awg-app) shows musical symbols (accidentals, dynamics, note values, …) with the SMuFL font [Bravura](https://github.com/steinbergmedia/bravura). The complete font is about 300 KB, but the app needs only the few glyphs listed in `EDITION_GLYPHS_DATA`.

The Python script `create_glyph_subset.py` reads these glyphs from awg-app and creates a small WOFF2 subset of Bravura 1.380 (about 8 KB) with exactly these glyphs.

Bravura is licensed under the [SIL Open Font License 1.1](fonts/bravura-1.380/OFL.txt) with the Reserved Font Name "Bravura". A modified version (such as a subset) must not use this name. The subset is therefore renamed:

| Field                        | Value                                                |
| ---------------------------- | ---------------------------------------------------- |
| Family                       | `AWG Edition Glyphs`                                 |
| Style                        | `Regular`                                            |
| PostScript name              | `AWGEditionGlyphs-Regular`                           |
| Description (name ID 10)     | `Subset of Bravura 1.380 for the AWG Online Edition` |

The copyright of Steinberg Media Technologies GmbH is kept. The same note is inserted after the copyright statement, and the license text follows.

## HOW?

> [!NOTE]
> This script uses the latest Python version (3.13 for now). Make sure to have Python installed on your system, or get it from here: [https://www.python.org/downloads/](https://www.python.org/downloads/)

### Preparation

* Make sure that you have a local copy of `awg-app` next to `awg-utils` (or know the path to it).
* Make sure that you have created a fork from this GitHub repository `awg-utils` and you have a local copy of this fork on your machine.
* In your file explorer, navigate to your local folder `awg-utils`, right-click on it, and open it with **VSCode** editor.
* Open a new terminal in **VSCode** editor (preferably **Git Bash**, following paths and directions are using Git Bash syntax).
* In the terminal, change directory to the subfolder `create_glyph_subset` by typing: `cd create_glyph_subset`.
* In the terminal, create and activate a virtual environment (see [Virtual Environments](../README.md#virtual-environments) in the main README for details):
  ```bash
  python -m venv .venv   # skip if already created
  source .venv/Scripts/activate
  ```
* In the terminal, type `pip install -r requirements.txt --require-hashes` to install the latest library versions with verified hashes.

Now you're good to run the script.

### Creating the subset

* In the terminal, type `python create_glyph_subset.py <path>/<to>/edition-glyphs.data.ts --out <output folder>`.
* Replace `<path>/<to>/edition-glyphs.data.ts` with the path to the glyph data file of awg-app (`src/app/views/edition-view/data/edition-glyphs.data.ts`).
* Replace `<output folder>` with the folder the three output files should be written to. It is created if it doesn't exist.

#### Example (using **Git Bash** syntax):

```bash
python create_glyph_subset.py ../../awg-app/src/app/views/edition-view/data/edition-glyphs.data.ts --out ~/Desktop/awg-edition-glyphs
```

> [!WARNING]
> Choose an output folder outside of `awg-utils` (or directly the target folder in awg-app), so the generated files don't end up in this repository.

> [!TIP]
> Add `--preview` to also write `AWGEditionGlyphs-preview.html` to the output folder (see [Preview](#preview) below).

> [!TIP]
> By default, the script uses the Bravura font bundled in [`fonts/bravura-1.380/`](fonts/bravura-1.380/). Use `--font <path>/Bravura.woff2` to take another source font. An `OFL.txt` must be placed in the same folder as that font.

### Input

The script collects every `\uXXXX` escape inside the `hex` string values (in single, double or backtick quotes) of `edition-glyphs.data.ts`. Escapes in comments or other properties are ignored.

* Values with several escapes add all of them (e.g. `SUBITO_PIANO: '\uE524\uE520'`).
* Codepoints used more than once are included only once.
* Literal characters are not included. For example, the space in `NOTE_HALF_DOTTED: '\uE1D3 \uE1E7'` is not part of the subset. The browser renders it with the next font in the `font-family` stack.

The script stops with an error if no codepoint is found, if a codepoint is not contained in the source font, or if there is no `OFL.txt` next to the source font. The license is copied before the font is written, so a font never ends up without its license.

### Output

The script writes three files to the output folder:

```
AWGEditionGlyphs-Regular.woff2   the font subset
AWGEditionGlyphs.json            manifest: font names, font file and its SHA-256, source, note, count and list of codepoints (U+XXXX)
OFL.txt                          the license of Bravura, which also applies to the subset
```

The manifest field `sha256` (right after `file`) is the SHA-256 hash of the written `AWGEditionGlyphs-Regular.woff2`, as 64 lowercase hex characters. It is computed from the file on disk after the font has been written, and the manifest is written only afterwards, so hash and font always belong together. `OFL.txt` and the preview are not part of the hash. awg-app (`yarn check:glyphs`) compares this hash with the font file it ships, so a stale font next to an up-to-date manifest is detected. Therefore always copy font and manifest together.

The output is reproducible. Running the script again with the same input produces byte-identical files, so a regenerated font only shows up as a change in awg-app if the glyph list has changed.

Copy all three files into awg-app. `OFL.txt` has to be distributed together with the font.

### Preview

With `--preview`, the script additionally writes `AWGEditionGlyphs-preview.html`. Open it in a browser (Git Bash: `start <output folder>/AWGEditionGlyphs-preview.html`) to check the subset visually:

- The font names from the written font file, its size, and how many of the codepoints are mapped in the font (`26 / 26 in cmap`).
- One card per entry of `EDITION_GLYPHS_DATA`, grouped by the section comments of the data file, with the glyph, its key (e.g. `DOUBLE_FLAT`), the alt text and the codepoint(s). Multi-glyph entries are shown as in the app (e.g. `SUBITO_PIANO` as two glyphs). A card whose glyph is missing in the font gets a red border.
- An inline sample with dynamics glyphs next to running text, to check size and baseline.

The font is embedded in the page, so it works when opened directly from disk. The preview is for checking only. Do **not** copy it into awg-app.
