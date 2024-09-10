import argparse
import os
from pysign import add_watermark, sign_pdf


def main():
    parser = argparse.ArgumentParser(description="Add a digital signature to a PDF.")
    parser.add_argument("pdf_path", help="Path to the PDF file to be signed.")
    parser.add_argument(
        "p12_path", help="Path to the .p12 file for the digital signature."
    )
    parser.add_argument("password", help="Password for the .p12 file.")
    parser.add_argument(
        "sign_text", help="Text to search in the PDF for placing the signature."
    )
    # parser.add_argument(
    #     "--right", type=int, default=0, help="Horizontal offset for the signature."
    # )

    args = parser.parse_args()

    pdf_path = args.pdf_path
    p12_path = args.p12_path
    password = args.password
    sign_text = args.sign_text
    # right = args.right

    if not os.path.isfile(pdf_path):
        print(f"The PDF file '{pdf_path}' does not exist.")
        return

    if not os.path.isfile(p12_path):
        print(f"The .p12 file '{p12_path}' does not exist.")
        return

    # Add watermark to PDF (This will override any existing signature)
    watermark_message = "TOP SECRET"
    add_watermark(pdf_path, watermark_message)

    # Firmar el PDF
    sign_pdf(pdf_path, p12_path, password, sign_text)
    print(f"Signed PDF saved at '{pdf_path}'.")


if __name__ == "__main__":
    main()
