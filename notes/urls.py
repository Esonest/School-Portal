from django.urls import path
from . import views

app_name = 'notes'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Notes creation/edit/delete
    path('upload/', views.teacher_upload_note, name='upload_note'),
    path('upload/<int:pk>/', views.teacher_upload_note, name='upload_note'),
    path('delete/<int:pk>/', views.teacher_delete_note, name='delete_note'),
    path('edit/<int:pk>/', views.teacher_upload_note, name='edit_note'),
    # Notes list (smart)
    path('list/', views.student_notes_list, name='student_list'),

    # Note details & download
    path('<int:pk>/', views.note_detail, name='note_detail'),
    path('<int:pk>/download/', views.download_note_file, name='download_note_file'),
]
