# finance/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import School

User = settings.AUTH_USER_MODEL


class SchoolAccountant(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="accountant_profile"
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="accountants"
    )
    staff_id = models.CharField(max_length=30, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.school.name}"


from django.db import models
from django.conf import settings
from accounts.models import School
from results.utils import SESSION_LIST, SESSION_CHOICES
from results.models import Score
from students.models import SchoolClass

class SchoolTransaction(models.Model):
    school = models.ForeignKey(
        School, 
        on_delete=models.CASCADE, 
        related_name='transactions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPE_CHOICES)
    title = models.CharField(max_length=255,default='')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)

    # New fields for term and session
    session = models.CharField(max_length=150,default='', choices=[(s, s) for s in SESSION_LIST])
    term = models.CharField(max_length=10, default='', choices=Score.TERM_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.transaction_type}) - {self.amount}"


from students.models import Student
from django.conf import settings


class Invoice(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)

    title = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=20, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    session = models.CharField(max_length=150)
    term = models.CharField(max_length=10, choices=Score.TERM_CHOICES)
    due_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("student", "session", "term", "title")

    @property
    def outstanding(self):
        return self.total_amount - self.amount_paid

    @property
    def status(self):
        if self.amount_paid == 0:
            return "UNPAID"
        elif self.amount_paid < self.total_amount:
            return "PARTIAL"
        return "PAID"

    def save(self, *args, **kwargs):
        # Ensure invoice class always matches student class
        if not self.school_class:
            self.school_class = self.student.school_class
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.title} ({self.session} T{self.term})"
    


class PaystackTransaction(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="paystack_transactions",
        null=True,
    )
    invoice = models.ForeignKey(
        "Invoice",
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    paystack_reference = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Pending'),
            ('success', 'Success'),
            ('failed', 'Failed')
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),  # faster admin filtering
        ]

    def __str__(self):
        return f"{self.invoice} - ₦{self.amount} [{self.status}]"




class Payment(models.Model):
    PAYMENT_METHODS = (
        ("cash", "Cash"),
        ("bank", "Bank Transfer"),
        ("pos", "POS"),
        ("online", "Online"),
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="payments",
        db_index=True
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="payments",
        db_index=True
    )

    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )

    # Required for Paystack / Moniepoint / idempotency
    reference = models.CharField(
        max_length=100,
        unique=True,
        help_text="Gateway reference or internal transaction ID"
    )

    payment_date = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )

    # Manual payments only (null for Paystack)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_payments"
    )

    # 🔹 Optional audit metadata
    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text="Raw gateway metadata (Paystack, Moniepoint, etc.)"
    )

    class Meta:
        ordering = ["-payment_date"]
        indexes = [
            models.Index(fields=["reference"]),
            models.Index(fields=["school", "payment_method"]),
            models.Index(fields=["invoice", "payment_date"]),
        ]

    @property
    def paystack_receipt_url(self):
        """
        Returns Paystack receipt URL if this payment was made online
        and a successful Paystack transaction exists.
        """
        if self.payment_method != "online":
            return None

        tx = (
            self.invoice.transactions
            .filter(status="success")
            .order_by("-created_at")
            .first()
        )

        if tx and tx.paystack_reference:
            return f"https://dashboard.paystack.com/receipts/{tx.paystack_reference}"

        return None

    def __str__(self):
        return (
            f"{self.invoice.student} paid ₦{self.amount} "
            f"via {self.payment_method}"
        )





class Expense(models.Model):
    title = models.CharField(max_length=255, default='')
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    date = models.DateField()
    session = models.CharField(max_length=150, default='')
    term = models.CharField(max_length=10, default='', choices=Score.TERM_CHOICES)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='expenses')
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.title} - ₦{self.amount}"

    


class Receipt(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, default='')
    session = models.CharField(max_length=150, default='')
    term = models.CharField(max_length=10, default='', choices=Score.TERM_CHOICES)
    school = models.ForeignKey(School, on_delete=models.CASCADE)

    def __str__(self):
        return f"Receipt for {self.student} - {self.amount}"


class FeeTemplate(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="fee_templates")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, default='')
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("school", "school_class", "name")

    def __str__(self):
        return f"{self.name} - {self.school_class}"



class SchoolTermSetting(models.Model):
    TERM_CHOICES = [('1', 'Term 1'), ('2', 'Term 2'), ('3', 'Term 3')]

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="term_settings"
    )

    session = models.CharField(
        max_length=30,
        choices=SESSION_CHOICES
    )

    term = models.CharField(
        max_length=1,
        choices=TERM_CHOICES
    )

    next_term_begins = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('school', 'session', 'term')
        ordering = ['-created_at']

    
    def save(self, *args, **kwargs):
        if self.is_active:
            SchoolTermSetting.objects.filter(
                school=self.school,
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.school.name} - {self.session} Term {self.term}" 


