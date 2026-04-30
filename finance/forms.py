from django import forms
from .models import SchoolTransaction, FeeTemplate
from django.forms.widgets import DateInput
from results.utils import SESSION_LIST
from results.models import Score
from students.models import SchoolClass, Student

TAILWIND_INPUT = "w-full border-gray-300 rounded px-3 py-2"

class SchoolTransactionForm(forms.ModelForm):
    class Meta:
        model = SchoolTransaction
        fields = [
            "transaction_type",
            "title",
            "amount",
            "date",
            "session",
            "term",
            "description",
        ]
        widgets = {
            "transaction_type": forms.Select(attrs={"class": TAILWIND_INPUT}),
            "title": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "amount": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "date": DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "session": forms.Select(attrs={"class": TAILWIND_INPUT}, choices=[(s, s) for s in SESSION_LIST]),
            "term": forms.Select(attrs={"class": TAILWIND_INPUT}, choices=Score.TERM_CHOICES),
            "description": forms.Textarea(attrs={"class": TAILWIND_INPUT, "rows": 3}),
        }


from django import forms
from .models import Invoice, Payment, Expense


TAILWIND = "w-full border rounded px-3 py-2"

class InvoiceForm(forms.ModelForm):
    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.none(),
        widget=forms.SelectMultiple(
            attrs={
                "class": TAILWIND,
                "size": 10,
            }
        ),
        required=True,
    )

    fee_template = forms.ModelChoiceField(
        queryset=FeeTemplate.objects.none(),
        empty_label="Select Template",
        required=False,
        widget=forms.Select(
            attrs={
                "class": TAILWIND,
                "id": "fee-template-select",   # Important for JavaScript
            }
        ),
    )

    class Meta:
        model = Invoice
        fields = [
            "school_class",
            "students",
            "fee_template",
            "title",
            "total_amount",
            "due_date",
            "session",
            "term",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": TAILWIND}),
            "total_amount": forms.NumberInput(attrs={"class": TAILWIND}),
            "due_date": forms.DateInput(
                attrs={
                    "class": TAILWIND,
                    "type": "date",
                }
            ),
            "session": forms.Select(
                choices=[(s, s) for s in SESSION_LIST],
                attrs={"class": TAILWIND},
            ),
            "term": forms.Select(
                choices=Score.TERM_CHOICES,
                attrs={"class": TAILWIND},
            ),
        }

    def __init__(self, *args, **kwargs):
        school = kwargs.pop("school", None)
        super().__init__(*args, **kwargs)

        if school:
            # Classes
            self.fields["school_class"].queryset = SchoolClass.objects.filter(
                school=school
            )

            # Students
            self.fields["students"].queryset = Student.objects.filter(school=school).select_related("user", "school_class")
            # Add class data attribute to each student option
            self.fields["students"].choices = [
                (
                    student.pk,
                    student.full_name,
                    {
                        "data-class": str(student.school_class_id),
                    },
                )
                for student in self.fields["students"].queryset
            ]

            # Fee Templates
            self.fields["fee_template"].queryset = FeeTemplate.objects.filter(
                school=school,
                is_active=True,
            ).select_related("school_class")

            


class PaymentForm(forms.ModelForm):
    # Filter-only field (not saved to Payment)
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        required=False,
        label="Class",
        widget=forms.Select(attrs={"class": TAILWIND})
    )

    class Meta:
        model = Payment
        fields = ["school_class", "invoice", "amount", "payment_method"]
        widgets = {
            "invoice": forms.Select(attrs={"class": TAILWIND}),
            "amount": forms.NumberInput(attrs={"class": TAILWIND}),
            "payment_method": forms.Select(attrs={"class": TAILWIND}),
        }

    def __init__(self, *args, **kwargs):
        school = kwargs.pop("school", None)
        super().__init__(*args, **kwargs)

        if school:
            self.fields["school_class"].queryset = SchoolClass.objects.filter(
                school=school
            )

            # IMPORTANT: restrict invoices to this school only
            self.fields["invoice"].queryset = Invoice.objects.filter(
                school=school
            )

        # POST filtering
        class_id = self.data.get("school_class")

        # GET/initial filtering
        if not class_id and self.initial.get("school_class"):
            class_id = self.initial.get("school_class")

        if class_id:
            try:
                queryset = Invoice.objects.filter(
                    school=school,
                    school_class_id=int(class_id)
                )

                self.fields["invoice"].queryset = queryset

            except (ValueError, TypeError):
                pass


# finance/forms.py
from django import forms
from .models import Expense

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["title", "description", "amount", "date","session", "term"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "w-full border rounded px-3 py-2"}),
            "description": forms.Textarea(attrs={"class": "w-full border rounded px-3 py-2", "rows": 3}),
            "amount": forms.NumberInput(attrs={"class": "w-full border rounded px-3 py-2"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "w-full border rounded px-3 py-2"}),
            "session": forms.Select(attrs={"class": "w-full border rounded-lg px-3 py-2"}),
            "term": forms.Select(attrs={"class": "w-full border rounded-lg px-3 py-2"}),
        }




# finance/forms.py

class BulkInvoiceForm(forms.Form):
    school_class = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={"class": TAILWIND})
    )
    fee_template = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={"class": TAILWIND})
    )
    session = forms.ChoiceField(
        choices=[(s, s) for s in SESSION_LIST],
        widget=forms.Select(attrs={"class": TAILWIND})
    )
    term = forms.ChoiceField(
        choices=Score.TERM_CHOICES,
        widget=forms.Select(attrs={"class": TAILWIND})
    )

    def __init__(self, *args, **kwargs):
        school = kwargs.pop("school")
        super().__init__(*args, **kwargs)

        self.fields["school_class"].queryset = SchoolClass.objects.filter(school=school)
        self.fields["fee_template"].queryset = FeeTemplate.objects.filter(
            school=school,
            is_active=True
        )



from django import forms
from .models import FeeTemplate  # adjust imports



class FeeTemplateForm(forms.ModelForm):
    amount = forms.CharField(  # Use CharField to allow commas in input
        widget=forms.TextInput(attrs={
            "placeholder": "Enter amount",
            "class": "w-full px-3 py-2 border rounded-md dark:bg-gray-800 dark:text-white",
        })
    )

    class Meta:
        model = FeeTemplate
        fields = ["name", "amount", "school_class"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            school = getattr(user, "accountant_profile", None)
            if school:
                self.fields["school_class"].queryset = SchoolClass.objects.filter(school=school.school)
            else:
                self.fields["school_class"].queryset = SchoolClass.objects.none()
        else:
            self.fields["school_class"].queryset = SchoolClass.objects.none()

    def clean_amount(self):
        # Remove commas and convert to decimal
        amount = self.cleaned_data.get("amount", "")
        try:
            # Remove commas
            amount = amount.replace(",", "")
            return float(amount)
        except ValueError:
            raise forms.ValidationError("Enter a valid number.")




class FinanceReportForm(forms.Form):
    school_class = forms.ModelChoiceField(
        queryset=None, required=False,
        widget=forms.Select(attrs={"class": TAILWIND})
    )
    session = forms.ChoiceField(
        choices=[(s, s) for s in SESSION_LIST],
        widget=forms.Select(attrs={"class": TAILWIND})
    )
    term = forms.ChoiceField(
        choices=Score.TERM_CHOICES,
        widget=forms.Select(attrs={"class": TAILWIND})
    )

    def __init__(self, *args, **kwargs):
        school = kwargs.pop("school")
        super().__init__(*args, **kwargs)
        self.fields["school_class"].queryset = school.classes.all()
        

