from django.urls import path
from . import views

app_name = 'notes'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('upload/', views.teacher_upload_note, name='upload_note'),
    path('edit/<int:pk>/', views.teacher_upload_note, name='edit_note'),
    path('delete/<int:pk>/', views.teacher_delete_note, name='delete_note'),
    path(
        "approve/<int:pk>/",
        views.approve_note,
        name="approve_note"
    ),

    path(
        "reject/<int:pk>/",
        views.reject_note,
        name="reject_note"
    ),

    path(
        "toggle-active/<int:pk>/",
        views.toggle_note_active,
        name="toggle_note_active"
    ),

    path('list/', views.student_notes_list, name='student_list'),

    path('<int:pk>/', views.note_detail, name='note_detail'),
    path('<int:pk>/download/', views.download_note_file, name='download_note_file'),
]
