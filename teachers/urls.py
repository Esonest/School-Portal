from django.urls import path
from . import views

app_name = 'teachers'
urlpatterns = [
    
    path('classes/', views.classes_list, name='classes'),
    path('class/<slug:class_slug>/', views.class_students, name='class_students'),
    path('exam/<int:exam_id>/scores/', views.enter_scores, name='enter_scores'),
    path('exam/<int:exam_id>/scores/<slug:class_slug>/', views.enter_scores, name='enter_scores_by_class'),
    path('exam/<int:exam_id>/affective/', views.enter_affective, name='enter_affective'),
    path('exam/<int:exam_id>/psychomotor/', views.enter_psychomotor, name='enter_psychomotor'),
    path('assignments/create/', views.create_assignment, name='create_assignment'),
    path('assignments/', views.assignments_list, name='assignments'),
    path('notes/upload/', views.upload_note, name='upload_note'),
    path('cbt/', views.manage_cbt, name='manage_cbt'),
     path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('results/', views.teacher_result_dashboard, name='teacher_result_dashboard'),
]