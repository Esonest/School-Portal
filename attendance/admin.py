from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student','date','status','marked_by')
    list_filter = ('status','date','marked_by')
    search_fields = ('student__admission_no','student__user__username')
