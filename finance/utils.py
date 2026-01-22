from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from django.http import HttpResponse
from .models import SchoolTermSetting


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


def get_next_term_begins(school, session, term=None):
    """
    - If term is provided → fetch exact term setting
    - If cumulative → fetch active term for the session
    """

    qs = SchoolTermSetting.objects.filter(
        school=school,
        session=session,
    )

    if term:
        qs = qs.filter(term=term)
    else:
        qs = qs.filter(is_active=True)

    ts = qs.first()
    return ts.next_term_begins if ts else None







import requests
import uuid
from django.conf import settings


class Paystack:
    def __init__(self, secret_key):
        self.secret_key = secret_key
        self.base_url = "https://api.paystack.co/"

    def initialize_transaction(self, amount, email, callback_url):
        url = self.base_url + "transaction/initialize"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        data = {
            "email": email,
            "amount": int(amount * 100),  # amount in kobo
            "callback_url": callback_url
        }
        resp = requests.post(url, json=data, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def verify_transaction(self, reference):
        url = self.base_url + f"transaction/verify/{reference}"
        headers = {"Authorization": f"Bearer {self.secret_key}"}
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()



from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum

from .models import Payment, Invoice


def update_invoice_amount_paid(invoice):
    total = (
        Payment.objects
        .filter(invoice=invoice)
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    if invoice.amount_paid != total:
        invoice.amount_paid = total
        invoice.save(update_fields=["amount_paid"])


@receiver(post_save, sender=Payment)
def payment_saved(sender, instance, **kwargs):
    update_invoice_amount_paid(instance.invoice)


@receiver(post_delete, sender=Payment)
def payment_deleted(sender, instance, **kwargs):
    update_invoice_amount_paid(instance.invoice)
