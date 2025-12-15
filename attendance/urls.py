from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('mark/<int:class_id>/', views.mark_attendance, name='mark_attendance'),
    path('report/', views.attendance_report, name='attendance_report'),
    path('report/<int:class_id>/', views.class_attendance_detail, name='class_attendance_detail'),
]
