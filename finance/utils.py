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


# finance/utils.py
import requests

PAYSTACK_BASE_URL = "https://api.paystack.co"

DEFAULT_EMAIL = "techcenter652@gmail.com"
DEFAULT_PHONE = "07085734441"


def create_paystack_customer(student):
    """
    Creates a Paystack customer for a student (once).
    Always uses default email and phone.
    """

    if student.paystack_customer_code:
        return student.paystack_customer_code

    headers = {
        "Authorization": f"Bearer {student.school.paystack_secret_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "email": DEFAULT_EMAIL,
        "first_name": student.user.first_name or student.admission_no,
        "last_name": student.user.last_name or student.admission_no,
        "phone": DEFAULT_PHONE,
        "metadata": {
            "student_id": student.id,
            "school_id": student.school_id,
            "admission_no": student.admission_no,
        },
    }

    response = requests.post(
        f"{PAYSTACK_BASE_URL}/customer",
        json=payload,
        headers=headers,
        timeout=30,
    )

    data = response.json()

    if not response.ok or not data.get("status"):
        raise Exception(
            f"Paystack customer creation failed: {data.get('message')}"
        )

    student.paystack_customer_code = data["data"]["customer_code"]
    student.save(update_fields=["paystack_customer_code"])

    return student.paystack_customer_code

import requests
from django.utils import timezone
from students.models import VirtualAccount

PAYSTACK_BASE_URL = "https://api.paystack.co"
DEFAULT_EMAIL = "techcenter652@gmail.com"
DEFAULT_PHONE = "07085734441"

# Add/remove banks here
PREFERRED_BANKS = [
    "titan-paystack",
    "wema-bank",
    "providus-bank",
    "gtbank",
]


# -------------------------------------------------
# Ensure Paystack customer phone exists
# -------------------------------------------------
def ensure_customer_phone(student):
    if not student.paystack_customer_code:
        return

    headers = {
        "Authorization": f"Bearer {student.school.paystack_secret_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "phone": DEFAULT_PHONE,
        "email": student.user.email or DEFAULT_EMAIL,
    }

    requests.put(
        f"{PAYSTACK_BASE_URL}/customer/{student.paystack_customer_code}",
        json=payload,
        headers=headers,
        timeout=30,
    )


# -------------------------------------------------
# Fetch ALL Paystack VAs (pagination-safe)
# -------------------------------------------------
def fetch_all_paystack_virtual_accounts(student):
    headers = {
        "Authorization": f"Bearer {student.school.paystack_secret_key}",
        "Content-Type": "application/json",
    }

    accounts = []
    page = 1

    while True:
        r = requests.get(
            f"{PAYSTACK_BASE_URL}/dedicated_account",
            headers=headers,
            params={
                "customer": student.paystack_customer_code,
                "page": page,
                "perPage": 50,
            },
            timeout=30,
        )
        data = r.json()

        if not data.get("status"):
            break

        accounts.extend(data.get("data", []))

        meta = data.get("meta", {})
        if page >= meta.get("pageCount", 1):
            break

        page += 1

    return accounts


# -------------------------------------------------
# Create VA for a specific bank (if missing)
# -------------------------------------------------
def create_virtual_account_for_bank(student, bank_slug):
    headers = {
        "Authorization": f"Bearer {student.school.paystack_secret_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "customer": student.paystack_customer_code,
        "preferred_bank": bank_slug,
    }

    r = requests.post(
        f"{PAYSTACK_BASE_URL}/dedicated_account",
        json=payload,
        headers=headers,
        timeout=30,
    )
    return r.json()


