from django.contrib import admin
from .models import NoteCategory, LessonNote

@admin.register(NoteCategory)
class NoteCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', )

@admin.register(LessonNote)
class LessonNoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'teacher', 'visibility', 'publish_date')
    list_filter = ('visibility', 'subject', 'publish_date', 'classes')
    search_fields = ('title', 'content', 'teacher__username')
