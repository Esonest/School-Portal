from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from django.utils.crypto import get_random_string
from results.utils import portal_required
from django.db import models
from django.db.models import Sum
from decimal import Decimal
from results.utils import SESSION_LIST
from results.models import Score
from .models import SchoolTransaction
from .utils import generate_invoice_pdf, generate_receipt_pdf
from .models import Invoice, Receipt
from .forms import FeeTemplate, FeeTemplateForm
from collections import defaultdict
from django.db.models import Q
from .utils import calculate_paystack_fee, send_school_payment_notification
from tis_website.models import AdmissionApplication


from django.db.models import (
    Sum,
    Count,
    DecimalField,
    Value,
    F,
)
from django.db.models.functions import Coalesce







# Helpers
def staff_required(user):
    return user.is_staff or hasattr(user,'teacher')

# Finance dashboard (admin)

from django.contrib.auth.decorators import login_required
from accounts.models import School  # if needed for school-specific filtering
from datetime import timedelta

TERM_CHOICES = [('1', 'Term 1'), ('2', 'Term 2'), ('3', 'Term 3')]



from finance.models import Invoice, Payment, Expense, PaystackTransaction
from results.models import Score
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import Coalesce
from django.contrib.auth.decorators import login_required

from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone




from django.db.models import Sum, Q, F, Value, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal


PAYMENT_METHOD_MAP = {
    "manual": ["manual", "cash", "pos", "transfer"],
    "online": ["online"],
    "bank": ["bank", "bank_transfer"],
}


def get_filtered_payments(school, start_date, session=None, term=None, class_id=None):
    qs = Payment.objects.filter(
        school=school,
        status="approved",
        payment_date__gte=start_date,
        invoice__isnull=False,   # IMPORTANT: keep dataset clean
    )

    if session:
        qs = qs.filter(invoice__session=session)

    if term:
        qs = qs.filter(invoice__term=term)

    if class_id:
        qs = qs.filter(invoice__school_class_id=class_id)

    return qs


def activate_student_after_admission_payment(payment):

    """
    Create and activate student account after admission fee payment.
    """

    from django.utils.crypto import get_random_string
    from accounts.models import User
    from students.models import Student


    # -----------------------------
    # Validate payment
    # -----------------------------

    invoice = payment.invoice

    if not invoice:
        return None


    # Only admission fee payments
    if not invoice.is_admission_fee:
        return None


    application = invoice.admission_application

    if not application:
        return None



    # -----------------------------
    # Prevent duplicate creation
    # -----------------------------

    existing_student = Student.objects.filter(
        admission_no=application.application_number
    ).first()


    if existing_student:

        # Ensure account is active
        existing_student.user.is_active = True
        existing_student.user.save(
            update_fields=[
                "is_active"
            ]
        )

        existing_student.is_active = True
        existing_student.save(
            update_fields=[
                "is_active"
            ]
        )

        return existing_student



    # -----------------------------
    # Ensure class exists
    # -----------------------------

    if not application.class_applying_for:

        raise Exception(
            "Cannot create student. Admission application has no class assigned."
        )



    # -----------------------------
    # Generate login details
    # -----------------------------

    username = application.application_number.lower()

    password = get_random_string(8)



    # -----------------------------
    # Create User Account
    # -----------------------------

    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=application.student_name,
        email=(
            application.student_email
            or application.parent_email
        ),
        role="student",
        school=application.school,
    )


    user.is_active = True

    user.save(
        update_fields=[
            "is_active"
        ]
    )



    # -----------------------------
    # Create Student Profile
    # -----------------------------

    student = Student.objects.create(

        user=user,

        admission_no=application.application_number,

        school=application.school,

        school_class=application.class_applying_for,

        dob=application.date_of_birth,

        gender=(
            "M"
            if application.gender == "Male"
            else "F"
        ),

        photo=application.passport,
        parent_name=application.parent_name,

        parent_email=application.parent_email,

        parent_phone=application.parent_phone,

        student_email=application.student_email,

        session=(
            application.admission_session
            or ""
        ),

        term=(
            application.admission_term
            or "1"
        ),

        is_active=True,
    )



    # -----------------------------
    # Update Admission Application
    # -----------------------------

    application.student_created = True

    application.student_username = username

    application.student_password = password

    application.payment_completed = True

    application.status = "completed"


    application.save(
        update_fields=[
            "student_created",
            "student_username",
            "student_password",
            "payment_completed",
            "status",
        ]
    )



    print(
        "NEW STUDENT CREATED:",
        student.admission_no,
        "CLASS:",
        student.school_class
    )


    return student

@login_required
def dashboard(request):
    school = request.user.school
    start_date = timezone.now() - timedelta(days=365)

    # -----------------------------
    # Filters
    # -----------------------------
    current_session = request.GET.get("session")
    current_term = request.GET.get("term")
    classes = SchoolClass.objects.filter(school=school).order_by("name")

    # -----------------------------
    # Invoices
    # -----------------------------
    invoices = Invoice.objects.filter(
        school=school,
        created_at__gte=start_date
    )
    if current_session:
        invoices = invoices.filter(session=current_session)
    if current_term:
        invoices = invoices.filter(term=current_term)


# Search filter
   # -----------------------------
# Invoice Analytics By Template
# -----------------------------

# Search filter
    search = request.GET.get("search")

    if search and search != "None":
        invoices = invoices.filter(
            Q(student__user__first_name__icontains=search) |
            Q(student__user__last_name__icontains=search) |
            Q(student__admission_no__icontains=search)
        )

# Class filter
    selected_class = request.GET.get("class")

    if selected_class:
        invoices = invoices.filter(
            school_class__id=selected_class
        )

# -----------------------------
# Totals AFTER filters
# -----------------------------
    invoice_totals = invoices.aggregate(
        total_expected=Coalesce(
            Sum("total_amount"),
            Decimal("0")
        ),
    )

    total_expected = invoice_totals["total_expected"]

# -----------------------------
# Invoice Breakdown
# -----------------------------
    invoice_breakdown = (
        invoices
        .values(
            "title",
            "school_class__name"
        )
        .annotate(
        # Total students invoiced
            total_students=Count(
                "student",
                distinct=True
            ),

        # Students owing
            balance_students=Count(
                "student",
                filter=Q(amount_paid__lt=F("total_amount")),
                distinct=True
            ),

        # Total invoice generated
            total_invoice_amount=Coalesce(
                Sum("total_amount"),
                Value(0),
                output_field=DecimalField(
                    max_digits=20,
                    decimal_places=2
                )
            ),

        # Total income received
            total_paid_amount=Coalesce(
                Sum("amount_paid"),
                Value(0),
                output_field=DecimalField(
                    max_digits=20,
                    decimal_places=2
                )
            ),
        )
        .annotate(
            balance=F("total_invoice_amount") - F("total_paid_amount")
        )
        .order_by(
            "school_class__name",
            "-total_invoice_amount"
        )
    )
    # -----------------------------
# PAYMENTS (CLEAN BASE)
# -----------------------------
    payments_base = get_filtered_payments(
        school=school,
        start_date=start_date,
        session=current_session,
        term=current_term,
        class_id=selected_class
    )

# -----------------------------
# PAYMENT TYPE FILTERING (SAFE + CONSISTENT)
# -----------------------------
    def payment_q(method):
        return payments_base.filter(
            payment_method__in=PAYMENT_METHOD_MAP[method]
        )

    manual_qs = payment_q("manual")
    online_qs = payment_q("online")
    bank_qs = payment_q("bank")

