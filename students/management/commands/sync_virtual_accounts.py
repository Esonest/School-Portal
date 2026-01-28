from django.core.management.base import BaseCommand
from students.models import Student
from finance.utils import create_virtual_account

class Command(BaseCommand):
    help = "Ensure all students have a dedicated Paystack virtual account."

    def handle(self, *args, **options):
        students = Student.objects.all()
        total = students.count()
        self.stdout.write(f"Checking {total} students for virtual accounts...")

        created_count = 0

        for student in students:
            try:
                if not student.virtual_account_number:
                    create_virtual_account(student)
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"Created VA for {student.user.get_full_name() or student.user.username} ({student.id})"
                    ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Failed for {student.user.username} ({student.id}): {e}"
                ))

        self.stdout.write(self.style.SUCCESS(
            f"Done! Created {created_count} virtual accounts."
        ))
