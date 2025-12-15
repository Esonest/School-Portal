from django.contrib import admin
from .models import Assignment, AssignmentSubmission, SubmissionFile

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title','subject','teacher','due_date','published','created_on')
    list_filter = ('published','subject','created_on')
    search_fields = ('title','description','teacher__username')

@admin.register(AssignmentSubmission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment','student','submitted_on','status','score','graded_on')
    list_filter = ('status','graded_on')
    search_fields = ('student__admission_no','assignment__title')

@admin.register(SubmissionFile)
class SubmissionFileAdmin(admin.ModelAdmin):
    list_display = ('submission','file','uploaded_on')