# -----------------------------
# TOTALS
# -----------------------------
    total_paid = payments_base.aggregate(
        total=Coalesce(Sum("amount"), Decimal("0"))
    )["total"]

    manual_total = manual_qs.aggregate(
        total=Coalesce(Sum("amount"), Decimal("0"))
    )["total"]

    paystack_online_total = online_qs.aggregate(
        total=Coalesce(Sum("amount"), Decimal("0"))
    )["total"]

    paystack_bank_total = bank_qs.aggregate(
        total=Coalesce(Sum("amount"), Decimal("0"))
    )["total"]

    paystack_total = paystack_online_total + paystack_bank_total

# -----------------------------
# RECENT LISTS
# -----------------------------
    recent_payments = manual_qs.order_by("-payment_date")[:5]

    recent_paystack_online = online_qs.order_by("-payment_date")[:5]
    recent_paystack_bank = bank_qs.order_by("-payment_date")[:5]

    recent_paystack = payments_base.filter(
        payment_method__in=["online", "bank", "bank_transfer"]
    ).order_by("-payment_date")[:5]

# -----------------------------
# OUTSTANDING (NOW CONSISTENT)
# -----------------------------
    outstanding = total_expected - total_paid

    # -----------------------------
    # Expenses
    # -----------------------------
    expenses = Expense.objects.filter(
        school=school,
        date__gte=start_date
    )
    if current_session:
        expenses = expenses.filter(session=current_session)
    if current_term:
        expenses = expenses.filter(term=current_term)
    recent_expenses = expenses.order_by("-date")[:5]

    # -----------------------------
    # Context
    # -----------------------------
    context = {
        "school": school,

        # Invoice summary
        "total_expected": total_expected,
        "outstanding": outstanding,
        "invoice_breakdown": invoice_breakdown,

        # Paid
        "total_paid": total_paid,
        "manual_total": manual_total,

        # Manual payments
        "recent_payments": recent_payments,

        # Paystack
        "paystack_total": paystack_total,
        "paystack_online_total": paystack_online_total,
        "paystack_bank_total": paystack_bank_total,
        "recent_paystack_online": recent_paystack_online,
        "recent_paystack_bank": recent_paystack_bank,
        "recent_paystack": recent_paystack,

        # Expenses
        "recent_expenses": recent_expenses,

        # Filters
        "sessions": SESSION_LIST,
        "current_session": current_session,
        "current_term": current_term,
        "term_choices": Score.TERM_CHOICES,
        "classes": classes,
        "selected_class": selected_class,
        "search": search,
    }

    return render(request, "finance/dashboard.html", context)






from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q


@login_required
def payments_modal(request):
    school = request.user.school
    start_date = timezone.now() - timedelta(days=365)

    page_number = int(request.GET.get("page", 1))
    method = request.GET.get("method")  # manual | online | bank_transfer

    # -----------------------------
    # Filters (same pattern as dashboard)
    # -----------------------------
    class_id = request.GET.get("class")
    current_term = request.GET.get("term")
    current_session = request.GET.get("session")
    search = request.GET.get("search")

    # -----------------------------
    # Base queryset (SINGLE SOURCE OF TRUTH)
    # -----------------------------
    payments_qs = (
        Payment.objects
        .filter(
            school=school,
            status="approved",
            payment_date__gte=start_date
        )
        .select_related(
            "invoice",
            "invoice__student"
        )
        .order_by("-payment_date")
    )

    # -----------------------------
    # Payment method filter
    # -----------------------------
    method = request.GET.get("method")

    if method in PAYMENT_METHOD_MAP:
        payments_qs = payments_qs.filter(
            payment_method__in=PAYMENT_METHOD_MAP[method]
        )


    # -----------------------------
    # Class filter (via student)
    # -----------------------------
    if class_id:
        payments_qs = payments_qs.filter(
            Q(school_class__id=class_id) |
            Q(invoice__school_class__id=class_id)
        )

    # -----------------------------
    # Term filter (NON-FK)
    # -----------------------------
    if current_term:
        payments_qs = payments_qs.filter(
            invoice__term=current_term
        )

    # -----------------------------
    # Session filter (NON-FK)
    # -----------------------------
    if current_session:
        payments_qs = payments_qs.filter(
            invoice__session=current_session
        )

    # -----------------------------
    # Student search
    # -----------------------------
    if search:
        payments_qs = payments_qs.filter(
            Q(invoice__student__user__first_name__icontains=search) |
            Q(invoice__student__user__last_name__icontains=search) |
            Q(invoice__student__admission_no__icontains=search) |
            Q(student__user__first_name__icontains=search) |
            Q(student__user__last_name__icontains=search) |
            Q(student__admission_no__icontains=search)
        )

    # -----------------------------
    # Pagination
    # -----------------------------
    paginator = Paginator(payments_qs, 20)
    page_obj = paginator.get_page(page_number)

    # -----------------------------
    # Classes for dropdown ✅ (THIS WAS MISSING)
    # -----------------------------
    classes = SchoolClass.objects.filter(
        school=school
    ).order_by("name")

    # -----------------------------
    # Render rows
    # -----------------------------
    html = render_to_string(
        "partials/payment_rows.html",
        {
            "page_obj": page_obj,
            "classes": classes,              # 👈 now available
            "current_class": class_id,
            "current_term": current_term,
            "current_session": current_session,
        },
        request=request
    )

    return JsonResponse({
        "html": html,
        "has_next": page_obj.has_next(),
        "has_prev": page_obj.has_previous(),
        "page": page_obj.number,
        "num_pages": page_obj.paginator.num_pages,
    })






def payment_void(request, pk):
    if not request.user.is_accountant_user:
        messages.error(request, "You do not have permission to void payments.")
        return redirect("finance:payment_list")

    payment = get_object_or_404(Payment, pk=pk)

    if payment.payment_method not in ["cash", "pos"]:
        messages.error(request, "Only manual payments can be voided.")
        return redirect("finance:payment_list")

    if payment.status != "approved":
        messages.warning(request, "Payment is already voided or reversed.")
        return redirect("finance:payment_list")

    # Void the payment
    payment.status = "voided"
    payment.save(update_fields=["status"])

    # Recalculate invoice amount_paid
    payment.invoice.recalc_amount_paid()

    messages.success(request, f"Payment {payment.reference} has been voided and invoice updated.")
    return redirect("finance:payment_list")





from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import SchoolTransaction
from .forms import SchoolTransactionForm


@login_required
def transaction_list(request, school_id):
    school = get_object_or_404(School, id=school_id)
    transactions = SchoolTransaction.objects.filter(school=school)
    return render(request, "finance/transaction_list.html", {"transactions": transactions, "school": school})

@login_required
def transaction_create(request, school_id):
    school = get_object_or_404(School, id=school_id)

    if request.method == "POST":
        form = SchoolTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.school = school
            transaction.user = request.user
            transaction.save()
            messages.success(request, "Transaction created successfully.")
            return redirect("finance:transaction_list", school.id)
    else:
        form = SchoolTransactionForm()

    return render(request, "finance/transaction_form.html", {"form": form, "school": school})

@login_required
def transaction_update(request, pk):
    transaction = get_object_or_404(SchoolTransaction, pk=pk)
    school = transaction.school

    if request.method == "POST":
        form = SchoolTransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, "Transaction updated successfully.")
            return redirect("finance:transaction_list", school.id)
    else:
        form = SchoolTransactionForm(instance=transaction)

    return render(request, "finance/transaction_form.html", {"form": form, "school": school})

