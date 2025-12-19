from django.core.management.base import BaseCommand
from students.models import Student
from accounts.models import School
from django.core.files import File
import os

class Command(BaseCommand):
    help = "Upload existing local media files to Cloudinary"

    def handle(self, *args, **kwargs):
        migrated = 0

        for student in Student.objects.exclude(photo=""):
            if student.photo and student.photo.name.startswith("student_photos/"):
                local_path = student.photo.path
                if os.path.exists(local_path):
                    with open(local_path, "rb") as f:
                        student.photo.save(
                            os.path.basename(local_path),
                            File(f),
                            save=True
                        )
                        migrated += 1

        for school in School.objects.exclude(principal_signature=""):
            if school.principal_signature:
                local_path = school.principal_signature.path
                if os.path.exists(local_path):
                    with open(local_path, "rb") as f:
                        school.principal_signature.save(
                            os.path.basename(local_path),
                            File(f),
                            save=True
                        )
                        migrated += 1

        self.stdout.write(self.style.SUCCESS(f"Migrated {migrated} files to Cloudinary"))
