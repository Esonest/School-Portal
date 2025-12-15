from django.urls import path
from . import views

app_name = 'assignments'
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    # teacher routes
    path('create/', views.create_assignment, name='create_assignment'),
    path('teacher/assignment/<int:pk>/edit/', views.create_assignment, name='edit_assignment'),
    path('teacher/assignment/<int:pk>/', views.teacher_assignment_detail, name='teacher_assignment_detail'),
    path('teacher/grade/<int:submission_id>/', views.grade_submission, name='grade_submission'),
    path('teacher/assignment/<int:pk>/delete/', views.delete_assignment, name='delete_assignment'),


    # student routes
    path('assignment/<int:pk>/', views.student_assignment_detail, name='student_assignment_detail'),
    path('assignment/<int:pk>/submit/', views.submit_assignment, name='submit_assignment'),
    # submissions
    path('submissions/', views.submission_list, name='submission_list'),
    path('submissions/<int:assignment_id>/', views.submission_list, name='submission_list_for_assignment'),
    path('file/<int:file_id>/download/', views.download_submission_file, name='download_submission_file'),
]
