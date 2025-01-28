"""Compare two PDF files and highlight differences between them.

The script extracts the pages of two PDF files as images, converts them to grayscale,
and highlights any differences in a separate diff image. The diff images are saved
in a specified directory.
"""
import argparse
import datetime
import logging
import os
from concurrent.futures import ThreadPoolExecutor
import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image


def extract_images_from_pdf(pdf_path: str, dpi=350) -> list[Image.Image]:
    """
    Extract images from a PDF file.

    Args:
        pdf_path (str): Path to the PDF file.
        dpi (int): Dots per inch applied in image extraction.

    Returns:
        list[Image.Image]: List of images extracted from the PDF.
    """
    # Use pdf2image to extract images from the PDF file
    logging.info("Extracting images from PDF: %s", pdf_path)
    images = convert_from_path(pdf_path, dpi)

    return images


def convert_to_grayscale(image: Image.Image) -> np.ndarray:
    """
    Convert an image to grayscale.

    Args:
        image: Input image.

    Returns:
        numpy.ndarray: Grayscale image.
    """
    # Convert PIL Image to NumPy array
    image_np = np.array(image)

    # Check if the image has 3 channels (BGR), i.e., it is not grayscale already
    if len(image_np.shape) == 3:
        return cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)

    return image_np


def highlight_differences(
    image1: np.ndarray, image2: np.ndarray, threshold=75
) -> tuple[np.ndarray, bool]:
    """
    Highlight differences between two given grayscale images.

    Args:
        image1 (numpy.ndarray): First grayscale image.
        image2 (numpy.ndarray): Second grayscale image.
        threshold (int): Threshold value for difference detection.

    Returns:
        tuple: Highlighted image and a boolean indicating if differences were found.
    """
    # Calculate the absolute difference between the two images
    diff = cv2.absdiff(image1, image2)

    # Apply a binary threshold to the difference image
    # Pixels with a value greater than threshold are set to 255 (white), others are set to 0 (black)
    _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

    # Find contours in the thresholded image
    # Contours are the boundaries of the white regions in the binary image
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Convert the second image back to BGR (color) format
    image2_bgr = cv2.cvtColor(image2, cv2.COLOR_GRAY2BGR)

    # Loop over the contours
    for contour in contours:
        # Get the bounding rectangle for each contour
        (x, y, w, h) = cv2.boundingRect(contour)

        # Draw a red rectangle around the contour on the second image
        # The color (0, 0, 255) represents red in BGR format
        cv2.rectangle(image2_bgr, (x, y), (x + w, y + h), (0, 0, 255), 2)

    return image2_bgr, len(contours) > 0


def compare_page(images1: list[Image.Image], images2: list[Image.Image],
                 page_num: int, diff_dir: str, threshold=75) -> bool:
    """
    Compare a single page from two given lists of images (PIL.Image.Image),
    highlight differences and save the output as image.

    Args:
        images1 (list): List of images from the first PDF.
        images2 (list): List of images from the second PDF.
        page_num (int): Page number to compare.
        diff_dir (str): Diff directory to save the output images.
        threshold (int): Threshold value for difference detection.

    Returns:
        bool: True if differences were found, False otherwise.
    """
    logging.info("Comparing page %d ...", page_num)

    # Convert the images to grayscale
    gray_image1 = convert_to_grayscale(images1[page_num - 1])
    gray_image2 = convert_to_grayscale(images2[page_num - 1])

    # Highlight differences between the two images
    highlighted_image, has_differences = highlight_differences(gray_image1, gray_image2, threshold)

    # Save the highlighted image
    cv2.imwrite(f"{diff_dir}/diff_page_{page_num}.png", highlighted_image)

    return has_differences


