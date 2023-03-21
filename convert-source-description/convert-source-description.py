"""Convert a source description from Word to JSON.

This script reads in a Word file (.docx) with source descriptions 
and converts it to to a JSON file (.json).

This script requires that `bs4` (BeautifulSoup) and `mammoth` be installed within the Python
environment you are running this script in. It also requires the `utils.py` file with the 
`ConversionUtils` class to be in the same directory.

This file can also be imported as a module and calls the following
functions:

    * convertSourceDescription - converts a source description from Word to JSON
    * main - the main function of the script
"""

import argparse

from bs4 import BeautifulSoup
from utils import ConversionUtils


def convertSourceDescription(directory: str, fileName: str):
    """Convert a source description from Word to JSON.

    Args:
        directory (str): The directory where the Word file is located.
        inputFile (str): The Word file to extract the source description from.

    Returns
        A JSON file with the source description.
    """

    # Define file path
    filePath = directory + fileName

    # Get HTML from Word file
    html = ConversionUtils.readHtmlFromWordFile(filePath)

    # Parse HTML
    soup = BeautifulSoup(html, 'html.parser')
                                
    # Find all p tags
    paras = soup.find_all('p')

    # Create the full sourceList object
    sourceList = ConversionUtils.createSourceList(paras)

    #pprint(sourceList)

    # Output
    ConversionUtils.writeJson(sourceList, filePath)



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'directory',
        type=str,
        help="The directory where the Word file is located."
    )
    parser.add_argument(
        'fileName',
        type=str,
        help="The Word file to extract the source description from (without the .docx extension)."
    )
    args = parser.parse_args()
    convertSourceDescription(args.directory, args.fileName)


if __name__ == "__main__":
    main()