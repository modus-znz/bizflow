"""
bizflow.doc — Document Conversions & Processing Module

Handles:
- DOCX -> Markdown / Text
- XLSX -> CSV / JSON / Parquet
- PPTX -> Text extraction
- Image / Scanned PDF -> Searchable PDF / Batch OCR
"""

import sys
import json
from pathlib import Path

def convert_docx_to_md(input_docx: str, output_md: str):
    try:
        from docx import Document
        doc = Document(input_docx)
        full_text = []
        for p in doc.paragraphs:
            if p.text.strip():
                if p.style and "Heading" in p.style.name:
                    level = p.style.name.replace("Heading", "").strip()
                    prefix = "#" * int(level) if level.isdigit() else "#"
                    full_text.append(f"\n{prefix} {p.text}\n")
                else:
                    full_text.append(p.text)
        
        content = "\n\n".join(full_text)
        with open(output_md, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ Converted {input_docx} -> {output_md}")
    except Exception as e:
        print(f"Error converting DOCX: {e}")

def convert_xlsx_to_json(input_xlsx: str, output_json: str):
    try:
        import openpyxl
        wb = openpyxl.load_workbook(input_xlsx, data_only=True)
        sheets_data = {}
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                continue
            headers = [str(h) if h is not None else f"col_{i}" for i, h in enumerate(rows[0])]
            data = []
            for row in rows[1:]:
                if any(cell is not None for cell in row):
                    row_dict = {headers[i]: cell for i, cell in enumerate(row) if i < len(headers)}
                    data.append(row_dict)
            sheets_data[sheet_name] = data
        
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(sheets_data, f, indent=2, default=str)
        print(f"✓ Converted XLSX {input_xlsx} -> {output_json}")
    except Exception as e:
        print(f"Error converting XLSX: {e}")

def extract_pptx_text(input_pptx: str, output_txt: str):
    try:
        from pptx import Presentation
        prs = Presentation(input_pptx)
        text_runs = []
        for i, slide in enumerate(prs.slides):
            text_runs.append(f"--- Slide {i+1} ---")
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    text_runs.append(shape.text.strip())
        
        content = "\n".join(text_runs)
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ Extracted PPTX {input_pptx} -> {output_txt}")
    except Exception as e:
        print(f"Error extracting PPTX text: {e}")
