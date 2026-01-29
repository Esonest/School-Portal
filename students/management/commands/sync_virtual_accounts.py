# students/management/commands/sync_virtual_accounts.py
from django.core.management.base import BaseCommand
from django.utils import timezone
import requests
from students.models import Student, VirtualAccount


PAYSTACK_BASE_URL = "https://api.paystack.co"
DEFAULT_EMAIL = "techcenter652@gmail.com"
DEFAULT_PHONE = "07085734441"
PREFERRED_BANK = "paystack-titan"  # your preferred bank for new VA creation


class Command(BaseCommand):
    help = "Sync all students' virtual accounts from Paystack"

    def handle(self, *args, **options):
        students = Student.objects.all()
        self.stdout.write(f"Checking {students.count()} students for virtual accounts...")

        for student in students:
            try:
                self.sync_student_vas(student)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed for {student.admission_no}: {e}"))

        self.stdout.write(self.style.SUCCESS("Virtual account sync complete."))

    def sync_student_vas(self, student: Student):
        now = timezone.now()
        headers = {
            "Authorization": f"Bearer {student.school.paystack_secret_key}",
            "Content-Type": "application/json",
        }

        # Ensure student has a Paystack customer
        if not student.paystack_customer_code:
            customer_payload = {
                "email": student.user.email or DEFAULT_EMAIL,
                "phone": getattr(student.user, "phone", DEFAULT_PHONE),
                "first_name": student.user.first_name or student.user.username,
                "last_name": student.user.last_name or student.admission_no,
            }
            resp = requests.post(f"{PAYSTACK_BASE_URL}/customer", json=customer_payload, headers=headers, timeout=30)
            data = resp.json()
            if not resp.ok or not data.get("status"):
                raise Exception(f"Paystack customer creation failed: {data.get('message')}")
            student.paystack_customer_code = data["data"]["customer_code"]
            student.save(update_fields=["paystack_customer_code"])

        # Fetch all dedicated accounts for this customer
        resp = requests.get(f"{PAYSTACK_BASE_URL}/dedicated_account", headers=headers, params={"customer": student.paystack_customer_code}, timeout=30)
        data = resp.json()
        vas = data.get("data", [])

        if not vas:
            self.stdout.write(self.style.WARNING(f"No VAs found for {student.admission_no}"))
            return

        for va in vas:
            bank = va.get("bank") or {}
            bank_name = bank.get("name") or "Unknown Bank"
            bank_slug = bank.get("slug") or "unknown-bank"

            # Avoid duplicate account numbers
            obj, created = VirtualAccount.objects.get_or_create(
                account_number=va["account_number"],
                defaults={
                    "student": student,
                    "account_name": va.get("account_name") or "Unknown Account",
                    "bank_name": bank_name,
                    "bank_slug": bank_slug,
                    "is_primary": va.get("is_primary", False),
                    "verified_at": now,
                }
            )

            # Update existing VA fields if changed
            updated = False
            fields_to_check = ["account_name", "bank_name", "bank_slug", "is_primary"]
            for field in fields_to_check:
                new_value = None
                if field == "bank_name":
                    new_value = bank_name
                elif field == "bank_slug":
                    new_value = bank_slug
                elif field == "is_primary":
                    new_value = va.get("is_primary", False)
                else:
                    new_value = va.get(field) or getattr(obj, field)

                if getattr(obj, field) != new_value:
                    setattr(obj, field, new_value)
                    updated = True

            if updated:
                obj.verified_at = now
                obj.save(update_fields=fields_to_check + ["verified_at"])

        self.stdout.write(self.style.SUCCESS(f"{student.admission_no} synced {len(vas)} VA(s)"))
