# HOW TO ... convert source-descriptions from WORD to JSON?

## WHY?

Source descriptions, that are only presented via the online edition, should be converted into machine-readable format as automatically as possible instead of being converted manually. 

The python script `convert_source_description.py` will create a JSON file `source-description.json` from a source description provided in WORD. It uses BeautifulSoup to parse the WORD document as HTML and extract the wanted data.

## HOW?

### Preparation of the WORD document

* The WORD document requires a certain structure to be converted properly. Some of those structural elements are crucial and should be followed as closely as possible.

#### HEAD
* Especially the *head* of the document, i.e. its first 5 lines, is very fragile, since there are no indications of the actual content beside its order and formatting.
* These 5 lines are expected to consist of the following (separated by blank lines):
  
  1) Any kind of "heading". (Please note that this should be plain text and have no special formatting. The heading itself is ignored in the conversion and serves only internal purposes.)
  2) The source siglum in bold formatting, e.g. **B**, **G<sup>H</sup>**, **E<sup>F1–2</sup>**. Missing sources are indicated by squared brackets, e.g. **\[B\]**, **\[G<sup>H</sup>\]**, **\[E<sup>F1–2</sup>\]**. 
  3) The type of the source, e.g. "Reihentabelle und Skizze für *Ein Titelstück*.".
  4) The location of the source, e.g., "CH-Bps, Sammlung Anton Webern."
  5) The general description of the source, e.g., "1 Blatt. Rissspuren am rechten Rand: von Bogen abgetrennt und beschnitten. Abriss an der oberen rechten Ecke. Zwei Risse am rechten Rand."

* Lines 3–5 can contain any kind of formatting and should have a final dot.

  Example:

  <img width="263" alt="SourceDesc_Meta" src="https://github.com/webern-unibas-ch/awg-utils/assets/21059419/a8b9aea2-e716-4c28-b3ce-dac243a025a2">

#### CATEGORIES
* The following lines contain more detailed descriptions of certain aspects of the source, like writing material, titles or annotation.
* These lines are less fragile in the conversion since they are supposed to start with a "category name" separated by colon from the actual content.
* These categories may include (in the order of their appearance):

  1) `Beschreibstoff:`
  2) `Schreibstoff:`
  3) `Titel:`
  4) `Datierung:`
  5) `Paginierung:`
  6) `Taktzahlen:`
  7) `Besetzung:`
  8) `Eintragungen:`

* The content of all these categories can contain any kind of formatting and should have a final dot. Multiple entries per category should be separated by semicolon.
  
  Example:
  
  <img width="263" alt="SourceDesc_Categories" src="https://github.com/webern-unibas-ch/awg-utils/assets/21059419/75480618-02b3-497f-9b4d-fa9f9b472add">

#### CONTENT

* The final, and often most extended "category" of the source description, is the "content" section. It describes the content units found in the source.
* This section of the WORD document should adopt the following structure:

  1) Main cateogry name: "Inhalt:"
  2) Some naming of the content unit, e.g. "I „Das dunkle Herz“ M 314: einzige Textfassung:". This may include sketch sigla which should appear in bold formatting, e.g. "**M 286 Sk# / M 287 Sk#** (Reihentabelle op. 19):" 
	3) Indication of the folio or page on which the content unit can be found, including system and measure numbers: "Bl. 1r 	System 8–9 (rechts): T. 15.", "S. 2  System 1–2: T. 18." This line starts with a `TAB`.
  4) If needed, more systems on the same folio/page can be appended in the following lines. Multiple line are starting with a double `TAB` and are separated by semicolon at the line ending. The final system line has a dot.

  Example: 

  <img width="182" alt="SourceDesc_Content" src="https://github.com/webern-unibas-ch/awg-utils/assets/21059419/5cbd66d8-5652-4feb-914e-b83f7ffa35b3">

> [!CAUTION]
> There must be a TAB before the "Bl." or "S.". There must be another TAB before the word "System", and a colon after the system number(s).

#### END

* If there is no further content in the WORD document, there is no need for further adaption. However, if there is further content, like textcritical comments or correction lists, you should make sure that, after the source description, you have a new line starting with `Textkritischer Kommentar:`. This line indicates the end of the source description for the script and prevents it from trying to parse the following lines. 

### Technical Preparation

* Make sure that you have created a fork from this GitHub repository `awg-utils` and you have a local copy of this fork on your machine.
* In your file explorer, navigate to your local folder `awg-utils`, right-click on it, and open it with **VSCode** editor.
* Open new terminal in **VSCode** editor (preferably **Git Bash**, following paths and directions are using Git Bash syntax).
* In the terminal, change directory to the subfolder `convert_source_description` by typing: `cd convert_source_description` (it should be sufficient to type `cd conv` + `TAB` key, the console autocompletes the name on its own). This subfolder is where the conversion script lives.

Now you're good to run the conversion script.

### Conversion

* In the terminal, type `python convert_source_description.py <SOURCEDESC_DIRECTORY> <SOURCEDESC_FILENAME>`.
* Replace `<SOURCEDESC_DIRECTORY>` with the path to your local directory that contains the source-description (with `/` at the end).
* Replace `<SOURCEDESC_FILENAME>` with the file name without the file type ending `.docx`.

> [!TIP]
> If you have the source-description in the same directory as the python script, use `./` as `<SOURCEDESC_DIRECTORY>`.

#### Examples (using **Git Bash** syntax):

* External directory: `python convert_source_description.py /c/Users/<USERNAME>/AWG/SourceDescriptions/ AWG_op19_B`
* Same directory: `python convert_source_description.py ./ AWG_op19_B`
