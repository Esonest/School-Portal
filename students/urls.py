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
    path( "announcements/",views.announcement_list,name="announcement_list"),
    path("announcements/create/",views.announcement_create,name="announcement_create"),
    path("announcements/<int:pk>/edit/",views.announcement_update,name="announcement_update"),
    path("announcements/<int:pk>/delete/",views.announcement_delete,name="announcement_delete"),
    path("ajax/load-students/",views.load_students_by_class,name="load_students_by_class"),

    path("verify/<uuid:student_uuid>/",views.student_verify,name="student_verify"),
    path("<int:school_id>/<int:student_id>/id-card/",views.student_id_card,name="student_id_card"),
    path("<int:school_id>/class/<int:class_id>/id-cards/",views.class_id_cards,name="class_id_cards"),

    
    path("webhooks/whatsapp/", views.whatsapp_webhook,name="whatsapp_webhook"),


]