@login_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(SchoolTransaction, pk=pk)
    school_id = transaction.school.id
    transaction.delete()
    messages.success(request, "Transaction deleted successfully.")
    return redirect("finance:transaction_list", school_id)

from django.http import JsonResponse
from django.db.models import Sum
from django.utils import timezone
from django.db.models.functions import TruncMonth



from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models.functions import TruncMonth

@login_required
def finance_summary_json(request):
    school = request.user.school

    current_session = request.GET.get("session")
    current_term = request.GET.get("term")

    # Always work with datetime first
    today = timezone.now()
    start_date = today - timedelta(days=365)

    # =====================
    # INCOME (Payments)
    # =====================
    payments = Payment.objects.filter(
        school=school,
        payment_date__gte=start_date
    )

    if current_session:
        payments = payments.filter(invoice__session=current_session)

    if current_term:
        payments = payments.filter(invoice__term=current_term)

    income_qs = (
        payments
        .annotate(month=TruncMonth("payment_date"))
        .values("month")
        .annotate(total=Sum("amount"))
    )

    # Normalize income months to DATE
    income_map = {
        row["month"].date(): row["total"]
        for row in income_qs
    }

    # =====================
    # EXPENSES
    # =====================
    expenses = Expense.objects.filter(
        school=school,
        date__gte=start_date.date()
    )

    if current_session:
        expenses = expenses.filter(session=current_session)

    if current_term:
        expenses = expenses.filter(term=current_term)

    expense_qs = (
        expenses
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Sum("amount"))
    )

    # Normalize expense months to DATE
    expense_map = {
        (
            row["month"].date()
            if hasattr(row["month"], "date")
            else row["month"]
        ): row["total"]
        for row in expense_qs
    }

    # =====================
    # MERGE MONTHS SAFELY
    # =====================
    months = sorted(
        set(income_map.keys()) | set(expense_map.keys())
    )

    labels = [m.strftime("%b %Y") for m in months]
    income_data = [income_map.get(m, 0) for m in months]
    expense_data = [expense_map.get(m, 0) for m in months]

    return JsonResponse({
        "labels": labels,
        "income": income_data,
        "expense": expense_data,
    })





from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from results.utils import SESSION_LIST
from finance.models import Invoice, Payment, Expense, Receipt
from students.models import Student
from results.models import Score

from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.http import HttpResponse


from .models import Invoice, Payment, Expense, Receipt
from .forms import InvoiceForm, PaymentForm, ExpenseForm, FinanceReportForm, BulkInvoiceForm

from accounts.models import SystemSetting



from decimal import Decimal
from django.db.models import Sum
from django.db.models.functions import Coalesce
from datetime import timedelta
from django.utils import timezone
import requests
from students.models import VirtualAccount
from .utils import ensure_virtual_accounts

PAYSTACK_BASE_URL = "https://api.paystack.co"


def verify_virtual_account(student):
    """
    Always reflect LIVE Paystack virtual account state.

    ✔ Supports MULTIPLE virtual accounts
    ✔ Titan preferred as primary
    ✔ No Student VA fields touched
    ✔ Safe to call repeatedly
    """

    now = timezone.now()

    # No customer → no VA possible
    if not student.paystack_customer_code:
        return False

    headers = {
        "Authorization": f"Bearer {student.school.paystack_secret_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.get(
            f"{PAYSTACK_BASE_URL}/dedicated_account",
            headers=headers,
            params={"customer": student.paystack_customer_code},
            timeout=15,
        )
        data = resp.json()
    except Exception:
        # Network error → keep existing accounts
        return student.virtual_accounts.exists()

    if not resp.ok or not data.get("status"):
        return student.virtual_accounts.exists()

    paystack_accounts = data.get("data") or []

    if not paystack_accounts:
        # Paystack has zero accounts → soft clear locally
        student.virtual_accounts.all().delete()
        return False

    seen_account_numbers = set()

    for va in paystack_accounts:
        account_number = va.get("account_number")
        if not account_number:
            continue

        bank = va.get("bank", {}) or {}
        bank_slug = bank.get("slug")
        bank_name = bank.get("name")

        seen_account_numbers.add(account_number)

        obj, created = VirtualAccount.objects.update_or_create(
            student=student,
            account_number=account_number,
            defaults={
                "account_name": va.get("account_name", ""),
                "bank_name": bank_name,
                "bank_slug": bank_slug,
                "verified_at": now,
            },
        )

        # Prefer Paystack Titan as primary
        if bank_slug in ("paystack-titan", "titan-paystack"):
            VirtualAccount.objects.filter(student=student).exclude(
                id=obj.id
            ).update(is_primary=False)

            if not obj.is_primary:
                obj.is_primary = True
                obj.save(update_fields=["is_primary"])

    # Remove stale local accounts not in Paystack anymore
    student.virtual_accounts.exclude(
        account_number__in=seen_account_numbers
    ).delete()

    # Ensure ONE primary exists
    if not student.virtual_accounts.filter(is_primary=True).exists():
        first = student.virtual_accounts.first()
        if first:
            first.is_primary = True
            first.save(update_fields=["is_primary"])

    return True




# -----------------------------
# Student Dashboard
# -----------------------------
from django.db.models import Sum, Q
from decimal import Decimal

from django.db.models import Sum, Q
from decimal import Decimal

@login_required
@portal_required("finance")
def student_dashboard(request):
    if not hasattr(request.user, 'student_profile'):
        return redirect('accounts:login')

    student = request.user.student_profile

    # Ensure all VAs exist for this student
    ensure_virtual_accounts(student)
    verify_virtual_account(student)  # optional, keep your verification logic

    # Current filters
    current_session = request.GET.get('session', SESSION_LIST[0])
    current_term = request.GET.get('term', '1')
    current_class_id = request.GET.get('class', student.school_class.id)

    classes = SchoolClass.objects.filter(school=student.school).order_by('name')

    # -----------------------------
    # Invoices
    # -----------------------------
    invoices = Invoice.objects.filter(
        student=student,
        session=current_session,
        term=current_term,
        school_class_id=current_class_id
    ).order_by('-created_at')

    for inv in invoices:
        inv.recalc_amount_paid()


    total_invoiced = invoices.aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0')

    total_paid = invoices.aggregate(
        total=Sum('amount_paid')
    )['total'] or Decimal('0')

    outstanding = total_invoiced - total_paid

    # -----------------------------
    # Payments
    # Include payments via invoice or student VAs
    # -----------------------------
    payments_base = (
        Payment.objects
        .filter(status='approved', invoice__in=invoices)
        .select_related('invoice', 'invoice__student')
        .order_by('-payment_date')
    )



    payments = payments_base[:10]

    # -----------------------------
    # Context
    # -----------------------------
    context = {
        'student': student,
        'invoices': invoices,
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'outstanding': outstanding,
        'payments': payments,
        'sessions': SESSION_LIST,
        'current_session': current_session,
        'terms': Score.TERM_CHOICES,
        'current_term': current_term,
        'classes': classes,
        'current_class_id': int(current_class_id),
    }

    return render(request, 'finance/student_dashboard.html', context)



from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
from django.shortcuts import render


# views.py