# -------------------------------------------------
# MAIN ENTRY
# -------------------------------------------------
def ensure_virtual_accounts(student):
    """
    ✔ Ensures Paystack customer
    ✔ Fixes missing phone numbers
    ✔ Creates MULTI-BANK VAs
    ✔ Syncs ALL VAs locally
    ✔ Never crashes dashboard
    """

    headers = {
        "Authorization": f"Bearer {student.school.paystack_secret_key}",
        "Content-Type": "application/json",
    }

    try:
        # 1️⃣ ENSURE CUSTOMER
        if not student.paystack_customer_code:
            payload = {
                "email": student.user.email or DEFAULT_EMAIL,
                "phone": DEFAULT_PHONE,
                "first_name": student.user.first_name or student.admission_no,
                "last_name": student.user.last_name or student.admission_no,
            }

            r = requests.post(
                f"{PAYSTACK_BASE_URL}/customer",
                json=payload,
                headers=headers,
                timeout=30,
            )
            data = r.json()

            if not data.get("status"):
                print("[PAYSTACK] Customer create failed:", data.get("message"))
                return

            student.paystack_customer_code = data["data"]["customer_code"]
            student.save(update_fields=["paystack_customer_code"])

        # 2️⃣ FIX OLD CUSTOMERS
        ensure_customer_phone(student)

        # 3️⃣ FETCH EXISTING VAs
        accounts = fetch_all_paystack_virtual_accounts(student)
        existing_bank_slugs = {
            (a.get("bank") or {}).get("slug") for a in accounts
        }

        # 4️⃣ CREATE MISSING BANK ACCOUNTS
        for bank_slug in PREFERRED_BANKS:
            if bank_slug not in existing_bank_slugs:
                r = create_virtual_account_for_bank(student, bank_slug)
                if r.get("status"):
                    accounts.append(r["data"])

        # 5️⃣ DETERMINE PRIMARY
        primary_account_number = next(
            (a["account_number"] for a in accounts if a.get("is_primary")),
            None,
        )

        # 6️⃣ SYNC LOCALLY
        for va in accounts:
            bank = va.get("bank") or {}

            VirtualAccount.objects.update_or_create(
                account_number=va["account_number"],
                defaults={
                    "student": student,
                    "account_name": va.get("account_name"),
                    "bank_name": bank.get("name"),
                    "bank_slug": bank.get("slug"),
                    "is_primary": va["account_number"] == primary_account_number,
                    "verified_at": timezone.now(),
                },
            )

        # 7️⃣ ENFORCE SINGLE PRIMARY LOCALLY
        if primary_account_number:
            VirtualAccount.objects.filter(
                student=student
            ).exclude(
                account_number=primary_account_number
            ).update(is_primary=False)

    except Exception as e:
        print(f"[VA ERROR] Student {student.id}: {e}")



from decimal import Decimal, ROUND_HALF_UP


PAYSTACK_PERCENT = Decimal("0.015")  # 1.5%
PAYSTACK_FLAT = Decimal("100")
PAYSTACK_CAP = Decimal("2000")


def calculate_paystack_fee(amount: Decimal):
    """
    Returns:
        fee (Decimal)
        total_to_charge (Decimal)
    """

    amount = Decimal(amount)

    percentage_fee = amount * PAYSTACK_PERCENT
    fee = percentage_fee + PAYSTACK_FLAT

    # Apply cap
    if fee > PAYSTACK_CAP:
        fee = PAYSTACK_CAP

    total = amount + fee

    return (
        fee.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
    )




from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_school_payment_notification(payment):
    """
    Sends payment copy to school email.
    """

    school_email = (
        payment.school.notification_email
        or "techcenter652@gmail.com"
    )

    if not school_email:
        return

    try:
        send_mail(
            subject=f"Payment Received - {payment.student}",
            message=f"""
Payment Notification

School: {payment.school.name}
Student: {payment.student}
Class: {payment.school_class}
Amount: ₦{payment.amount:,.2f}
Term: {payment.term}
Session: {payment.session}
Reference: {payment.reference}
Method: {payment.payment_method}

Generated by TECHCENTER School Portal.
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[school_email],
            fail_silently=False,
        )

        logger.info(
            f"School payment email sent to {school_email}"
        )

    except Exception as e:
        logger.error(
            f"School payment email failed: {e}"
        )    