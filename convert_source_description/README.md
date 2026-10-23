# HOW TO ... convert source-descriptions from WORD to JSON?

## WHY?

Source descriptions, that are only presented via the online edition, should be converted into machine-readable format as automatically as possible instead of being converted manually. 

The python script `convert_source_description.py` will create a JSON file `source-description.json` from a source description provided in WORD. It uses BeautifulSoup to parse the WORD document as HTML and extract the wanted data.

## HOW?

> [!NOTE]
> This converter uses latest Python version (3.13 for now). Make sure to have Python installed on your system, or get it from here: [https://www.python.org/downloads/](https://www.python.org/downloads/)

### Preparation

* Make sure that you have a source description file in WORD (`.docx`) formatted according to these [style guidelines](how_to/word-formatting.md).
* Make sure that you have created a fork from this GitHub repository `awg-utils` and you have a local copy of this fork on your machine.
* Make sure that you have a local copy of [`awg-app`](https://github.com/webern-unibas-ch/awg-app) **next to** `awg-utils` (both folders in the same parent folder, e.g. `.../webern-unibas-ch/awg-app` and `.../webern-unibas-ch/awg-utils`). The converter reads the glyph names from there (see [Glyphs](#glyphs)). If `awg-app` lives somewhere else, pass the path with `--glyphs-data` (see below).
* In your file explorer, navigate to your local folder `awg-utils`, right-click on it, and open it with **VSCode** editor.
* Open new terminal in **VSCode** editor (preferably **Git Bash**, following paths and directions are using Git Bash syntax).
* In the terminal, change directory to the subfolder `convert_source_description` by typing: `cd convert_source_description` (it should be sufficient to type `cd conv` + `TAB` key, the console autocompletes the name on its own). This subfolder is where the conversion script lives.
* In the terminal, create and activate a virtual environment (see [Virtual Environments](../README.md#virtual-environments) in the main README for details):
  ```bash
  python -m venv .venv   # skip if already created
  source .venv/Scripts/activate
  ```
* In the terminal, type `pip install -r requirements.txt --require-hashes` to install the latest library versions with verified hashes.

Now you're good to run the conversion script.

### Conversion

* In the terminal, type `python convert_source_description.py <SOURCEDESC_FILEPATH>`.
* Replace `<SOURCEDESC_FILEPATH>` with the full path to your source-description file, including the `.docx` extension.

> [!TIP]
> If you have the source-description in the same directory as the python script, use `./` at the start of the path.

#### Examples (using **Git Bash** syntax):

* External directory: `python convert_source_description.py /c/Users/<USERNAME>/AWG/SourceDescriptions/AWG_op19_B.docx`
* Same directory: `python convert_source_description.py ./AWG_op19_B.docx`
* `awg-app` in another place: `python convert_source_description.py ./AWG_op19_B.docx --glyphs-data /c/Users/<USERNAME>/awg-app/src/app/views/edition-view/data/edition-glyphs.data.ts`

### Glyphs

Glyph names in square brackets in the textcritical comments (e.g. `[f]`, `[#]`, `[Halbe Note]`) are converted to `<span class='glyph …'>{{ref.getGlyph('[f]')}}</span>`. A name directly followed by a hyphen (e.g. `[b]-Vorzeichen`) is left as it is.

The list of glyph names is not kept in this tool. It is read from the `alt` values of `EDITION_GLYPHS_DATA` in `awg-app/src/app/views/edition-view/data/edition-glyphs.data.ts`, so a glyph added there is converted here as well. The CSS class comes from the section comment of the entry in that file:

| Section in `edition-glyphs.data.ts` | CSS class     |
| ----------------------------------- | ------------- |
| `ACCIDENTALS`                       | `glyph accid` |
| `NOTE VALUES`                       | `glyph note`  |
| any other section                   | `glyph`       |

If the file is missing or contains no glyph entry, the converter stops with an error message.
