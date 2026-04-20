"""String and HTML tag stripping helpers for conversion utilities."""

from typing import List


############################################
# Public class: StrippingUtils
############################################
class StrippingUtils:
    """A class that contains utility functions for string and HTML tag stripping."""

    ############################################
    # Public class function: strip_by_delimiter
    ############################################
    @staticmethod
    def strip_by_delimiter(input_str: str, delimiter: str) -> List[str]:
        """Splits a string by a delimiter and returns a list of stripped substrings.

        Args:
            input_str (str): The input string to split and strip.
            delimiter (str): The delimiter to split the string by.

        Returns:
            List[str]: A list of stripped substrings.
        """
        stripped_substring_list: List[str] = [
            s.strip() for s in input_str.split(delimiter)
        ]
        return stripped_substring_list

    ############################################
    # Public static method: strip_label_from_text
    ############################################
    @staticmethod
    def strip_label_from_text(text: str, label: str) -> str:
        """
        Strips a label prefix (and any immediately following non-breaking space)
        from the given text, also removing leading tabs and surrounding whitespace.

        Args:
            text (str): The text to strip the label from.
            label (str): The label string to remove (e.g. 'Bl.' or 'S.').

        Returns:
            str: The text with the label removed and whitespace stripped.
        """
        text = text.lstrip("\t")
        text = text.replace(label + "\xa0", "").strip()
        text = text.replace(label, "").strip()
        return text

    ############################################
    # Public class function: strip_tag
    ############################################
    @staticmethod
    def strip_tag(content: str, tag_str: str) -> str:
        """Strips opening and closing tags from an HTML/XML string and returns the
        content within the tags as a string.

        Args:
            content (str): The input string.
            tag_str (str): The name of the tag to strip.

        Returns:
            str: The content within the specified tags,
                with leading and trailing whitespace removed.
        """
        if content is None:
            print(f"Content is None for tag_str: {tag_str}")
            return ""

        stripped_str = str(content)

        # Strip opening and closing tags from input (incl. attributes in opening tag)
        closing_tag = "</" + tag_str + ">"
        opening_tag = "<" + tag_str
        opening_tag_start_index = stripped_str.find(opening_tag)
        opening_tag_end_index = stripped_str.find(">", opening_tag_start_index) + 1

        if opening_tag_start_index == -1:
            # Preserve plain text when no tags are present; otherwise match prior behavior.
            return stripped_str.strip() if "<" not in stripped_str else ""

        stripped_str = stripped_str[opening_tag_end_index:]
        stripped_str = stripped_str.removesuffix(closing_tag)

        # Strip trailing white space
        stripped_str = stripped_str.strip()

        return stripped_str

    ############################################
    # Public class function: strip_tag_and_clean
    ############################################
    @staticmethod
    def strip_tag_and_clean(content: str, tag: str) -> str:
        """Strips opening and closing tags from an HTML string
        and strips surrounding paragraph tags.

        Args:
            content (str): The input string.
            tag (str): The name of the tag to strip.

        Returns:
            str: The content within the specified tags,
                with leading and trailing whitespace removed.
        """
        stripped_content = StrippingUtils.strip_tag(content, tag)
        stripped_content = StrippingUtils.strip_tag(stripped_content, "p")
        return stripped_content.replace("</p><p>", " <br /> ")
