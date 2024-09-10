# Digital Signature Script

This script allows you to add a digital signature to a PDF file. It also provides an option to add a watermark to the PDF.

## Prerequisites

Before running the script, make sure you have the following installed:

- Python 3.x
- Required Python libraries (listed below)

## Installation

1. **Clone or download the repository**:
   ```bash
   git clone https://github.com/DIOR27/pysign_ec.git
   cd pysign_ec
   ```
2. **Install the required Python libraries**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the following command to add a digital signature to the PDF file (you must to provide the path to the PDF file, the path to the .p12 file, the password for the .p12 file, and the text to search in the PDF for placing the signature):

```bash
python3 main.py path/to/pdf path/to/p12_file "password_for_p12_file" "text_to_search"
```

### Output

The script will generate a new PDF file with the digital signature added showing the followin output:
```bash
Signed PDF saved at 'Path/to/file.pdf'.
```

## Screenshots

![result](/result.png)

![watermark](/watermark.png)