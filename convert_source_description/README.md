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
* In your file explorer, navigate to your local folder `awg-utils`, right-click on it, and open it with **VSCode** editor.
* Open new terminal in **VSCode** editor (preferably **Git Bash**, following paths and directions are using Git Bash syntax).
* In the terminal, change directory to the subfolder `convert_source_description` by typing: `cd convert_source_description` (it should be sufficient to type `cd conv` + `TAB` key, the console autocompletes the name on its own). This subfolder is where the conversion script lives.

Now you're good to run the conversion script.

### Conversion

* In the terminal, type `pip install --require-hashes -r requirements.txt` to install the latest library versions with verified hashes.
* In the terminal, type `python convert_source_description.py <SOURCEDESC_DIRECTORY> <SOURCEDESC_FILENAME>`.
* Replace `<SOURCEDESC_DIRECTORY>` with the path to your local directory that contains the source-description (with `/` at the end).
* Replace `<SOURCEDESC_FILENAME>` with the file name without the file type ending `.docx`.

> [!TIP]
> If you have the source-description in the same directory as the python script, use `./` as `<SOURCEDESC_DIRECTORY>`.

#### Examples (using **Git Bash** syntax):

* External directory: `python convert_source_description.py /c/Users/<USERNAME>/AWG/SourceDescriptions/ AWG_op19_B`
* Same directory: `python convert_source_description.py ./ AWG_op19_B`
