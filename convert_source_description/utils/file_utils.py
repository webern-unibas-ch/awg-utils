"""
Utility functions for file operations. This includes reading from WORD and writing to JSON.
"""

import json
import os
from typing import Dict

import mammoth


############################################
# Public class: FileUtils
############################################
class FileUtils:
    """A class that contains utility functions for file operations like reading or writing."""

    ############################################
    # Public class function: read_html_from_word_file
    ############################################
    def read_html_from_word_file(self, file_path: str) -> str:
        """
        Reads a Word file in .docx format and returns its content as an HTML string.

        Args:
            file_path (str): The path to the Word file, including the .docx extension.

        Returns:
            str: The content of the Word file as an HTML string.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError("File not found: " + file_path)

        with open(file_path, "rb") as docx_file:
            try:
                style_map = """
                u => u
                small-caps => span.smallcaps
                """
                result = mammoth.convert_to_html(
                    docx_file, style_map=style_map)

                return result.value  # The generated HTML
            except ValueError as error:
                raise ValueError('Error converting file: ' +
                                 str(error)) from error

    ############################################
    # Public class function: write_json
    ############################################
    def write_json(self, data: Dict, file_path: str) -> None:
        """
        Serializes a data dictionary as a JSON formatted string and writes it to a file.

        Args:
            data (Dict): The data dictionary to be serialized and written.
            file_path (str): The path to the file to be written, without the .json extension.

        Returns:
            None
        """
        # Serializing json
        json_object = json.dumps(data, indent=4, ensure_ascii=False).encode(
            'utf8').decode('utf8')

        # Writing to target file
        target_file_name = file_path + ".json"
        try:
            with open(target_file_name, "w", encoding='utf-8') as target_file:
                target_file.write(json_object)
                target_file.write("\n")
            print(f"Data written to {target_file_name} successfully.")
        except IOError:
            print(f"Error writing data to {target_file_name}.")
