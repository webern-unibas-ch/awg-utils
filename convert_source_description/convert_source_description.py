"""Convert a source description from Word to JSON.

This script reads in a Word file (.docx) with source descriptions
and converts it to to a JSON file (.json).

This script requires that `bs4` (BeautifulSoup) and `mammoth` be installed within the Python
environment you are running this script in. It also requires the `utils.py` file with the
`ConversionUtils` class to be in the same directory.

The script expects a Word file input structured in the following way:

    <Heading> XYZ

    <Single letter SIGLUM in bold formatting> A

    <Paragraph with the TYPE of the source> Skizzen zu ...

    <Paragraph with the LOCATION of the source> CH-Bps, Sammlung Anton Webern.

    <Paragraph with the status DESCRIPTION of the source> 1 Blatt: Das Blatt ist ...

    <Multiple paragraphs with labels indicating the expected content. These labels can include:

        * Beschreibstoff:
        * Schreibstoff:
        * Titel:
        * Datierung:
        * Paginierung:
        * Taktzahlen:
        * Besetzung:
        * Eintragungen:
        * Inhalt:
    >

    <Section with the CONTENT of the source including the following information:
        <LABEL of the content item in bold formatting (TYPE of item):>
            <[TAB] FOLIO label [TAB] SYSTEM numbers: T. MEASURE numbers>
                <{TAB][TAB] if needed, multiple lines with information about systems and measures>
    Inhalt:
    M* 408 (Tintenniederschrift von Studienkomposition für Klavier M* 408):
    ->  Bl. 1r -> 	System 2–5: T. 1–9;
    ->         ->   System 7–10: T. 10–17;
    ->         ->   System 12–15: T. 18–25.
    M 22 Sk1 (Skizze zu Studienkomposition für Klavier M 22: Thema):
    ->  Bl. 1r	->  System 22–23: T. 1–8.
    >
"""

import argparse

from bs4 import BeautifulSoup
from file_utils import FileUtils
from utils import ConversionUtils


def convert_source_description(directory: str, file_name: str):
    """Convert a source description from Word to JSON.

    Args:
        directory (str): The directory where the Word file is located.
        inputFile (str): The Word file to extract the source description from.

    Returns
        A JSON file with the source description.
    """

    file_utils = FileUtils()
    conversion_utils = ConversionUtils()

    # Define file path
    file_path = directory + file_name

    # Get HTML from Word file
    html = file_utils.read_html_from_word_file(file_path)

    # Parse HTML
    soup = BeautifulSoup(html, 'html.parser')

    # Create the full sourceList object
    source_list = conversion_utils.create_source_list(soup)

    # Create the full textcritics object
    textcritics = conversion_utils.create_textcritics(soup)

    # Output
    file_utils.write_json(source_list, file_path + '_source-description')
    file_utils.write_json(textcritics, file_path + '_textcritics')


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'directory',
        type=str,
        help="The directory where the Word file is located."
    )
    parser.add_argument(
        'file_name',
        type=str,
        help="The Word file to extract the source description from (without the .docx extension)."
    )
    args = parser.parse_args()
    convert_source_description(args.directory, args.file_name)


if __name__ == "__main__":
    main()
