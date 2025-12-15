from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from django.http import HttpResponse


def generate_invoice_pdf(invoice):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="invoice_{invoice.id}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"<b>{invoice.school.name}</b>", styles["Title"]))
    elements.append(Paragraph("Invoice", styles["Heading2"]))
    elements.append(Paragraph(f"Student: {invoice.student}", styles["Normal"]))
    elements.append(Paragraph(f"Class: {invoice.school_class}", styles["Normal"]))
    elements.append(Paragraph(f"Session: {invoice.session} | Term: {invoice.term}", styles["Normal"]))

    table = Table([
        ["Title", "Amount"],
        [invoice.title, invoice.total_amount],
        ["Amount Paid", invoice.amount_paid],
        ["Balance", invoice.balance],
    ])

    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
    ]))

    elements.append(table)
    doc.build(elements)
    return response


def generate_receipt_pdf(receipt):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="receipt_{receipt.id}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"<b>{receipt.school.name}</b>", styles["Title"]))
    elements.append(Paragraph("Payment Receipt", styles["Heading2"]))

    elements.append(Paragraph(f"Student: {receipt.student}", styles["Normal"]))
    elements.append(Paragraph(f"Class: {receipt.school_class}", styles["Normal"]))
    elements.append(Paragraph(f"Amount Paid: ₦{receipt.amount}", styles["Normal"]))
    elements.append(Paragraph(f"Session: {receipt.session} | Term: {receipt.term}", styles["Normal"]))

    doc.build(elements)
    return response
