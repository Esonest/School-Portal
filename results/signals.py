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
