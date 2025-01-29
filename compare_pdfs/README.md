# HOW TO ... compare two PDF files and highlight differences?

## WHY?

Comparing PDF files manually to find differences can be time-consuming and error-prone. Automating this process ensures accuracy and saves time. The `compare_pdfs.py` script extracts pages from two PDF files, converts them to grayscale, and highlights any differences in separate diff images.

## HOW?

> [!NOTE]
> This script uses the latest Python version (3.13 for now). Make sure to have Python installed on your system, or get it from here: [https://www.python.org/downloads/](https://www.python.org/downloads/)

### Preparation

* Make sure that you have two PDF files that you want to compare. They should have identical page numbers.
* Make sure that you have created a fork from this GitHub repository `awg-utils` and you have a local copy of this fork on your machine.
* In your file explorer, navigate to your local folder `awg-utils`, right-click on it, and open it with **VSCode** editor.
* Open a new terminal in **VSCode** editor (preferably **Git Bash**, following paths and directions are using Git Bash syntax).
* In the terminal, change directory to the subfolder `compare_pdfs` by typing: `cd compare_pdfs` (it should be sufficient to type `cd comp` + `TAB` key, the console autocompletes the name on its own). This subfolder is where the comparison script lives.

Now you're good to run the comparison script.

### Comparison

* In the terminal, type `pip install --require-hashes -r requirements.txt` to install the latest library versions with verified hashes.
* In the terminal, type `python compare_pdfs.py <PDF1_PATH> <PDF2_PATH> <OUTPUT_DIRECTORY> [--dpi <DPI>] [--threshold <THRESHOLD>]`.
* Replace `<PDF1_PATH>` with the path to your first PDF file.
* Replace `<PDF2_PATH>` with the path to your second PDF file.
* Replace `<OUTPUT_DIRECTORY>` with the path to the directory where you want to save the output images.
* Optionally, replace `<DPI>` with the desired DPI for image extraction (default is 350).
* Optionally, replace `<THRESHOLD>` with the desired threshold value for difference detection (default is 75).

> [!TIP]
> If you have the PDF files in the same directory as the python script, you can use relative paths.

#### Examples (using **Git Bash** syntax):

* External directory: `python compare_pdfs.py /c/Users/<USERNAME>/Documents/PDFs/file1.pdf /c/Users/<USERNAME>/Documents/PDFs/file2.pdf /c/Users/<USERNAME>/Documents/PDFs/output`
* Same directory: `python compare_pdfs.py ./file1.pdf ./file2.pdf ./output`
* With optional parameters: `python compare_pdfs.py ./file1.pdf ./file2.pdf ./output --dpi 400 --threshold 50`

### Output

The script will log the pages where changes were detected and write the output to a text file named `diff.txt` in the `diff_images` folder within the specified output directory. The output images, highlighting the diffs in red, will also be saved in the `diff_images` folder.