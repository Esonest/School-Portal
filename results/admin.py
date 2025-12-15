from django.contrib import admin
from .models import Student, Subject, Score, Psychomotor, Affective
from accounts.models import School, Teacher

admin.site.register(School)

admin.site.register(Subject)
admin.site.register(Score)
admin.site.register(Psychomotor)
admin.site.register(Affective)
