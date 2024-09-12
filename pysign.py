# -*- coding: utf-8 -*-
import os
import re
import tempfile
from datetime import datetime
from io import BytesIO
from urllib.request import urlopen

import pytz
import qrcode
from PIL import Image, ImageDraw, ImageFont
from cryptography.hazmat import backends
from cryptography.hazmat.primitives.serialization import pkcs12
from endesive.pdf import cms
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter
from spire.pdf import PdfDocument, PdfTextFinder, PdfTextFindOptions, TextFindParameter

def add_watermark(pdf_path, message):
    with open(pdf_path, "rb") as file:
        pdf_content = file.read()

    original_pdf = BytesIO(pdf_content)
    pdf_reader = PdfReader(original_pdf)
    output_stream = BytesIO()

    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica-Bold", 36)
    can.setFillColorRGB(1, 0, 0)  # Color rojo

    width, height = letter
    can.saveState()
    can.translate(width / 2, height / 2)
    can.rotate(45)
    can.drawCentredString(0, 0, message)
    can.restoreState()
    can.save()

    packet.seek(0)
    watermark_pdf = PdfReader(packet)
    pdf_writer = PdfWriter()

    for page_num in range(len(pdf_reader.pages)):
        original_page = pdf_reader.pages[page_num]
        watermark_page = watermark_pdf.pages[0]
        original_page.merge_page(watermark_page)
        pdf_writer.add_page(original_page)

    pdf_writer.write(output_stream)
    output_stream.seek(0)

    modified_pdf_content = output_stream.read()
    with open(pdf_path, "wb") as file:
        file.write(modified_pdf_content)

def sign_pdf(pdf_path, p12_path, password, sign_text, x_scroll=50, y_scroll=-60):
    with open(pdf_path, "rb") as file:
        pdf_content = file.read()
    with open(p12_path, "rb") as file:
        digital_signature_content = file.read()

    p12file = BytesIO(digital_signature_content)
    pdf_file = BytesIO(pdf_content)

    with tempfile.NamedTemporaryFile(delete=False) as temp_pdf_file:
        temp_pdf_file.write(pdf_content)
        temp_pdf_path = temp_pdf_file.name

    doc = PdfDocument()
    doc.LoadFromFile(temp_pdf_path)
    num_pages = doc.Pages.Count
    last_page_num = num_pages - 1
    last_page = doc.Pages[last_page_num]
    textFinder = PdfTextFinder(last_page)
    page_size = last_page.Size

    findOptions = PdfTextFindOptions()
    findOptions.Parameter = TextFindParameter.IgnoreCase
    findOptions.Parameter = TextFindParameter.WholeWord
    textFinder.Options = findOptions

    findResults = textFinder.Find(sign_text)
    if not findResults:
        print(f"The term '{sign_text}' was not found in the document.")
        return False

    result = findResults[0]
    x = int(result.Positions[0].X)
    x += x_scroll
    y = int(result.Positions[0].Y)

    y = page_size.Height - y
    y += y_scroll
    
    doc.Dispose()
    PDF_SIGN_LOCATION = (x, y)

    datau, datas = sign_pdf_data(password, p12file, pdf_file, PDF_SIGN_LOCATION, last_page_num)
    signed_pdf = datau + datas

    base, ext = os.path.splitext(pdf_path)
    signed_pdf_path = f"{base}_signed{ext}"

    # Guardar el PDF firmado en un nuevo archivo
    with open(signed_pdf_path, "wb") as file:
        file.write(signed_pdf)

    print(f"Signed PDF saved as '{signed_pdf_path}'.")

    return True