from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def invoice_list(request):
    school = request.user.school

    search = request.GET.get("search", "").strip()
    current_class = request.GET.get("class", "")
    current_session = request.GET.get("session", "")
    current_term = request.GET.get("term", "")

    invoices = (
        Invoice.objects
        .filter(school=school)
        .select_related(
            "student",
            "student__user",
            "school_class"
        )
        .prefetch_related(
            Prefetch(
                "transactions",
                queryset=PaystackTransaction.objects.filter(status="success"),
                to_attr="successful_transactions"
            )
        )
        .order_by("-created_at")
    )

    if search:
        invoices = invoices.filter(
            Q(student__user__first_name__icontains=search) |
            Q(student__user__last_name__icontains=search) |
            Q(student__user__username__icontains=search) |
            Q(student__admission_no__icontains=search) |
            Q(admission_application__student_name__icontains=search) |
            Q(admission_application__application_number__icontains=search)
        ).distinct()

    if current_class:
        invoices = invoices.filter(school_class_id=current_class)

    if current_session:
        invoices = invoices.filter(session=current_session)

    if current_term:
        invoices = invoices.filter(term=current_term)

    # ============================
    # Pagination
    # ============================
    paginator = Paginator(invoices, 10)
    page_number = request.GET.get("page")
    invoices = paginator.get_page(page_number)

    context = {
        "invoices": invoices,
        "search": search,
        "current_class": current_class,
        "current_session": current_session,
        "current_term": current_term,
        "classes": SchoolClass.objects.filter(
            school=school
        ).order_by("name"),
        "sessions": SESSION_LIST,
        "term_choices": Score.TERM_CHOICES,
    }

    return render(request, "finance/invoice_list.html", context)

from django.db.models import F

@login_required
def bulk_delete_invoices(request):
    if request.method == "POST":
        invoice_ids = request.POST.getlist("invoice_ids")

        if invoice_ids:
            deleted_count, _ = Invoice.objects.filter(
                id__in=invoice_ids,
                school=request.user.school,
                amount_paid__lt=F("total_amount")  # Prevent deleting fully paid invoices
            ).delete()

            if deleted_count:
                messages.success(
                    request,
                    f"{deleted_count} invoice(s) deleted successfully."
                )
            else:
                messages.warning(
                    request,
                    "Selected invoices are fully paid and cannot be deleted."
                )
        else:
            messages.warning(
                request,
                "No invoices were selected."
            )

    return redirect("finance:invoice_list")




@login_required
def approve_payment(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id)
    invoice = payment.invoice

    # 🔐 Paystack is auto-approved & immutable
    if payment.payment_method == "online":
        return HttpResponseForbidden("Online payments cannot be approved manually")

    # 🚫 Invoice already settled
    if invoice.amount_paid >= invoice.total_amount:
        messages.error(request, "Invoice already fully paid.")
        return redirect("finance:payment_list")

    # 🚫 Already approved
    if payment.status == "approved":
        return redirect("finance:payment_list")

    payment.status = "approved"
    payment.approved_by = request.user
    payment.save()

    return redirect("finance:payment_list")



from collections import defaultdict


@login_required
def invoice_create(request):
    school = getattr(request.user, "school", None)
    if not school:
        return HttpResponse("User is not assigned to any school")

    # System settings
    system_setting, _ = SystemSetting.objects.get_or_create(id=1)
    current_session = system_setting.current_session
    current_term = system_setting.current_term

    # Fetch classes and active fee templates
    classes = school.classes.prefetch_related("students").all()
    templates = FeeTemplate.objects.filter(
        school=school,
        is_active=True
    ).select_related("school_class")

    # Group templates by class for JavaScript filtering
    templates_by_class = defaultdict(list)
    for template in templates:
        templates_by_class[template.school_class.id].append(template)

    if request.method == "POST":
        form = InvoiceForm(request.POST, school=school)

        if form.is_valid():
            students = form.cleaned_data["students"]

            for student in students:
                Invoice.objects.create(
                    school=school,
                    school_class=form.cleaned_data["school_class"],
                    student=student,
                    title=form.cleaned_data["title"],
                    total_amount=form.cleaned_data["total_amount"],
                    due_date=form.cleaned_data["due_date"],
                    session=form.cleaned_data["session"],
                    term=form.cleaned_data["term"],
                )

            messages.success(
                request,
                f"{students.count()} invoice(s) created successfully."
            )
            return redirect("finance:invoice_list")

        else:
            print(form.errors)

    else:
        form = InvoiceForm(
            school=school,
            initial={
                "session": current_session,
                "term": current_term,
            },
        )

    return render(
        request,
        "finance/invoice_form.html",
        {
            "form": form,
            "classes": classes,
            "templates_by_class": templates_by_class,
        },
    )



@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice,
        pk=pk,
        school=request.user.school
    )

    can_delete = (
        getattr(request.user, "is_superadmin", False)
        or getattr(request.user, "is_schooladmin", False)
        or "accountant" in getattr(request.user, "roles", [])
    )

    return render(
        request,
        "finance/invoice_detail.html",
        {
            "invoice": invoice,
            "can_delete": can_delete,
        }
    )




@login_required
def expense_list(request):
    expenses = Expense.objects.filter(school=request.user.school)
    return render(request, "finance/expense/list.html", {"expenses": expenses})


