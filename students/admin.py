# students/admin.py
from django.contrib import admin
from .models import Student, SchoolClass


admin.site.register(Student)
admin.site.register(SchoolClass)