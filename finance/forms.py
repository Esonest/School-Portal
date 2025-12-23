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
    class Meta:
        model = Invoice
        fields = ["school_class", "student", "title", "total_amount", "due_date", "session", "term"]
        widgets = {
            "title": forms.TextInput(attrs={"class": TAILWIND}),
            "total_amount": forms.NumberInput(attrs={"class": TAILWIND}),
            "due_date": forms.DateInput(attrs={"class": TAILWIND, "type": "date"}),
            "session": forms.Select(choices=[(s, s) for s in SESSION_LIST], attrs={"class": TAILWIND}),
            "term": forms.Select(choices=Score.TERM_CHOICES, attrs={"class": TAILWIND}),
        }

    def __init__(self, *args, **kwargs):
        school = kwargs.pop("school", None)
        super().__init__(*args, **kwargs)
        if school:
            # Only show classes from this school
            self.fields["school_class"].queryset = SchoolClass.objects.filter(school=school)
            # Initially show all students from the school
            self.fields["student"].queryset = Student.objects.filter(school=school)




class PaymentForm(forms.ModelForm):
    # Used ONLY for filtering invoices, not saved on Payment
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
            # Limit classes and invoices to the user's school
            self.fields["school_class"].queryset = SchoolClass.objects.filter(
                school=school
            )
            self.fields["invoice"].queryset = Invoice.objects.filter(
                school=school
            )

        # Dynamically filter invoices by selected class
        if self.data.get("school_class"):
            try:
                class_id = int(self.data.get("school_class"))
                self.fields["invoice"].queryset = Invoice.objects.filter(
                    school_class_id=class_id
                )
            except (ValueError, TypeError):
                pass



class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["title", "amount", "school_class", "session", "term"]
        widgets = {
            "session": forms.Select(choices=[(s, s) for s in SESSION_LIST], attrs={"class": TAILWIND}),
            "term": forms.Select(choices=Score.TERM_CHOICES, attrs={"class": TAILWIND}),
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
    class Meta:
        model = FeeTemplate
        fields = ["name", "amount", "school_class"]  # adjust fields

    def __init__(self, *args, **kwargs):
        # Pop the user from kwargs; don't pass it to super()
        user = kwargs.pop("user", None)
        super(FeeTemplateForm, self).__init__(*args, **kwargs)
        
        if user:
            # Determine the school from the user's accountant profile
            school = getattr(user, "accountant_profile", None)
            if school:
                self.fields["school_class"].queryset = SchoolClass.objects.filter(school=school.school)
            else:
                self.fields["school_class"].queryset = SchoolClass.objects.none()
        else:
            self.fields["school_class"].queryset = SchoolClass.objects.none()



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
        