@login_required
def expense_create(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.school = request.user.school
            expense.save()
            return redirect("finance:expense_list")
    else:
        form = ExpenseForm()

    return render(request, "finance/expense/form.html", {"form": form})


@login_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(
        Invoice,
        pk=pk,
        school=request.user.school
    )
    return generate_invoice_pdf(invoice)


@login_required
def receipt_pdf(request, pk):
    receipt = get_object_or_404(
        Receipt,
        pk=pk,
        school=request.user.school
    )
    return generate_receipt_pdf(receipt)



from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import BulkInvoiceForm
from .models import Invoice, FeeTemplate
from datetime import date, timedelta


@login_required
def bulk_generate_invoices(request):
    # Determine the school of the logged-in user
    school = getattr(request.user, "school", None)
    if not school:
        messages.error(request, "No school assigned to your account.")
        return redirect("dashboard")  # or another safe page

    # Fetch active fee templates and classes
    templates = FeeTemplate.objects.filter(school=school, is_active=True)
    classes = school.classes.prefetch_related("students").all()  # Ensure School has 'classes' related_name

    if request.method == "POST":
        form = BulkInvoiceForm(request.POST, school=school)
        if form.is_valid():
            school_class = form.cleaned_data["school_class"]
            fee_template = form.cleaned_data["fee_template"]
            session = form.cleaned_data["session"]
            term = form.cleaned_data["term"]

            # Validate that the fee template matches the selected class
            if fee_template.school_class != school_class:
                messages.error(request, "Fee template does not match selected class.")
                return redirect("finance:bulk_generate_invoices")

            students = school_class.students.all()
            created_count = 0

            for student in students:
                # Set a default due date 30 days from today
                due_date = date.today() + timedelta(days=30)

                obj, was_created = Invoice.objects.get_or_create(
                    student=student,
                    school=school,
                    school_class=school_class,
                    session=session,
                    term=term,
                    title=fee_template.name,
                    defaults={
                        "total_amount": fee_template.amount,
                        "due_date": due_date,  # <-- add due_date here
                    }
                )
                if was_created:
                    created_count += 1

            messages.success(
                request,
                f"{created_count} invoices generated using '{fee_template.name}'."
            )

            # Optional: redirect with ?generated=true to trigger PDF download
            return redirect(f"{request.path}?generated=true")
    else:
        form = BulkInvoiceForm(school=school)

    return render(
        request,
        "finance/invoice_bulk_form.html",
        {
            "form": form,
            "templates": templates,
            "classes": classes,
        }
    )




@login_required
def fee_template_list(request):
    templates = FeeTemplate.objects.filter(school=request.user.school)
    return render(request, "finance/fee_list.html", {"templates": templates})


@login_required
def fee_template_create(request):
    if request.method == "POST":
        form = FeeTemplateForm(request.POST, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.school = request.user.accountant_profile.school  # assign school
            obj.save()
            messages.success(request, "Fee template created")
            return redirect("finance:fee_template_list")
    else:
        form = FeeTemplateForm(user=request.user)

    return render(request, "finance/fee_form.html", {"form": form})





@login_required
def finance_report(request):
    school = request.user.school
    form = FinanceReportForm(request.GET or None, school=school)

    invoices = Invoice.objects.filter(school=school)
    payments = Payment.objects.filter(school=school)
    expenses = Expense.objects.filter(school=school)

    if form.is_valid():
        session = form.cleaned_data["session"]
        term = form.cleaned_data["term"]
        school_class = form.cleaned_data.get("school_class")

        invoices = invoices.filter(session=session, term=term)
        payments = payments.filter(session=session, term=term)
        expenses = expenses.filter(session=session, term=term)

        if school_class:
            invoices = invoices.filter(school_class=school_class)
            payments = payments.filter(school_class=school_class)
            expenses = expenses.filter(school_class=school_class)

    total_invoiced = invoices.aggregate(t=models.Sum("total_amount"))["t"] or 0
    total_paid = payments.aggregate(t=models.Sum("amount"))["t"] or 0
    total_expense = expenses.aggregate(t=models.Sum("amount"))["t"] or 0

    context = {
        "form": form,
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "total_expense": total_expense,
        "balance": total_paid - total_expense,
        "invoices": invoices,
    }

    return render(request, "finance/report/dashboard.html", context)


from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from students.models import SchoolClass

@login_required
def invoice_update(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    school = getattr(request.user, "school", None)
    if not school:
        return HttpResponse("User is not assigned to any school")

    # Ensure the invoice belongs to the user's school
    if invoice.school != school:
        return HttpResponse("You cannot edit invoices from another school.")

    if request.method == "POST":
        form = InvoiceForm(request.POST, instance=invoice, school=school)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.school = school  # always assign school
            invoice.save()
            return redirect("finance:invoice_list")
    else:
        form = InvoiceForm(instance=invoice, school=school)

    return render(request, "finance/invoice_form.html", {"form": form, "invoice": invoice})




@login_required
def generate_invoices(request):
    school = getattr(request.user, "school", None)
    if not school:
        return HttpResponse("User is not assigned to any school.")

    # Use session/term from GET if provided, else fallback to system settings
    system_setting, _ = SystemSetting.objects.get_or_create(id=1)
    session = request.GET.get("session") or system_setting.current_session
    term = request.GET.get("term") or system_setting.current_term

    students = Student.objects.filter(school=school).order_by("school_class", "admission_no")
    school_classes = SchoolClass.objects.filter(school=school)

    # Create invoices for all students if they don't already exist
    for student in students:
        if not Invoice.objects.filter(student=student, session=session, term=term).exists():
            Invoice.objects.create(
                school=school,
                school_class=student.school_class,
                student=student,
                title=f"Invoice for {session} Term {term}",
                total_amount=0,  # Set default or customize per class/student
                due_date=None,   # Optional default due date
                session=session,
                term=term,
            )

    # Redirect to invoice list with session/term filters applied
    return redirect(f"{reverse('finance:invoice_list')}?session={session}&term={term}")





from decimal import Decimal

@login_required
def record_payment(request):
    school = request.user.school

    # Preserve filters across GET and POST
    current_session = (
        request.POST.get("session")
        or request.GET.get("session")
        or SESSION_LIST[0]
    )

    current_term = (
        request.POST.get("term")
        or request.GET.get("term")
        or "1"
    )

    current_class = (
        request.POST.get("school_class")
        or request.GET.get("class")
        or ""
    )

    # Base querysets
    invoices = Invoice.objects.filter(
        school=school,
        session=current_session,
        term=current_term,
    ).select_related("student", "school_class")

    students = Student.objects.filter(school=school)

    if current_class:
        invoices = invoices.filter(school_class_id=current_class)
        students = students.filter(school_class_id=current_class)

    if request.method == "POST":
        form = PaymentForm(
            request.POST,
            school=school,
            initial={"school_class": current_class},
        )

        if form.is_valid():
            payment = form.save(commit=False)
            payment.school = school
            payment.recorded_by = request.user
            payment.session = current_session
            payment.term = current_term

            invoice = payment.invoice
            outstanding = invoice.total_amount - invoice.amount_paid

            if payment.amount > outstanding:
                form.add_error(
                    "amount",
                    f"Payment exceeds outstanding balance "
                    f"(₦{outstanding:,.2f})"
                )
            else:
                payment.save()

                Receipt.objects.create(
                    student=invoice.student,
                    school_class=invoice.school_class,
                    payment=payment,
                    amount=payment.amount,
                    session=payment.session,
                    term=payment.term,
                    school=school,
                )

                messages.success(
                    request,
                    "Payment recorded successfully."
                )

                return redirect(
                    f"{reverse('finance:record_payment')}"
                    f"?class={current_class}"
                    f"&session={current_session}"
                    f"&term={current_term}"
                )
    else:
        form = PaymentForm(
            school=school,
            initial={
                "school_class": current_class,
            },
        )

    return render(
        request,
        "finance/record_payment.html",
        {
            "form": form,
            "students": students,
            "invoices": invoices,
            "school": school,
            "session": current_session,
            "term": current_term,
            "current_class": current_class,
            "sessions": SESSION_LIST,
            "term_choices": Score.TERM_CHOICES,
            "selected_students": request.POST.getlist("students"),
        },
    )


from django.db.models import Sum, F
from decimal import Decimal

@login_required
def financial_reports(request):
    school = request.user.school
    start_date = timezone.now() - timedelta(days=365)

    selected_session = request.GET.get("session")
    selected_term = request.GET.get("term")
    selected_class = request.GET.get("school_class")

    # ---------------------------------------------------
    # INVOICES
    # ---------------------------------------------------
    invoices = Invoice.objects.filter(
        school=school,
        created_at__gte=start_date
    )

    if selected_session:
        invoices = invoices.filter(session=selected_session)

    if selected_term:
        invoices = invoices.filter(term=selected_term)

    if selected_class:
        invoices = invoices.filter(school_class_id=selected_class)

    invoices = invoices.annotate(
        balance=F("total_amount") - F("amount_paid")
    )

    total_invoiced = invoices.aggregate(
        total=Coalesce(Sum("total_amount"), Decimal("0"))
    )["total"]

    # ---------------------------------------------------
    # PAYMENTS
    # ---------------------------------------------------
    student_ids_with_va = VirtualAccount.objects.filter(
        student__school=school
    ).values_list("student_id", flat=True)

    payments = Payment.objects.filter(
        school=school,
        status="approved",
        payment_date__gte=start_date
    ).filter(
        Q(invoice__isnull=False) |
        Q(student_id__in=student_ids_with_va)
    )

    if selected_session:
        payments = payments.filter(
            Q(invoice__session=selected_session) |
            Q(session=selected_session)
        )

    if selected_term:
        payments = payments.filter(
            Q(invoice__term=selected_term) |
            Q(term=selected_term)
        )

    if selected_class:
        payments = payments.filter(
            Q(invoice__school_class_id=selected_class) |
            Q(student__school_class_id=selected_class)
        )

    total_paid = payments.aggregate(
        total=Coalesce(Sum("amount"), Decimal("0"))
    )["total"]

    # ---------------------------------------------------
    # BALANCE
    # ---------------------------------------------------
    total_balance = total_invoiced - total_paid

    # ---------------------------------------------------
    # DISPLAY VALUES (truncate decimals, don't round)
    # ---------------------------------------------------
    total_invoiced_display = int(total_invoiced)
    total_paid_display = int(total_paid)
    total_balance_display = int(total_balance)

    context = {
        "school": school,
        "invoices": invoices,

        # Exact values
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "total_balance": total_balance,

        # Display values
        "total_invoiced_display": total_invoiced_display,
        "total_paid_display": total_paid_display,
        "total_balance_display": total_balance_display,

        # Filters
        "classes": SchoolClass.objects.filter(
            school=school
        ).order_by("name"),
        "sessions": SESSION_LIST,
        "terms": Score.TERM_CHOICES,
        "selected_session": selected_session,
        "selected_term": selected_term,
        "selected_class": selected_class,
    }

    return render(
        request,
        "finance/financial_report.html",
        context
    )






@login_required
def payment_receipt(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id, school=request.user.school)
    return render(request, "finance/payment_receipt.html", {"payment": payment})



@login_required
def student_payments(request, student_id):
    student = get_object_or_404(Student, pk=student_id, school=request.user.school)
    payments = Payment.objects.filter(student=student, school=request.user.school).order_by("-payment_date")

    return render(request, "finance/student_payments.html", {
        "student": student,
        "payments": payments,
    })




@login_required
def payment_reverse(request, pk):
    payment = get_object_or_404(Payment, pk=pk, school=request.user.school)
    if request.method == "POST":
        invoice = payment.invoice
        invoice.amount_paid -= payment.amount
        invoice.save()
        payment.delete()
        messages.success(request, "Payment reversed successfully.")
        return redirect("finance:student_payments", student_id=payment.student.id)

    return render(request, "finance/payment_reverse_confirm.html", {"payment": payment})


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Invoice, Payment

@login_required
def invoice_payments_json(request, invoice_id):
    """
    Return JSON of all payments for a given invoice.
    """
    try:
        invoice = Invoice.objects.get(id=invoice_id, school=request.user.school)
    except Invoice.DoesNotExist:
        return JsonResponse({"error": "Invoice not found"}, status=404)

    payments = Payment.objects.filter(invoice=invoice).order_by('-payment_date')
    payments_data = [
        {
            "id": p.id,
            "title": p.invoice.title,
            "amount": f"₦{p.amount:.2f}",
            "method": p.get_payment_method_display(),
            "date": p.payment_date.strftime("%d-%b-%Y"),
        }
        for p in payments
    ]

    data = {
        "student": str(invoice.student),
        "payments": payments_data,
    }
    return JsonResponse(data)




@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, school=request.user.school)

    if request.method == "POST":
        invoice.delete()
        messages.success(request, "Invoice deleted successfully.")
        return redirect("finance:invoice_list")

    return render(request, "finance/invoice_confirm_delete.html", {
        "invoice": invoice
    })



@login_required
def payment_delete(request, pk):
    payment = get_object_or_404(
        Payment, pk=pk, school=request.user.school
    )

    if request.method == "POST":
        payment.delete()
        messages.success(request, "Payment deleted.")
        return redirect("finance:payment_list")

    return render(request, "finance/payment_confirm_delete.html", {
        "payment": payment
    })

from django.contrib.auth.decorators import login_required
from results.utils import SESSION_LIST
from results.models import Score
from students.models import SchoolClass


def filter_by_student_name(queryset, name):
    """
    Filter payments by student user name (first, last, or username).
    Supports multi-word searches.
    """
    if not name:
        return queryset

    terms = name.split()
    name_q = Q()

    for term in terms:
        name_q &= (
            Q(invoice__student__user__first_name__icontains=term) |
            Q(invoice__student__user__last_name__icontains=term) |
            Q(invoice__student__user__username__icontains=term)
        )

    return queryset.filter(name_q)


@login_required
def payment_list(request):
    school = request.user.school

    payments = (
        Payment.objects
        .filter(school=school)
        .select_related(
            "invoice",
            "invoice__student",
            "invoice__student__school_class",
            "invoice__student__user",
        )
    )

    # ---- READ FILTERS ----
    filters = {
        "class": request.GET.get("class"),
        "term": request.GET.get("term"),
        "session": request.GET.get("session"),
        "name": request.GET.get("name"),
    }

    # ---- APPLY FILTERS ----
    if filters["class"]:
        payments = payments.filter(
            invoice__student__school_class_id=filters["class"]
        )

    if filters["term"]:
        payments = payments.filter(
            invoice__term=filters["term"]
        )

    if filters["session"]:
        payments = payments.filter(
            invoice__session=filters["session"]
        )

    payments = filter_by_student_name(payments, filters["name"])

    return render(request, "finance/payment_list.html", {
        "payments": payments,
        "classes": school.classes.all(),
        "terms": Score.TERM_CHOICES,
        "sessions": SESSION_LIST,
        "filters": filters,
    })




@login_required
def payment_update(request, pk):
    payment = get_object_or_404(
        Payment, pk=pk, school=request.user.school
    )

    if request.method == "POST":
        form = PaymentForm(request.POST, instance=payment, school=request.user.school)
        if form.is_valid():
            form.save()
            messages.success(request, "Payment updated.")
            return redirect("finance:payment_list")
    else:
        form = PaymentForm(instance=payment, school=request.user.school)

    return render(request, "finance/payment_form.html", {
        "form": form,
        "title": "Edit Payment"
    })


@login_required
def fee_template_edit(request, pk):
    school = request.user.school

    template = get_object_or_404(
        FeeTemplate,
        pk=pk,
        school=school
    )

    if request.method == "POST":
        form = FeeTemplateForm(
            request.POST,
            instance=template
        )
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Fee template updated successfully."
            )
            return redirect("finance:fee_template_list")
    else:
        # 🔑 Binds existing data (including school_class)
        form = FeeTemplateForm(instance=template)

    return render(
        request,
        "finance/fee_form.html",
        {
            "form": form,
            "is_edit": True,
            "page_title": "Edit Fee Template",
        }
    )



@login_required
def fee_template_delete(request, pk):
    school = request.user.school
    template = get_object_or_404(FeeTemplate, pk=pk, school=school)

    if request.method == "POST":
        template.delete()
        messages.success(request, "Fee template deleted successfully.")
        return redirect("finance:fee_template_list")

    return render(request, "finance/fee_confirm_delete.html", {
        "template": template
    })



# finance/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Expense
from .forms import ExpenseForm

@login_required
def expense_list(request):
    school = request.user.school

    selected_session = request.GET.get("session", "")
    selected_term = request.GET.get("term", "")
    search = request.GET.get("q", "")

    expenses = Expense.objects.filter(school=school)

    if selected_session:
        expenses = expenses.filter(session=selected_session)

    if selected_term:
        expenses = expenses.filter(term=selected_term)

    if search:
        expenses = expenses.filter(title__icontains=search)

    expenses = expenses.order_by("-date", "-id")

    context = {
        "expenses": expenses,
        "sessions": (
            Expense.objects.filter(school=school)
            .values_list("session", flat=True)
            .distinct()
            .order_by("session")
        ),
        # Use the choices from the model field itself
        "term_choices": Expense._meta.get_field("term").choices,
        "selected_session": selected_session,
        "selected_term": selected_term,
        "search": search,
    }

    return render(
        request,
        "finance/expense_list.html",
        context,
    )


@login_required
def expense_create(request):
    school = getattr(request.user, "school", None)
    if not school:
        return HttpResponse("User is not assigned to any school")

    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.school = school
            expense.save()
            return redirect("finance:expense_list")
    else:
        form = ExpenseForm()

    context = {
        "form": form,
        "sessions": SESSION_LIST,  # Pass sessions to template if needed
    }
    return render(request, "finance/expense_form.html", context)


@login_required
def expense_update(request, pk):
    school = getattr(request.user, "school", None)
    expense = get_object_or_404(
        Expense,
        pk=pk,
        school=school
    )

    # Get all available sessions for dropdown
    sessions = (
        Expense.objects.filter(school=school)
        .values_list("session", flat=True)
        .distinct()
        .order_by("session")
    )

    if request.method == "POST":
        form = ExpenseForm(
            request.POST,
            instance=expense
        )

        if form.is_valid():
            form.save()
            return redirect("finance:expense_list")

    else:
        form = ExpenseForm(instance=expense)

    context = {
        "form": form,
        "sessions": sessions,
        "current_session": expense.session,
    }

    return render(
        request,
        "finance/expense_form.html",
        context
    )

    
@login_required
def expense_delete(request, pk):
    school = getattr(request.user, "school", None)
    expense = get_object_or_404(Expense, pk=pk, school=school)
    if request.method == "POST":
        expense.delete()
        return redirect("finance:expense_list")
    return render(request, "finance/expense_confirm_delete.html", {"expense": expense})


# finance/views.py
from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from .models import Invoice, Payment, Receipt
from .utils import Paystack

from django.http import JsonResponse

from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from finance.models import Invoice, Payment


from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import requests 
 
import requests
from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from finance.models import Invoice, PaystackTransaction, Payment
from accounts.models import School

from decimal import Decimal
import requests

from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from finance.models import Invoice, PaystackTransaction


@login_required
def pay_invoice(request, invoice_id):
    """
    Initialize a Paystack payment for an invoice.
    Metadata includes student, class, term, session for the webhook.
    """
    invoice = get_object_or_404(
        Invoice,
        pk=invoice_id,
        school=request.user.school
    )
    school = invoice.school

    if not school.paystack_secret_key:
        return JsonResponse(
            {"status": "error", "message": "Paystack secret key not configured for this school."},
            status=400
        )

    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Invalid request method."},
            status=400
        )

    # -----------------------------
    # Validate amount
    # -----------------------------
    try:
        amount = Decimal(request.POST.get("amount"))
    except Exception:
        return JsonResponse(
            {"status": "error", "message": "Invalid amount format."},
            status=400
        )

    outstanding = invoice.total_amount - invoice.amount_paid
    if amount <= 0 or amount > outstanding:
        return JsonResponse(
            {"status": "error", "message": f"Amount must be > 0 and ≤ outstanding ₦{outstanding:.2f}"},
            status=400
        )

    # -----------------------------
    # Convert to kobo
    # -----------------------------
    # -----------------------------------
    # Calculate Paystack fee (Option A)
    # -----------------------------------
    fee, total_to_charge = calculate_paystack_fee(amount)

    amount_kobo = int(total_to_charge * 100)


    # -----------------------------
    # Ensure email exists
    # -----------------------------
    email = (
        invoice.student.user.email
        or school.notification_email
        or "techcenter652@gmail.com"
    )

    # -----------------------------
    # Build callback URL (optional, used only for redirection)
    # -----------------------------
    callback_url = request.build_absolute_uri(
        reverse("finance:paystack_verify", args=[invoice.id])
    )

    # -----------------------------
    # Create pending PaystackTransaction
    # -----------------------------
    try:
        transaction = PaystackTransaction.objects.create(
            school=school,
            invoice=invoice,
            amount=amount,
            paystack_reference="",
            status="pending",
            metadata={
                "paystack_fee": str(fee),
                "gross_amount": str(total_to_charge),
            }
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Failed to create transaction record: {e}"},
            status=500
        )

    # -----------------------------
    # Prepare Paystack request
    # -----------------------------
    headers = {
        "Authorization": f"Bearer {school.paystack_secret_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "email": email,
        "amount": amount_kobo,
        "callback_url": callback_url,
        "metadata": {
            "invoice_id": invoice.id,
            "transaction_id": transaction.id,
            "school_id": school.id,
            "student_id": invoice.student.id,
            "school_class_id": invoice.school_class.id,
            "term": invoice.term,
            "session": invoice.session,
            "payment_type": "invoice",
            "partial_payment": True,
        }
    }

    # -----------------------------
    # Call Paystack API
    # -----------------------------
    try:
        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            json=payload,
            headers=headers,
            timeout=30
        )
        data = response.json()
    except requests.exceptions.Timeout:
        transaction.delete()
        return JsonResponse({"status": "error", "message": "Paystack request timed out."}, status=504)
    except requests.exceptions.ConnectionError:
        transaction.delete()
        return JsonResponse({"status": "error", "message": "Network connection error."}, status=502)
    except Exception as e:
        transaction.delete()
        return JsonResponse({"status": "error", "message": f"Unexpected error: {e}"}, status=500)

    # -----------------------------
    # Handle Paystack response
    # -----------------------------
    if not data.get("status"):
        transaction.delete()
        message = data.get("message") or "Paystack initialization failed."
        return JsonResponse({"status": "error", "message": f"Paystack error: {message}"}, status=400)

    # -----------------------------
    # Update transaction with actual Paystack reference
    # -----------------------------
    try:
        transaction.paystack_reference = data["data"]["reference"]
        transaction.save(update_fields=["paystack_reference"])
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Failed to update transaction reference: {e}"}, status=500)

    # -----------------------------
    # Return checkout URL
    # -----------------------------
    return JsonResponse({
        "status": "success",
        "checkout_url": data["data"]["authorization_url"]
    })



