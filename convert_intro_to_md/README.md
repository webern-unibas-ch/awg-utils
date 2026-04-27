# HOW TO ... convert an AWG intro JSON to Markdown?

## WHY?

The online edition stores introductory texts in a JSON format where content is represented as HTML fragments inside a `blockContent` array. To make these texts usable outside the Angular application — for example for editing, reviewing, or archiving — they need to be converted to plain Markdown.

The Python script `convert_intro_to_md.py` reads an `intro.json` file and produces one Markdown output file per locale found in the `intro` array (e.g. `intro_de.md`, `intro_en.md`). Angular-specific HTML attributes are stripped, footnote references and cross-references are converted to Markdown footnote syntax, and footnotes are appended as a numbered section at the end.

## HOW?

> [!NOTE]
> This script uses the latest Python version (3.13 for now). Make sure to have Python installed on your system, or get it from here: [https://www.python.org/downloads/](https://www.python.org/downloads/)

### Preparation

* Make sure that you have an `intro.json` file ready.
* Make sure that you have created a fork from this GitHub repository `awg-utils` and you have a local copy of this fork on your machine.
* In your file explorer, navigate to your local folder `awg-utils`, right-click on it, and open it with **VSCode** editor.
* Open a new terminal in **VSCode** editor (preferably **Git Bash**, following paths and directions are using Git Bash syntax).
* In the terminal, change directory to the subfolder `convert_intro_to_md` by typing: `cd convert_intro_to_md` (it should be sufficient to type `cd conv` + `TAB` key, the console autocompletes the name on its own). This subfolder is where the conversion script lives.
* In the terminal, create and activate a virtual environment (see [Virtual Environments](../README.md#virtual-environments) in the main README for details):
  ```bash
  python -m venv .venv   # skip if already created
  source .venv/Scripts/activate
  ```
* In the terminal, type `pip install -r requirements.txt --require-hashes` to install the latest library versions with verified hashes.

Now you're good to run the conversion script.

### Conversion

* In the terminal, type `python convert_intro_to_md.py <path>/<to>/intro.json`.
* Replace `<path>/<to>/intro.json` with the path to your intro JSON file.

> [!TIP]
> If you have the `intro.json` in the same directory as the python script, you can use a relative path.

#### Examples (using **Git Bash** syntax):

* External directory: `python convert_intro_to_md.py /c/Users/<USERNAME>/AWG/intro.json`
* Same directory: `python convert_intro_to_md.py ./intro.json`

### Output

The script writes one Markdown file per locale next to the input file, named after it with the locale appended before the extension. For example, given `intro.json` with German and English entries:

```
intro_de.md
intro_en.md
```

Each file contains the converted Markdown text, with:
- Section headers rendered as `## <header>`
- Consecutive small-text paragraphs (`<p class="small">`, except list variants) combined into a single blockquote (`> ...`)
- HTML tables converted to Markdown tables
- Footnote references converted to `[^N]`
- Footnote back-references (cross-references within the text) converted to inline links `[N](#fnN)`
- Footnotes appended as a `## Notes` / `## Anmerkungen` section at the end
