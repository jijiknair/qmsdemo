from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
import os
from django.conf import settings

def generate_quotation_pdf(data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    top_margin = 150  # space for letterhead
    y_start = A4[1] - top_margin

    # ===== HEADER TABLE (Client Info + Date + Quotation No) =====
    # Header data for the table (4 columns, 3 rows)
    header_data = [
    ["DATE", data['date'], "QTN No", data['qtn_no']],
    ["TO", data['client_company'], "EMAIL", data['client_email']],
    ["ATTN", data['client_name'], "PHONE", data['client_phone']],
    ]

# Create table
    header_table = Table(header_data, colWidths=[50, 200, 60, 180])

# Add styling (optional)
    header_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # optional for first row
    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),      # table borders
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
    ('FONTSIZE', (0,0), (-1,-1), 11),
]))

# Draw table below letterhead
    y_start = 584  # adjust this value to move the table down if overlapping with logo
    header_table.wrapOn(c, A4[0], A4[1])
    header_table.drawOn(c, 50, y_start)

    # BODY TEXT
    body_y = y_start - (20 * len(header_data)) - 0
    c.setFont("Helvetica", 11)
    c.drawString(50, body_y, "Dear Sir,")
    body_y -= 10
    c.drawString(50, body_y, "We thank you for your enquiry and pleased to quote our best price for the following:")

    # ===== PRODUCT TABLE =====
    product_table_data = [['S.No', 'Product Details', 'Pack Size', 'Price (RO)']]
    for i, (name, size, price) in enumerate(zip(data['product_name'], data['pack_size'], data['unit_price']), start=1):
        product_table_data.append([str(i), name, size, price])

    product_table = Table(product_table_data, colWidths=[50, 200, 90, 80])
    product_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 11),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 11),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))

    product_y = body_y - 40
    product_table.wrapOn(c, A4[0], A4[1])
    product_table.drawOn(c, 50, product_y - (20 * len(product_table_data)))

    # ===== TERMS =====
    terms_y = product_y - (20 * len(product_table_data)) - 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, terms_y, "Terms:")
    terms_y -= 20

    c.setFont("Helvetica", 11)
    c.drawString(50, terms_y, f"1. Offer Validity: {data['validity']}")
    terms_y -= 20
    c.drawString(50, terms_y, f"2. Delivery: {data['delivery']}")
    terms_y -= 20
    c.drawString(50, terms_y, f"3. Payment: {data['payment_terms']}")
    terms_y -= 20
    c.drawString(50, terms_y, f"4. Warranty: {data['warranty']}")


    # ===== Additional Text Lines =====
    terms_y -= 40 
    c.drawString(50, terms_y, "Looking forward for your valuable orders.")
    c.setFont("Helvetica-Bold", 10)
    terms_y -= 20
    c.drawString(50, terms_y, "Hope this is in line with your requirement, for any further clarifications please feel free to call the undersigned.")

    # ===== SIGNATURE =====
    signature_y = terms_y - 40
    c.setFont("Helvetica-Oblique", 11)  # Use italic font
    c.drawString(50, signature_y, "Thanks & regards")
    c.setFont("Helvetica-Bold", 10)
    signature_y -= 20
    c.drawString(50, signature_y, data['salesperson'])
    signature_y -= 20
    c.drawString(50, signature_y, "Sales Executive")

    c.save()
    buffer.seek(0)
    content_pdf = PdfReader(buffer)

    # MERGE WITH LETTERHEAD
    letterhead_path = os.path.join(settings.BASE_DIR, "quotes", "static", "quotes", "GIC Letterhead new.pdf")
    if not os.path.exists(letterhead_path):
        raise FileNotFoundError(f"Letterhead PDF not found at {letterhead_path}")

    letterhead_pdf = PdfReader(letterhead_path)
    output = PdfWriter()
    page = letterhead_pdf.pages[0]
    page.merge_page(content_pdf.pages[0])
    output.add_page(page)

    final_buffer = BytesIO()
    output.write(final_buffer)
    final_buffer.seek(0)
    return final_buffer