from django.db import transaction



@login_required
def paystack_verify(request, invoice_id):
    """
    Paystack redirect verification (READ-ONLY)

    - Confirms transaction status with Paystack
    - Does NOT create Payment
    - Does NOT update Invoice
    - Webhook is the single source of truth
    """
    invoice = get_object_or_404(
        Invoice,
        pk=invoice_id,
        school=request.user.school
    )
    school = invoice.school
    reference = request.GET.get("reference")

    if not reference:
        messages.error(request, "No payment reference provided.")
        return redirect("finance:student_dashboard")

    # -----------------------------
    # Ensure transaction exists
    # -----------------------------
    ps_transaction = PaystackTransaction.objects.filter(
        paystack_reference=reference,
        invoice=invoice
    ).first()

    if not ps_transaction:
        messages.warning(
            request,
            "Payment is being processed. Your dashboard will update shortly."
        )
        return redirect("finance:student_dashboard")

    # -----------------------------
    # Verify with Paystack
    # -----------------------------
    try:
        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers={"Authorization": f"Bearer {school.paystack_secret_key}"},
            timeout=30
        )
        data = response.json()
    except Exception:
        messages.warning(
            request,
            "Payment verification is pending. Your dashboard will update shortly."
        )
        return redirect("finance:student_dashboard")

    # -----------------------------
    # Check response status
    # -----------------------------
    status = data.get("data", {}).get("status")
    if not data.get("status") or status != "success":
        messages.warning(
            request,
            "Payment is still pending or unsuccessful."
        )
        return redirect("finance:student_dashboard")

    # -----------------------------
    # Optional amount sanity check
    # -----------------------------
    amount_paid = Decimal(data["data"].get("amount", 0)) / 100
    if amount_paid <= 0:
        messages.warning(
            request,
            "Payment received but amount is invalid. Please contact support."
        )
        return redirect("finance:student_dashboard")

    # -----------------------------
    # Success message only
    # -----------------------------
    messages.success(
        request,
        f"Payment of ₦{amount_paid:,.2f} was successful. "
        "Your dashboard will update shortly."
    )

    return redirect("finance:student_dashboard")






