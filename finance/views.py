from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
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

@login_required
def dashboard(request):
    school = request.user.school

    # -----------------------------
    # Filters
    # -----------------------------
    current_session = request.GET.get("session")
    current_term = request.GET.get("term")

    start_date = timezone.now() - timedelta(days=365)

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

    total_expected = invoices.aggregate(
        total=Coalesce(Sum("total_amount"), Decimal("0"))
    )["total"]

    total_received = invoices.aggregate(
        total=Coalesce(Sum("amount_paid"), Decimal("0"))
    )["total"]

    outstanding = total_expected - total_received

    # -----------------------------
    # Payments
    # -----------------------------
    recent_payments = Payment.objects.filter(
        school=school
    ).select_related(
        "invoice", "invoice__student"
    ).order_by("-payment_date")[:5]

    # -----------------------------
    # Paystack
    # -----------------------------
    paystack_qs = PaystackTransaction.objects.filter(
        school=school,
        status="success",
        created_at__gte=start_date
    )

    paystack_total = paystack_qs.aggregate(
        total=Coalesce(Sum("amount"), Decimal("0"))
    )["total"]

    recent_paystack = paystack_qs.select_related(
        "invoice", "invoice__student"
    ).order_by("-created_at")[:5]

    # -----------------------------
    # Expenses
    # -----------------------------
    recent_expenses = Expense.objects.filter(
        school=school,
        date__gte=start_date
    )

    if current_session:
        recent_expenses = recent_expenses.filter(session=current_session)

    if current_term:
        recent_expenses = recent_expenses.filter(term=current_term)

    recent_expenses = recent_expenses.order_by("-date")[:5]

    context = {
        "school": school,

        "invoices": invoices,
        "total_expected": total_expected,
        "total_received": total_received,
        "outstanding": outstanding,

        "recent_payments": recent_payments,

        "paystack_total": paystack_total,
        "recent_paystack": recent_paystack,

        "recent_expenses": recent_expenses,

        "sessions": SESSION_LIST,
        "current_session": current_session,
        "current_term": current_term,
        "term_choices": Score.TERM_CHOICES,
    }

    return render(request, "finance/dashboard.html", context)









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



