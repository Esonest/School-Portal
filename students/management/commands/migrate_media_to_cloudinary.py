from django.core.management.base import BaseCommand
from students.models import Student
from accounts.models import School
from django.core.files import File
import os

class Command(BaseCommand):
    help = "Migrate local media files to Cloudinary safely"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting media migration..."))

        # -------------------------
        # STUDENT PHOTOS
        # -------------------------
        for student in Student.objects.exclude(photo=""):
            field = student.photo

            # Skip already-migrated files
            if field.url.startswith("http"):
                continue

            local_path = field.path

            if not os.path.exists(local_path):
                self.stdout.write(
                    self.style.WARNING(f"Missing file: {local_path}")
                )
                continue

            with open(local_path, "rb") as f:
                field.save(
                    os.path.basename(local_path),
                    File(f),
                    save=True
                )

            self.stdout.write(
                self.style.SUCCESS(f"Migrated student photo: {student}")
            )

        # -------------------------
        # PRINCIPAL SIGNATURES
        # -------------------------
        for school in School.objects.exclude(principal_signature=""):
            field = school.principal_signature

            if field.url.startswith("http"):
                continue

            local_path = field.path

            if not os.path.exists(local_path):
                self.stdout.write(
                    self.style.WARNING(f"Missing file: {local_path}")
                )
                continue

            with open(local_path, "rb") as f:
                field.save(
                    os.path.basename(local_path),
                    File(f),
                    save=True
                )

            self.stdout.write(
                self.style.SUCCESS(f"Migrated signature for: {school.name}")
            )

        self.stdout.write(self.style.SUCCESS("✅ Media migration completed"))