import json
import hmac
import hashlib
from decimal import Decimal
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction


# finance/views.py

import json
import hmac
import hashlib
from decimal import Decimal

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Sum

import json
import hmac
import hashlib
from decimal import Decimal
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction


# finance/views.py

import json
import hmac
import hashlib
from decimal import Decimal

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

# finance/views.py
import json
import hmac
import hashlib
from decimal import Decimal
from django.db.models import F, Sum  # ✅ Import F here for virtual account logic

@csrf_exempt
def paystack_webhook(request):
    """
    PAYSTACK WEBHOOK (PRODUCTION SAFE)

    ✔ Per-school signature verification
    ✔ Idempotent
    ✔ Fast DB transaction
    ✔ Safe retries
    ✔ Online + Virtual account
    ✔ No long DB locks
    """

    if request.method != "POST":
        return HttpResponse(status=405)

    payload = request.body
    signature = request.headers.get("X-Paystack-Signature")

    try:
        event = json.loads(payload)
        data = event.get("data") or {}
    except Exception:
        return HttpResponse(status=400)

    event_type = event.get("event")

    if event_type not in {
        "charge.success",
        "transfer.success",
        "deposit.success",
    }:
        return HttpResponse(status=200)

    reference = data.get("reference") or str(data.get("id"))
    amount = Decimal(data.get("amount", 0)) / 100

    if not reference or amount <= 0:
        return HttpResponse(status=200)

    is_virtual_account = (
        data.get("channel") == "dedicated_nuban"
        or event_type in {"transfer.success", "deposit.success"}
    )

    account_number = (
        (data.get("dedicated_account") or {}).get("account_number")
        or (data.get("metadata") or {}).get("receiver_account_number")
    )

    metadata = data.get("metadata") or {}

    school = None
    student = None
    va = None

    school_id = metadata.get("school_id")

    if school_id:
        school = School.objects.filter(id=school_id).first()

    if not school and account_number:
        va = (
            VirtualAccount.objects
            .select_related("student", "student__school")
            .filter(account_number=account_number)
            .first()
        )

        if va:
            student = va.student
            school = student.school

    if not school:
        return HttpResponse(status=200)

    # VERIFY SIGNATURE
    computed_signature = hmac.new(
        school.paystack_secret_key.encode(),
        payload,
        hashlib.sha512
    ).hexdigest()

    if computed_signature != signature:
        return HttpResponse(status=400)

    payment = None
    created = False

    # ==================================================
    # SHORT TRANSACTION ONLY
    # ==================================================
    with transaction.atomic():

        invoice = None

        # ---------------- ONLINE ----------------
        if not is_virtual_account:

            tx = (
                PaystackTransaction.objects
                .select_for_update(skip_locked=True)
                .filter(paystack_reference=reference)
                .first()
            )

            if not tx:
                return HttpResponse(status=200)

            # already processed
            if tx.status == "success":
                return HttpResponse(status=200)

            tx.status = "success"
            tx.save(update_fields=["status"])

            invoice = tx.invoice
            amount = tx.amount