@login_required
def finance_summary_json(request):
    school = request.user.school

    current_session = request.GET.get("session")
    current_term = request.GET.get("term")

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

    income = (
        payments
        .annotate(month=TruncMonth("payment_date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    # =====================
    # EXPENSES
    # =====================
    expenses = Expense.objects.filter(
        school=school,
        date__gte=start_date
    )

    if current_session:
        expenses = expenses.filter(session=current_session)

    if current_term:
        expenses = expenses.filter(term=current_term)

    expense = (
        expenses
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    # =====================
    # MERGE MONTHS
    # =====================
    months = sorted(
        {i["month"] for i in income} | {e["month"] for e in expense}
    )

    labels = []
    income_data = []
    expense_data = []

    for m in months:
        labels.append(m.strftime("%b %Y"))

        income_data.append(
            next((i["total"] for i in income if i["month"] == m), 0)
        )

        expense_data.append(
            next((e["total"] for e in expense if e["month"] == m), 0)
        )

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
from django.http import JsonResponse
from django.http import HttpResponse


from .models import Invoice, Payment, Expense, Receipt
from .forms import InvoiceForm, PaymentForm, ExpenseForm, FinanceReportForm, BulkInvoiceForm

from accounts.models import SystemSetting



from decimal import Decimal
from django.db.models import Sum
from django.db.models.functions import Coalesce

@portal_required("finance")
@login_required
def student_dashboard(request):
    if not hasattr(request.user, 'student_profile'):
        return redirect('accounts:login')

    student = request.user.student_profile

    current_session = request.GET.get('session', SESSION_LIST[0])
    current_term = request.GET.get('term', '1')
    current_class_id = request.GET.get('class', student.school_class.id)

    classes = SchoolClass.objects.filter(
        school=student.school
    ).order_by('name')

    invoices = Invoice.objects.filter(
        student=student,
        session=current_session,
        term=current_term,
        school_class_id=current_class_id
    ).order_by('-created_at')

    total_invoiced = invoices.aggregate(
        total=Coalesce(Sum('total_amount'), Decimal('0'))
    )['total']

    total_paid = invoices.aggregate(
        total=Coalesce(Sum('amount_paid'), Decimal('0'))
    )['total']

    outstanding = total_invoiced - total_paid

    payments = Payment.objects.filter(
        invoice__in=invoices
    ).order_by('-payment_date')[:10]

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








from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required

@login_required
def invoice_list(request):
    school = request.user.school

    invoices = (
        Invoice.objects
        .filter(school=school)
        .select_related("student", "school_class")
        .prefetch_related(
            Prefetch(
                "transactions",
                queryset=PaystackTransaction.objects.filter(status="success"),
                to_attr="successful_transactions"
            )
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "finance/invoice_list.html",
        {"invoices": invoices}
    )




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
    templates = FeeTemplate.objects.filter(school=school, is_active=True).select_related("school_class")

    # Group templates by class for JS filtering
    templates_by_class = defaultdict(list)
    for template in templates:
        templates_by_class[template.school_class.id].append(template)

    if request.method == "POST":
        form = InvoiceForm(request.POST, school=school)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.school = school
            invoice.save()
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
    invoice = get_object_or_404(Invoice, pk=pk, school=request.user.school)
    return render(request, "finance/invoice_detail.html", {"invoice": invoice})




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
    current_session = request.GET.get("session", SESSION_LIST[0])
    current_term = request.GET.get("term", "1")  # default to first term

    if request.method == "POST":
        form = PaymentForm(request.POST, school=school)
        if form.is_valid():
            payment = form.save(commit=False)

            # 🔒 Set controlled fields (never trust form for these)
            payment.school = school
            payment.recorded_by = request.user

            # If Payment model does NOT have session/term, remove these lines
            payment.session = form.cleaned_data.get("session", current_session)
            payment.term = form.cleaned_data.get("term", current_term)

            # ✅ SAVE ONCE — invoice.amount_paid is auto-synced in model
            payment.save()

            # 🧾 Create receipt (read from invoice to avoid mismatch)
            Receipt.objects.create(
                student=payment.invoice.student,
                school_class=payment.invoice.school_class,
                payment=payment,
                amount=payment.amount,
                session=payment.session,
                term=payment.term,
                school=school,
            )

            messages.success(request, "Payment recorded successfully")
            return redirect("finance:invoice_list")
    else:
        form = PaymentForm(school=school)

    return render(request, "finance/record_payment.html", {
        "form": form,
        "school": school,
        "session": current_session,
        "term": current_term,
        "sessions": SESSION_LIST,
        "term_choices": Score.TERM_CHOICES,
    })



from django.db.models import Sum, F
from decimal import Decimal

@login_required
def financial_reports(request):
    school = request.user.school

    selected_session = request.GET.get("session")
    selected_term = request.GET.get("term")
    selected_class = request.GET.get("school_class")

    invoices = Invoice.objects.filter(school=school)

    if selected_session:
        invoices = invoices.filter(session=selected_session)
    if selected_term:
        invoices = invoices.filter(term=selected_term)
    if selected_class:
        invoices = invoices.filter(school_class_id=selected_class)

    invoices = invoices.annotate(balance=F('total_amount') - F('amount_paid'))

    total_invoiced = invoices.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
    total_paid = invoices.aggregate(total=Sum("amount_paid"))["total"] or Decimal("0")
    total_balance = total_invoiced - total_paid

    context = {
        "school": school,
        "invoices": invoices,
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "total_balance": total_balance,
        "classes": SchoolClass.objects.filter(school=school),
        "sessions": SESSION_LIST,
        "terms": Score.TERM_CHOICES,
        "selected_session": selected_session,
        "selected_term": selected_term,
        "selected_class": selected_class,
    }

    return render(request, "finance/financial_report.html", context)







@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, school=request.user.school)

    if request.method == "POST":
        invoice.delete()
        messages.success(request, f"Invoice '{invoice.title}' has been deleted successfully.")
        return redirect("finance:invoice_list")

    return render(request, "finance/invoice_delete.html", {"invoice": invoice})




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
    school = getattr(request.user, "school", None)
    expenses = Expense.objects.filter(school=school).order_by("-date")
    return render(request, "finance/expense_list.html", {"expenses": expenses})


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
    expense = get_object_or_404(Expense, pk=pk, school=school)
    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect("finance:expense_list")
    else:
        form = ExpenseForm(instance=expense)
    return render(request, "finance/expense_form.html", {"form": form})

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

@login_required
def pay_invoice(request, invoice_id):
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

    # 1️⃣ Validate amount
    try:
        amount = Decimal(request.POST.get("amount"))
    except:
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

    # 2️⃣ Convert to kobo
    amount_kobo = int(amount * 100)

    # 3️⃣ Ensure email exists
    email = invoice.student.user.email or "techcenter652@gmail.com"

    # 4️⃣ Build callback URL
    callback_url = request.build_absolute_uri(
        reverse("finance:paystack_verify", args=[invoice.id])
    )

    # 5️⃣ Create pending PaystackTransaction
    try:
        transaction = PaystackTransaction.objects.create(
            school=school,
            invoice=invoice,
            amount=amount,
            paystack_reference="",  # updated after initialization
            status="pending"
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Failed to create transaction record: {e}"},
            status=500
        )

    # 6️⃣ Prepare Paystack request
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
            "student_id": invoice.student.id,
            "school_id": school.id,
            "transaction_id": transaction.id,
            "payment_type": "invoice",
            "partial_payment": True,
        }
    }

    # 7️⃣ Call Paystack API
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
        return JsonResponse(
            {"status": "error", "message": "Paystack request timed out."},
            status=504
        )
    except requests.exceptions.ConnectionError:
        transaction.delete()
        return JsonResponse(
            {"status": "error", "message": "Network connection error."},
            status=502
        )
    except Exception as e:
        transaction.delete()
        return JsonResponse(
            {"status": "error", "message": f"Unexpected error: {e}"},
            status=500
        )

    # 8️⃣ Handle Paystack response
    if not data.get("status"):
        transaction.delete()
        message = data.get("message") or "Paystack initialization failed."
        return JsonResponse(
            {"status": "error", "message": f"Paystack error: {message}"},
            status=400
        )

    # 9️⃣ Update transaction with actual Paystack reference
    try:
        transaction.paystack_reference = data["data"]["reference"]
        transaction.save(update_fields=["paystack_reference"])
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Failed to update transaction reference: {e}"},
            status=500
        )

    # 10️⃣ Return checkout URL
    return JsonResponse({
        "status": "success",
        "checkout_url": data["data"]["authorization_url"]
    })





@login_required
def pay_invoice(request, invoice_id):
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

    # 1️⃣ Validate amount
    try:
        amount = Decimal(request.POST.get("amount"))
    except:
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

    # 2️⃣ Convert to kobo
    amount_kobo = int(amount * 100)

    # 3️⃣ Ensure email exists
    email = invoice.student.user.email or "techcenter652@gmail.com"

    # 4️⃣ Build callback URL
    callback_url = request.build_absolute_uri(
        reverse("finance:paystack_verify", args=[invoice.id])
    )

    # 5️⃣ Create pending PaystackTransaction
    try:
        transaction = PaystackTransaction.objects.create(
            school=school,
            invoice=invoice,
            amount=amount,
            paystack_reference="",  # updated after initialization
            status="pending"
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Failed to create transaction record: {e}"},
            status=500
        )

    # 6️⃣ Prepare Paystack request
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
            "student_id": invoice.student.id,
            "school_id": school.id,
            "transaction_id": transaction.id,
            "payment_type": "invoice",
            "partial_payment": True,
        }
    }

    # 7️⃣ Call Paystack API
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
        return JsonResponse(
            {"status": "error", "message": "Paystack request timed out."},
            status=504
        )
    except requests.exceptions.ConnectionError:
        transaction.delete()
        return JsonResponse(
            {"status": "error", "message": "Network connection error."},
            status=502
        )
    except Exception as e:
        transaction.delete()
        return JsonResponse(
            {"status": "error", "message": f"Unexpected error: {e}"},
            status=500
        )

    # 8️⃣ Handle Paystack response
    if not data.get("status"):
        transaction.delete()
        message = data.get("message") or "Paystack initialization failed."
        return JsonResponse(
            {"status": "error", "message": f"Paystack error: {message}"},
            status=400
        )

    # 9️⃣ Update transaction with actual Paystack reference
    try:
        transaction.paystack_reference = data["data"]["reference"]
        transaction.save(update_fields=["paystack_reference"])
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Failed to update transaction reference: {e}"},
            status=500
        )

    # 10️⃣ Return checkout URL
    return JsonResponse({
        "status": "success",
        "checkout_url": data["data"]["authorization_url"]
    })



