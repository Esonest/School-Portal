from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify

from accounts.models import School
from .models import SchoolWebsite


@receiver(post_save, sender=School)
def create_school_website(sender, instance, created, **kwargs):

    if created:

        SchoolWebsite.objects.get_or_create(
            school=instance,
            defaults={
                "slug": slugify(instance.name),
                "motto": "",
                "vision": "",
                "mission": "",
                "history": "",
                "principal_name": "",
                "principal_message": "",
            },
        )