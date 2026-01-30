from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Teacher
from .utils import sync_class_subject_teacher


# Runs when teacher.classes OR teacher.subjects are updated
@receiver(m2m_changed, sender=Teacher.classes.through)
@receiver(m2m_changed, sender=Teacher.subjects.through)
def update_class_subject_teacher(sender, instance, action, **kwargs):
    if action not in ("post_add", "post_remove", "post_clear"):
        return

    teacher = instance
    sync_class_subject_teacher(teacher)


# students/signals.py
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from finance.utils import ensure_virtual_accounts
from .models import Student


@receiver(post_save, sender=Student)
def create_student_virtual_accounts(sender, instance, created, **kwargs):
    if not created:
        return

    # 🚨 Paystack must run AFTER DB commit
    transaction.on_commit(
        lambda: safe_ensure_virtual_accounts(instance.id)
    )


def safe_ensure_virtual_accounts(student_id):
    from students.models import Student

    try:
        student = Student.objects.get(id=student_id)
        ensure_virtual_accounts(student)
    except Exception as e:
        print(f"[VA ERROR] Student {student_id}: {e}")