from django.db import transaction


@login_required
def paystack_verify(request, invoice_id):
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

    # 1️⃣ Get transaction
    try:
        ps_transaction = PaystackTransaction.objects.get(paystack_reference=reference)
    except PaystackTransaction.DoesNotExist:
        messages.warning(request, "Transaction not found. Webhook will handle it.")
        return redirect("finance:student_dashboard")

    # 2️⃣ Verify with Paystack safely
    try:
        headers = {"Authorization": f"Bearer {school.paystack_secret_key}"}
        response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
        data = response.json()
    except Exception as e:
        messages.warning(request, f"Verification failed: {e}. Webhook will update the status.")
        return redirect("finance:student_dashboard")

    # 3️⃣ Check Paystack response
    if not data.get("status") or "data" not in data or data["data"].get("status") != "success":
        messages.error(request, "Payment not successful or still pending.")
        return redirect("finance:student_dashboard")

    # 4️⃣ Safely get amount
    amount_paid = Decimal(data["data"].get("amount", 0)) / 100
    if amount_paid <= 0:
        messages.error(request, "Invalid payment amount received.")
        return redirect("finance:student_dashboard")

    # 5️⃣ Process transaction idempotently
    with transaction.atomic():
        if ps_transaction.status != "success":
            ps_transaction.status = "success"
            ps_transaction.save(update_fields=["status"])

        payment, created = Payment.objects.get_or_create(
            reference=reference,
            defaults={
                "school": invoice.school,
                "invoice": invoice,
                "student": invoice.student,
                "school_class": invoice.school_class,
                "amount": amount_paid,
                "payment_method": "online",
                "session": invoice.session,
                "term": invoice.term,
            }
        )

        # Recompute invoice.amount_paid
        invoice.amount_paid = Payment.objects.filter(invoice=invoice).aggregate(total=Sum("amount"))["total"] or 0
        invoice.save(update_fields=["amount_paid"])

        # Create Receipt once
        if created:
            Receipt.objects.create(
                student=invoice.student,
                school_class=invoice.school_class,
                payment=payment,
                amount=payment.amount,
                session=invoice.session,
                term=invoice.term,
                school=invoice.school
            )

    messages.success(request, f"Payment of ₦{amount_paid:.2f} was successful! Invoice will be updated shortly")
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
from django.db.models import Sum



