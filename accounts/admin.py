from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Teacher, SchoolAdmin
from results.models import ClassSubjectTeacher
from finance.models import SchoolAccountant
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Columns in the list view
    list_display = ('username', 'get_full_name', 'email', 'role', 'school', 'is_staff', 'is_active')

    # Add role and school to the edit form
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('role', 'school')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'school')}),
    )

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'


@admin.register(ClassSubjectTeacher)
class ClassSubjectTeacherAdmin(admin.ModelAdmin):
    list_display = ("school_class", "subject", "teacher")
    list_filter = ("school_class", "subject")



# Register Teacher model
admin.site.register(Teacher)
admin.site.register(SchoolAdmin)
admin.site.register(SchoolAccountant)

