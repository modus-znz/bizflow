"""
bizflow.account — Accounting & Financial Operations Module

Handles:
- OFX / QIF / CSV bank statement parsing
- Double-entry ledger audit & balance verification
- Invoice & Receipt PDF generation
- Tax itemization & expense summaries
"""

import os
import sys
import json
import csv
from pathlib import Path

def parse_statement(file_path: str, output_csv: str = None) -> list:
    p = Path(file_path)
    transactions = []
    
    if p.suffix.lower() in [".ofx", ".qfx"]:
        try:
            from ofxparse import OfxParser
            with open(p, "rb") as f:
                ofx = OfxParser.parse(f)
            account = ofx.account
            statement = account.statement
            for tx in statement.transactions:
                transactions.append({
                    "date": str(tx.date),
                    "amount": float(tx.amount),
                    "payee": tx.payee,
                    "memo": tx.memo,
                    "type": tx.type,
                    "id": tx.id
                })
            print(f"✓ Parsed {len(transactions)} OFX transactions from {p.name}")
        except Exception as e:
            print(f"Error parsing OFX statement: {e}")
    else:
        # Fallback CSV parsing
        try:
            with open(p, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    transactions.append(row)
            print(f"✓ Parsed {len(transactions)} CSV transactions from {p.name}")
        except Exception as e:
            print(f"Error reading CSV statement: {e}")
            
    if output_csv and transactions:
        keys = transactions[0].keys()
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(transactions)
        print(f"✓ Saved transactions to {output_csv}")
        
    return transactions

def verify_ledger(transactions: list):
    total_debits = 0.0
    total_credits = 0.0
    
    for tx in transactions:
        amt = float(tx.get("amount", 0.0))
        if amt > 0:
            total_credits += amt
        else:
            total_debits += abs(amt)
            
    net = total_credits - total_debits
    print("\n--- Double-Entry Ledger Audit Summary ---")
    print(f"Total Deposits / Credits:  {total_credits:12.2f}")
    print(f"Total Debits / Expenses:   {total_debits:12.2f}")
    print(f"Net Statement Balance:     {net:12.2f}")

def generate_invoice_pdf(data: dict, output_pdf: str):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors

        doc = SimpleDocTemplate(output_pdf, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        title = f"INVOICE #{data.get('invoice_number', '1001')}"
        elements.append(Paragraph(title, styles['Title']))
        elements.append(Spacer(1, 12))

        vendor = data.get('vendor', 'Company Name')
        client = data.get('client', 'Client Name')
        elements.append(Paragraph(f"<b>From:</b> {vendor}", styles['Normal']))
        elements.append(Paragraph(f"<b>To:</b> {client}", styles['Normal']))
        elements.append(Spacer(1, 18))

        # Items Table
        table_data = [["Item Description", "Qty", "Price", "Total"]]
        items = data.get('items', [
            {"desc": "Consulting Services", "qty": 1, "price": 500.0}
        ])
        subtotal = 0.0
        for item in items:
            t = float(item['qty']) * float(item['price'])
            subtotal += t
            table_data.append([item['desc'], str(item['qty']), f"${item['price']:.2f}", f"${t:.2f}"])
        
        tax = subtotal * 0.16
        total = subtotal + tax
        table_data.append(["", "", "Subtotal:", f"${subtotal:.2f}"])
        table_data.append(["", "", "VAT (16%):", f"${tax:.2f}"])
        table_data.append(["", "", "Total Due:", f"${total:.2f}"])

        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        elements.append(t)
        doc.build(elements)
        print(f"✓ Generated Invoice PDF: {output_pdf}")
    except Exception as e:
        print(f"Error generating Invoice PDF: {e}")