def sign_pdf_data(password, p12file, pdf, sign_location, last_page):
    date = datetime.now(pytz.timezone("America/Guayaquil")).isoformat()

    p12 = pkcs12.load_key_and_certificates(
        p12file.read(), password.encode("ascii"), backends.default_backend()
    )

    subject_info = p12[1].subject.rfc4514_string()
    matches = re.search(r"CN=(.*)$", subject_info)

    data = []
    author_name = None
    if matches:
        author_name = matches.group(1)
        author_name = author_name.split(",")
        author_name = author_name[0]

        data.append(f"FIRMADO POR: {author_name}")
        data.append(f"FECHA: {date}")

    date = datetime.now(pytz.timezone("America/Guayaquil")).strftime("%Y%m%d%H%M%S")
    qr_image = generate_qr_code(f"{data[0]}\n{data[1]}")
    text_to_add = f"Firmado electrónicamente por:\n{author_name}"
    qr_with_text_image = add_text_to_qr(qr_image, text_to_add)

    qr_bytes_io = BytesIO()
    qr_with_text_image.save(qr_bytes_io, format="PNG")
    qr_image_bytes = qr_bytes_io.getvalue()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_qr_file:
        temp_qr_file.write(qr_image_bytes)
        temp_qr_path = temp_qr_file.name

    dct = {
        "aligned": 0,
        "sigflags": 3,
        "sigflagsft": 132,
        "sigpage": last_page,
        "sigbutton": True,
        "sigfield": "Signature1",
        "auto_sigfield": True,
        "sigandcertify": True,
        "signaturebox": (sign_location[0], sign_location[1], 150 + sign_location[0], 50 + sign_location[1]),
        "signature_img": temp_qr_path,
        "contact": author_name,
        "location": "",
        "signingdate": date,
        "reason": "",
        "password": password,
    }

    datau = pdf.read()
    temp_pdf_stream = BytesIO(datau)

    datas = cms.sign(
        temp_pdf_stream.getvalue(), dct, p12[0], p12[1], p12[2], "sha256"
    )
    return temp_pdf_stream.getvalue(), datas

def generate_qr_code(data, qr_size=75):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=qr_size / 25.4,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    return img

def add_text_to_qr(qr_image, text):
    qr_image_pil = qr_image.convert("RGB")
    width, height = qr_image_pil.size

    regular_font_url = "https://github.com/quoteunquoteapps/CourierPrime/blob/master/fonts/ttf/CourierPrime-Regular.ttf?raw=true"
    bold_font_url = "https://github.com/quoteunquoteapps/CourierPrime/blob/master/fonts/ttf/CourierPrime-Bold.ttf?raw=true"
    regular_font = ImageFont.truetype(urlopen(regular_font_url), size=11)
    bold_font = ImageFont.truetype(urlopen(bold_font_url), size=18)

    draw = ImageDraw.Draw(qr_image_pil)
    lines = text.split("\n")

    text_width = max(
        draw.textbbox((0, 0), line, font=regular_font)[2] for line in lines
    )
    text_height = sum(
        draw.textbbox((0, 0), line, font=regular_font)[3] for line in lines
    )

    new_image = Image.new("RGB", (width + text_width + 10, height), "white")
    new_image.paste(qr_image_pil, (0, 0))

    draw = ImageDraw.Draw(new_image)
    y_text = (height - text_height) // 2 - 10

    author_lines = text.split("\n")
    signed_text = author_lines[0]
    author_name_lines = format_author_name(author_lines[1])

    draw.text((width + 5, y_text), signed_text, font=regular_font, fill="black")
    y_text += draw.textbbox((0, 0), signed_text, font=regular_font)[3]

    for line in author_name_lines:
        draw.text((width + 5, y_text), line, font=bold_font, fill="black")
        y_text += draw.textbbox((0, 0), line, font=bold_font)[3]

    return new_image

def format_author_name(author_name):
    words = author_name.split()
    match len(words):
        case 4:
            return [" ".join(words[:2]), " ".join(words[2:])]
        case 3:
            return [" ".join(words[:2]), words[2]]
        case 2:
            return [" ".join(words)]
        case _:
            return [author_name]
