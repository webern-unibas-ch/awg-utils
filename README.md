# awg-utils

![Pylint](https://github.com/webern-unibas-ch/awg-utils/actions/workflows/pylint.yml/badge.svg)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/webern-unibas-ch/awg-app)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/webern-unibas-ch/awg-utils/badge)](https://scorecard.dev/viewer/?uri=github.com/webern-unibas-ch/awg-utils)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/webern-unibas-ch/awg-utils)

A repo for utility scripts of the Anton Webern Gesamtausgabe.

---

## Virtual Environments

### Activating a Virtual Environment

1. Navigate to the target folder:

```bash
cd /d/Repositories/webern-unibas-ch/awg-utils/compare_pdfs
```

2. Create a virtual environment:

```bash
python -m venv .venv
```

3. Activate the virtual environment:

```bash
source .venv/Scripts/activate
```

> [!NOTE]
> Only for Devs: To create (or update) dependency files, install pip-tools via `python -m pip install pip-tools`
> 
> Then create/update the `requirements.txt` file via `pip-compile --generate-hashes --strip-extras requirements.in`


4. Install the dependencies:

```bash
pip install -r requirements.txt --require-hashes
```


### Deactivating a Virtual Environment

To deactivate the currently active virtual environment, simply run:

```bash
deactivate
```

## [SCRIPT]: convert_intro_to_md

The python script in this folder converts an AWG intro JSON file (with HTML block content) to Markdown, producing one output file per locale.

See [HOW TO ... convert an AWG intro JSON to Markdown?](convert_intro_to_md/README.md)

## [SCRIPT]: convert_source_description

The python script in this folder converts a source description given in Word format from .docx to .json. 

See [HOW TO ... convert source-descriptions from WORD to JSON?](convert_source_description/README.md)

## [SCRIPT]: compare_pdfs

The python script in this folder compares the pages of two pdfs and highlights any diffs.

See [HOW TO ... compare two PDF files and highlight differences?](compare_pdfs/README.md)

## [SCRIPT]: unify_ids

The python scripts in this folder unify SVG group IDs for TKK and link-box elements across JSON textcritics and SVG files.

See [HOW TO ... unify IDs in SVG and JSON files?](unify_ids/README.md)

## Repository structure

![Visualization of the codebase](./diagram.svg)
