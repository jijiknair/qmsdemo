from io import BytesIO
import os
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
)
from reportlab.lib.units import mm
from PyPDF2 import PdfReader, PdfWriter, PageObject
from num2words import num2words


def generate_quotation_pdf(data):
    buffer = BytesIO()

    # ------------------------------------------------------
    # PDF DOCUMENT WITH SAFE MARGINS (IMPORTANT!)
    # ------------------------------------------------------
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=67 * mm,
        bottomMargin=50 * mm,   # RESERVE SPACE FOR FOOTER
        leftMargin=20 * mm,
        rightMargin=20 * mm
    )

    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    normal_style.fontName = "Helvetica"
    normal_style.fontSize = 10
    normal_style.leading = 12

    elements = []

    elements.append(Spacer(1, 50))

    # ------------------------------------------------------
    # HEADER TABLE
    # ------------------------------------------------------
    header_data = [
        ["DATE", data["date"], "QTN No", data["qtn_no"]],
        ["TO", data["client_company"], "EMAIL", data["client_email"]],
        ["ATTN", data["client_name"], "PHONE", data["client_phone"]],
    ]

    header_table = Table(header_data, colWidths=[50, 200, 60, 150])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 12))

    # ------------------------------------------------------
    # INTRO TEXT
    # ------------------------------------------------------
    elements.append(Paragraph("Dear Sir,", normal_style))
    elements.append(Spacer(1, 6))

    intro_text = data.get("intro_text", "")
    if intro_text:
        elements.append(Paragraph(intro_text, normal_style))
    else:
        elements.append(Paragraph(
            "We thank you for your enquiry and pleased to quote our best price for the following:",
            normal_style
        ))

    elements.append(Spacer(1, 12))

    # ------------------------------------------------------
    # PRODUCT TABLE
    # ------------------------------------------------------
    product_table_data = [
        ["S.No", "Description", "Pack Size", "Qty", "Unit Price", "Total"]
    ]

    subtotal = 0

    for i, product in enumerate(data.get("products", []), start=1):
        qty = int(product.get("qty", 0))
        price = float(product.get("unit_price", 0))
        total = qty * price
        subtotal += total

        product_table_data.append([
            str(i),
            Paragraph(f"<b>{product.get('name','')}</b><br/>{product.get('desc','')}", normal_style),
            product.get("pack_size", ""),
            str(qty),
            f"{price:.3f}",
            f"{total:.3f}",
        ])

    vat_amount = round(subtotal * 0.05, 3)
    grand_total = round(subtotal + vat_amount, 3)

    product_table_data.append(["", "", "", "", "", ""])
    product_table_data.append(["", "", "", "", "Subtotal", f"{subtotal:.3f}"])
    product_table_data.append(["", "", "", "", "VAT 5%", f"{vat_amount:.3f}"])
    product_table_data.append(["", "", "", "", "Grand Total", f"{grand_total:.3f}"])

    product_table = Table(product_table_data, colWidths=[30, 150, 60, 40, 70, 70])
    product_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (3, 1), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    elements.append(product_table)
    elements.append(Spacer(1, 12))

    # ------------------------------------------------------
    # TERMS SECTION
    # ------------------------------------------------------
    elements.append(Paragraph("<b>Terms:</b>", normal_style))
    elements.append(Spacer(1, 6))

    terms_list = [
        f"1. Offer Validity: {data['validity']}",
        f"2. Delivery: {data['delivery']}",
        f"3. Payment: {data['payment_terms']}",
    ]

    for term in terms_list:
        elements.append(Paragraph(term, normal_style))
        elements.append(Spacer(1, 4))

    # ------------------------------------------------------
    # SIGNATURE BLOCK (KEPT TOGETHER TO AVOID SPLIT)
    # ------------------------------------------------------
    signature_block = []

    signature_block.append(Spacer(1, 12))

    closing_text = data.get("closing_text", "")
    if closing_text:
        signature_block.append(Paragraph(closing_text, normal_style))
    else:
        signature_block.append(Paragraph("Looking forward for your valuable orders.", normal_style))

    signature_block.append(Spacer(1, 12))
    signature_block.append(Paragraph("Thanks & regards,", normal_style))
    signature_block.append(Paragraph(f"<b>{data['salesperson']}</b>", normal_style))
    signature_block.append(Paragraph("Sales Executive", normal_style))

    elements.append(KeepTogether(signature_block))

    # ------------------------------------------------------
    # BUILD PDF CONTENT (WITHOUT LETTERHEAD)
    # ------------------------------------------------------
    doc.build(elements)

    # ------------------------------------------------------
    # MERGE WITH LETTERHEAD PDF
    # ------------------------------------------------------
    buffer.seek(0)
    content_pdf = PdfReader(buffer)

    letterhead_path = os.path.join(settings.BASE_DIR, "quotes", "static", "quotes", "GIC Letterhead new.pdf")
    letterhead_pdf = PdfReader(letterhead_path)

    output = PdfWriter()

    for page_number in range(len(content_pdf.pages)):
        merged_page = PageObject.create_blank_page(
            width=letterhead_pdf.pages[0].mediabox.width,
            height=letterhead_pdf.pages[0].mediabox.height
        )

        merged_page.merge_page(letterhead_pdf.pages[0])
        merged_page.merge_page(content_pdf.pages[page_number])

        output.add_page(merged_page)

    final_buffer = BytesIO()
    output.write(final_buffer)
    final_buffer.seek(0)

    return final_buffer
