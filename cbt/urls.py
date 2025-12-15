from django.urls import path
from . import views

app_name = "cbt"

urlpatterns = [
    path("", views.exam_list, name="exam_list"),
    path("exam/<int:exam_id>/start/", views.start_exam_page, name="start_exam_page"),  # ⚠ warning page
    path("exam/<int:exam_id>/begin/", views.start_exam, name="start_exam"),            # actual start after warning
    path("exam/<int:exam_id>/question/<int:question_index>/", views.take_exam, name="take_exam"),
    path("exam/<int:exam_id>/submit/", views.submit_exam, name="submit_exam"),
    path('ajax/save_answer/', views.ajax_save_answer, name='ajax_save_answer'),
    path("exam/<int:exam_id>/result/", views.student_exam_result, name="student_exam_result"),

]