@csrf_exempt
def paystack_webhook(request):
    """
    Paystack webhook handler (SAFE + IDEMPOTENT)

    - Verifies signature
    - Handles retries correctly
    - Creates Payment once
    - ALWAYS recomputes Invoice.amount_paid
    - Generates Receipt once
    """

    if request.method != "POST":
        return HttpResponse(status=405)

    payload = request.body
    signature = request.headers.get("X-Paystack-Signature")

    # -----------------------------
    # 1️⃣ Parse payload safely
    # -----------------------------
    try:
        event = json.loads(payload)
        data = event.get("data", {})
        metadata = data.get("metadata", {})
        school_id = metadata.get("school_id")
    except Exception:
        return HttpResponse(status=400)

    if not school_id:
        return HttpResponse(status=200)

    # -----------------------------
    # 2️⃣ Resolve school
    # -----------------------------
    try:
        school = School.objects.get(id=school_id)
    except School.DoesNotExist:
        return HttpResponse(status=200)

    # -----------------------------
    # 3️⃣ Verify Paystack signature
    # -----------------------------
    computed_hash = hmac.new(
        school.paystack_secret_key.encode(),
        payload,
        hashlib.sha512
    ).hexdigest()

    if computed_hash != signature:
        return HttpResponse(status=400)

    # -----------------------------
    # 4️⃣ Only process success event
    # -----------------------------
    if event.get("event") != "charge.success":
        return HttpResponse(status=200)

    reference = data.get("reference")
    amount = Decimal(data.get("amount", 0)) / 100  # kobo → naira

    if not reference or amount <= 0:
        return HttpResponse(status=200)

    # -----------------------------
    # 5️⃣ Atomic processing
    # -----------------------------
    with transaction.atomic():

        # Lock Paystack transaction
        try:
            tx = (
                PaystackTransaction.objects
                .select_for_update()
                .get(paystack_reference=reference)
            )
        except PaystackTransaction.DoesNotExist:
            return HttpResponse(status=200)

        invoice = tx.invoice

        # Mark Paystack transaction successful (once)
        if tx.status != "success":
            tx.status = "success"
            tx.save(update_fields=["status"])

        # Create Payment ONCE (idempotent)
        payment, created = Payment.objects.get_or_create(
            reference=reference,
            defaults={
                "school": invoice.school,
                "invoice": invoice,
                "student": invoice.student,
                "school_class": invoice.school_class,
                "amount": amount,
                "payment_method": "online",
                "session": invoice.session,
                "term": invoice.term,
            }
        )

        # 🔥 ALWAYS recompute invoice total (DO NOT rely on signals)
        invoice.amount_paid = (
            Payment.objects
            .filter(invoice=invoice)
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0")
        )
        invoice.save(update_fields=["amount_paid"])

        # Create Receipt only once
        if created:
            Receipt.objects.create(
                student=invoice.student,
                school_class=invoice.school_class,
                payment=payment,
                amount=payment.amount,
                session=invoice.session,
                term=invoice.term,
                school=invoice.school
            )

    return HttpResponse(status=200)