def compare_pages_in_parallel(images1: list[Image.Image], images2: list[Image.Image],
                              diff_dir: str, threshold: int) -> list[int]:
    """
    Compare the pages of two PDFs in parallel and return the list of pages with differences.

    Args:
        images1 (list): List of images from the first PDF.
        images2 (list): List of images from the second PDF.
        diff_dir (str): Diff directory to save the output images.
        threshold (int): Threshold value for difference detection.

    Returns:
        list[int]: List of pages with differences.
    """
    pages_with_changes: list[int] = []
    with ThreadPoolExecutor() as executor:
        results = list(
            executor.map(
                lambda i: compare_page(
                    images1, images2, i + 1, diff_dir, threshold
                ),
                range(len(images1))
            )
        )

    # Check if differences were found on each page
    for i, has_differences in enumerate(results):
        if has_differences:
            pages_with_changes.append(i + 1)

    return pages_with_changes


def create_diff_dir(output_path: str) -> str:
    """
    Create the output diff directory if it doesn't exist.

    Args:
        output_path (str): Path to the output directory.

    Returns:
        str: Path to the output diff directory.
    """
    diff_dir = os.path.join(output_path, "diff_images")
    os.makedirs(diff_dir, exist_ok=True)

    return diff_dir


def log_and_write_diff_results(pages_with_changes: list[int], diff_dir: str, settings: dict):
    """
    Log the pages with differences and write to a TXT file.

    Args:
        pages_with_changes (list): List of pages with differences.
        diff_dir (str): Path to diff directory.
        settings (dict): Dictionary containing the following keys:
            - pdf1_path (str): Path to the first PDF file.
            - pdf2_path (str): Path to the second PDF file.
            - output_path (str): Directory to save the output images.
            - dpi (int): Dots per inch for image extraction.
            - threshold (int): Threshold value for difference detection.
    """
    diff_txt_path = os.path.join(diff_dir, "diff.txt")
    with open(diff_txt_path, "w", encoding='utf-8') as diff_file:
        diff_file.write("PDF Comparison Results\n")
        diff_file.write("=" * 50 + "\n")
        diff_file.write(f"PDF 1: {settings['pdf1_path']}\n")
        diff_file.write(f"PDF 2: {settings['pdf2_path']}\n")
        diff_file.write(f"DPI: {settings['dpi']}\n")
        diff_file.write(f"Threshold: {settings['threshold']}\n")
        diff_file.write(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        diff_file.write("=" * 50 + "\n")
        if pages_with_changes:
            message = f"Diffs detected on pages: {', '.join(map(str, pages_with_changes))}"
            logging.info(message)
            diff_file.write(message + "\n")
        else:
            message = "No diffs detected."
            logging.info(message)
            diff_file.write(message + "\n")


def compare_pdfs(settings: dict):
    """
    Compare two PDF files and highlight differences.

    Args:
        settings (dict): Dictionary containing the following keys:
            - pdf1_path (str): Path to the first PDF file.
            - pdf2_path (str): Path to the second PDF file.
            - output_path (str): Directory to save the output images.
            - dpi (int): Dots per inch for image extraction.
            - threshold (int): Threshold value for difference detection.
    """
    images1 = extract_images_from_pdf(settings['pdf1_path'], dpi=settings['dpi'])
    images2 = extract_images_from_pdf(settings['pdf2_path'], dpi=settings['dpi'])

    if len(images1) != len(images2):
        raise ValueError("PDFs have different number of pages")

    # Create an output diff directory if it doesn't exist
    diff_dir = create_diff_dir(settings['output_path'])

    # Compare the pages in parallel
    pages_with_changes = compare_pages_in_parallel(
        images1, images2, diff_dir, settings['threshold']
    )

    # Log the results and write to a text file
    log_and_write_diff_results(pages_with_changes, diff_dir, settings)


def main():
    """
    Main function.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "pdf1",
        help="Path to the first PDF file"
    )
    parser.add_argument(
        "pdf2",
        help="Path to the second PDF file"
    )
    parser.add_argument(
        "output",
        help="Directory to save the output images"
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=350,
        help="DPI for image extraction (default: 350)"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=75,
        help="Threshold value for difference detection (default: 75)"
    )
    args = parser.parse_args()

    settings = {
        'pdf1_path': args.pdf1,
        'pdf2_path': args.pdf2,
        'output_path': args.output,
        'dpi': args.dpi,
        'threshold': args.threshold
    }

    logging.basicConfig(level=logging.INFO)

    compare_pdfs(settings)


if __name__ == "__main__":
    main()
