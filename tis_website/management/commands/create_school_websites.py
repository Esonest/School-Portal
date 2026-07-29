from django.core.management.base import BaseCommand
from django.utils.text import slugify

from accounts.models import School
from tis_website.models import SchoolWebsite


class Command(BaseCommand):
    help = "Create website profiles for existing schools"


    def handle(self, *args, **kwargs):

        created = 0

        for school in School.objects.all():

            website, was_created = SchoolWebsite.objects.get_or_create(
                school=school,
                defaults={
                    "slug": slugify(school.name),
                    "motto": "",
                    "vision": "",
                    "mission": "",
                    "history": "",
                    "principal_name": "",
                    "principal_message": "",
                },
            )

            if was_created:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{created} website profile(s) created."
            )
        )