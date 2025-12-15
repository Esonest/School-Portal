from django.urls import path
from . import views

app_name = 'students'
urlpatterns = [
    path('', views.student_dashboard, name='student_dashboard'),
    path('<int:school_id>/', views.student_dashboard, name='student_dashboard_admin'),
    path('profile/', views.profile_view, name='profile'),
    path('result/<int:pk>/', views.result_detail, name='result_detail'),
    path('result/<int:pk>/pdf/', views.download_pdf, name='result_pdf'),
    path('cumulative/<str:session>/', views.cumulative_view, name='cumulative'),
    path('assignments/', views.assignments_list, name='assignments'),
    path('attendance/', views.attendance_report, name='attendance'),
    path('cbt/', views.cbt_list, name='cbt_list'),
    path('results/', views.student_result_dashboard, name='student_result_dashboard'),
    path('notes/', views.notes_list, name='notes_list'),
    path('notes/<int:pk>/', views.note_detail, name='note_detail'),


    
]