# Normal student invoice
            if invoice.student:
                student = invoice.student

# Admission invoice
            elif invoice.admission_application:
                student = None
        # ---------------- VA ----------------
        else:

            if not student:
                return HttpResponse(status=200)

            invoice = (
                Invoice.objects
                .select_for_update(skip_locked=True)
                .filter(
                    student=student,
                    amount_paid__lt=F("total_amount")
                )
                .order_by("created_at")
                .first()
            )

        # ---------------- PAYMENT ----------------

        payment, created = Payment.objects.get_or_create(
            reference=reference,
            defaults={
                "school": school,
                "invoice": invoice,
                "student": student,
                "school_class": (
                    invoice.school_class if invoice else None
                ),
                "term": (
                    invoice.term if invoice else None
                ),
                "session": (
                    invoice.session if invoice else None
                ),
                "amount": amount,
                "status": "approved",
                "payment_method": (
                    "bank" if is_virtual_account else "online"
                ),
                "metadata": {
                    **data,
                    "va_account_number": account_number,
                    "va_bank": va.bank_name if va else None,
                },
            }
        )

        # already existed
        if not created:
            return HttpResponse(status=200)

        # ---------------- INVOICE UPDATE ----------------

        if invoice:

            total_paid = (
                Payment.objects
                .filter(invoice=invoice)
                .aggregate(
                    total=Sum("amount")
                )["total"]
                or Decimal("0")
            )

            invoice.amount_paid = total_paid
            invoice.save(update_fields=["amount_paid"])

            # ==============================
# ADMISSION PAYMENT UPDATE
# ==============================

            if invoice.is_admission_fee and invoice.admission_application:

                application = invoice.admission_application

                if invoice.amount_paid >= invoice.total_amount:

                    application.invoice_generated = True
                    application.save(
                        update_fields=[
                            "invoice_generated"
                        ]
                    )

            Receipt.objects.get_or_create(
                payment=payment,
                defaults={
                    "student": student,
                    "amount": payment.amount,
                    "school_class": invoice.school_class,
                    "session": invoice.session,
                    "term": invoice.term,
                    "school": school,
                }
            )

    # ==================================================
    # OUTSIDE TRANSACTION (NO LOCKS)
    # ==================================================

    if created:


    # ======================================
    # ADMISSION PAYMENT ACTIVATION
    # ======================================

        try:

            activate_student_after_admission_payment(
                payment
            )

        except Exception as e:

            print(
                "Admission activation error:",
                e
            )

        # SEND LOGIN DETAILS TO PARENT
    # ======================================

        try:

            from tis_website.models import AdmissionApplication
            from students.services.admission_notification import (
                send_student_login_details
            )


            application = None


    # Admission payment
            if payment.invoice.admission_application:

                application = payment.invoice.admission_application


    # Normal student payment
            elif payment.student:

                application = AdmissionApplication.objects.filter(
                    application_number=payment.student.admission_no
                ).first()


            if application:

                send_student_login_details(application)


        except Exception as e:

            print(
                "Login notification error:",
                e
            )

    # ======================================
    # NORMAL PAYMENT NOTIFICATION
    # ======================================

        try:

            send_school_payment_notification(
                payment
            )

        except Exception as e:

            print(
                "Payment notification error:",
                e
            )

    return HttpResponse(status=200)


from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import InvoiceForm


@login_required
def create_admission_invoice(request):

    school = request.user.school

    form = InvoiceForm(
        request.POST or None,
        school=school,
        admission_mode=True
    )


    if request.method == "POST":

        if form.is_valid():

            applications = form.cleaned_data[
                "admission_application"
            ]


            for application in applications:

                Invoice.objects.create(
                    school=school,
                    student=None,
                    school_class=application.class_applying_for,
                    admission_application=application,
                    is_admission_fee=True,
                    title="Admission Fee",
                    total_amount=school.admission_fee,
                    due_date=date.today() + timedelta(days=30),
                    session=form.cleaned_data["session"],
                    term=form.cleaned_data["term"],
                )


            messages.success(
                request,
                "Admission invoice(s) created successfully."
            )

            return redirect(
                "finance:invoice_list"
            )


    return render(
        request,
        "finance/invoice_form.html",
        {
            "form": form,
            "admission_mode": True,
        }
    )