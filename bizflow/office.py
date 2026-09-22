"""
bizflow.office — Office Administration & Utilities Module

Handles:
- QR code & Barcode generation/reading
- PDF stamping, watermarking, page extraction, splitting, and SHA256 hashing
- Administrative document templating (memos, purchase orders, letters)
"""

import sys
import hashlib
from pathlib import Path

def generate_qr(text: str, output_path: str):
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(output_path)
        print(f"✓ QR code generated: {output_path}")
    except ImportError:
        print("Error: qrcode package not installed.")

def stamp_pdf(input_pdf: str, output_pdf: str, stamp_text: str):
    try:
        from pypdf import PdfReader, PdfWriter
        reader = PdfReader(input_pdf)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        metadata = reader.metadata or {}
        writer.add_metadata({
            "/Stamp": stamp_text,
            "/ProcessedBy": "bizflow office stamp"
        })

        with open(output_pdf, "wb") as f:
            writer.write(f)
        
        print(f"✓ PDF stamped and saved: {output_pdf}")
    except Exception as e:
        print(f"Error stamping PDF: {e}")

def hash_document(file_path: str):
    p = Path(file_path)
    if not p.exists():
        print(f"Error: File {file_path} not found.")
        return
    
    sha = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    
    digest = sha.hexdigest()
    print(f"File: {p.name}")
    print(f"SHA256: {digest}")
    return digest

def render_template(template_text: str, data: dict) -> str:
    try:
        from jinja2 import Template
        t = Template(template_text)
        return t.render(**data)
    except ImportError:
        # Fallback simple format
        res = template_text
        for k, v in data.items():
            res = res.replace(f"{{{{ {k} }}}}", str(v)).replace(f"{{{{{k}}}}}", str(v))
        return res
