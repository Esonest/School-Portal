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



# Helpers
def staff_required(user):
    return user.is_staff or hasattr(user,'teacher')

# Finance dashboard (admin)

from django.contrib.auth.decorators import login_required
from accounts.models import School  # if needed for school-specific filtering
from datetime import timedelta

TERM_CHOICES = [('1', 'Term 1'), ('2', 'Term 2'), ('3', 'Term 3')]



@login_required
def dashboard(request):
    school = request.user.school

    current_session = request.GET.get("session")
    current_term = request.GET.get("term")

    # ✅ last 12 months range
    start_date = timezone.now() - timedelta(days=365)

    invoices = Invoice.objects.filter(
        school=school,
        created_at__gte=start_date
    )

    # ✅ OPTIONAL filters (only apply if selected)
    if current_session:
        invoices = invoices.filter(session=current_session)

    if current_term:
        invoices = invoices.filter(term=current_term)

    # ✅ aggregates
    total_expected = invoices.aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    total_received = invoices.aggregate(
        total=Sum("amount_paid")
    )["total"] or 0

    outstanding = total_expected - total_received

    # ✅ recent payments (NO session/term filter here)
    recent_payments = Payment.objects.filter(
        school=school
    ).select_related("invoice", "invoice__student").order_by("-payment_date")[:5]

    context = {
        "school": school,
        "invoices": invoices,  # 🔥 THIS NAME MUST MATCH TEMPLATE
        "total_expected": total_expected,
        "total_received": total_received,
        "outstanding": outstanding,
        "recent_payments": recent_payments,
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

    today = timezone.now()
    start_date = today - timedelta(days=365)

    income = (
        Payment.objects.filter(
            school=school,
            payment_date__gte=start_date
        )
        .annotate(month=TruncMonth("payment_date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    expense = (
        Expense.objects.filter(
            school=school,
            date__gte=start_date
        )
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    labels = []
    income_data = []
    expense_data = []

    months = sorted(
        {i["month"] for i in income} | {e["month"] for e in expense}
    )

    for m in months:
        labels.append(m.strftime("%b %Y"))
        income_data.append(next((i["total"] for i in income if i["month"] == m), 0))
        expense_data.append(next((e["total"] for e in expense if e["month"] == m), 0))

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

@portal_required("finance")
@login_required
def student_dashboard(request):
    if not hasattr(request.user, 'student_profile'):
        return redirect('accounts:login')

    student = request.user.student_profile

    # Get filters from GET parameters
    current_session = request.GET.get('session', SESSION_LIST[0])
    current_term = request.GET.get('term', '1')
    current_class_id = request.GET.get('class', student.school_class.id)

    # Get all classes for the dropdown
    classes = SchoolClass.objects.filter(school=student.school).order_by('name')

    # Filter invoices
    invoices = Invoice.objects.filter(
        student=student,
        session=current_session,
        term=current_term,
        school_class_id=current_class_id
    ).order_by('-created_at')

    total_invoiced = invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    total_paid = invoices.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
    outstanding = total_invoiced - total_paid

    # Filter payments by invoices
    payments = Payment.objects.filter(invoice__in=invoices).order_by('-payment_date')[:10]

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






@login_required
def invoice_list(request):
    invoices = Invoice.objects.filter(school=request.user.school)
    return render(request, "finance/invoice_list.html", {"invoices": invoices})


@login_required
def invoice_create(request):
    school = getattr(request.user, "school", None)  # make sure user has a school
    if not school:
        return HttpResponse("User is not assigned to any school")

    system_setting, _ = SystemSetting.objects.get_or_create(id=1)
    current_session = system_setting.current_session
    current_term = system_setting.current_term

    if request.method == "POST":
        form = InvoiceForm(request.POST, school=school)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.school = school  # <-- assign school here
            invoice.save()
            return redirect("finance:invoice_list")
        else:
            print(form.errors)
    else:
        form = InvoiceForm(school=school, initial={
            "session": current_session,
            "term": current_term,
        })

    return render(request, "finance/invoice_form.html", {"form": form})






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

@login_required
def payment_list(request):
    payments = Payment.objects.filter(
        school=request.user.school
    ).select_related("invoice", "invoice__student")

    return render(request, "finance/payment_list.html", {
        "payments": payments
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
