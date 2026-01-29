
from django.db import migrations


def forwards(apps, schema_editor):
    Student = apps.get_model("students", "Student")
    VirtualAccount = apps.get_model("students", "VirtualAccount")

    for student in Student.objects.all():
        va_number = getattr(student, "virtual_account_number", None)

        if not va_number:
            continue

        VirtualAccount.objects.get_or_create(
            student=student,
            account_number=va_number,
            defaults={
                "account_name": getattr(student, "virtual_account_name", ""),
                "bank_name": getattr(student, "virtual_bank_name", ""),
                "bank_slug": getattr(student, "virtual_bank_slug", ""),
                "is_primary": True,
                "verified_at": getattr(student, "va_verified_at", None),
            }
        )



def backwards(apps, schema_editor):
    VirtualAccount = apps.get_model("students", "VirtualAccount")
    VirtualAccount.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("students", '0006_remove_student_va_verified_at_and_more'),  
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
