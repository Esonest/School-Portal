# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SchoolCommunicationSetting
from accounts.models import School

@receiver(post_save, sender=School)
def create_school_comm_settings(sender, instance, created, **kwargs):
    if created:
        SchoolCommunicationSetting.objects.create(
            school=instance
        )