from django.urls import path
from . import views

app_name = 'results'

urlpatterns = [
    path('student/<int:student_id>/', views.student_result, name='student_result'),
    path('bulk_score_entry/<int:school_id>/', views.bulk_score_entry, name='bulk_score_entry'),
    path('bulk_psycho_affective/<int:school_id>/', views.bulk_psycho_affective, name='bulk_psycho_affective'),
    path('termly_report/<int:student_id>/', views.generate_termly_report, name='termly_report'),
    path('cumulative_report/<int:student_id>/', views.generate_cumulative_report, name='cumulative_report'),
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('download_students_template/', views.download_students_template, name='download_students_template'),
    path('download_scores_template/', views.download_scores_template, name='download_scores_template'),
    path('bulk_student_upload/<int:school_id>', views.bulk_student_upload, name='bulk_student_upload'),
    path('bulk_score_upload/<int:school_id>', views.bulk_score_upload, name='bulk_score_upload'),

    path('grade-settings/<int:school_id>/', views.grade_settings, name='grade_settings'),
    path("grade-settings/<int:school_id>/overview/",views.grade_settings_overview,name="grade_settings_overview"),


    path('dashboard/<int:school_id>/', views.results_dashboard, name='results_dashboard'),
    path('export-excel/<int:school_id>/', views.export_results_excel, name='export_results_excel'),
    path('report/<int:student_id>/', views.report_card_view, name='report_card_view'),
    # direct download link (optional)
    path('report/<int:student_id>/download/', views.report_card_download, name='report_card_download'),
    # verification endpoint scanned by QR
    path('verify/<str:admission_no>/', views.verify_result, name='verify_result'),

    # teacher dashboard
    path('teacher/portal/', views.teacher_portal, name='teacher_portal'),
    # urls.py
    path('teacher/bulk-save/<int:school_id>/', views.bulk_save_all, name='bulk_save_all'),

    # student detail quick view (teacher)
    path('teacher/student/<int:student_id>/', views.teacher_student_detail, name='teacher_student_detail'),

    path('teacher/export/<int:subject_id>/pdf/', views.export_students_pdf, name='export_students_pdf'),
    path('teacher/export/<int:subject_id>/excel/', views.export_students_excel, name='export_students_excel'),
    path('teacher/export/<int:subject_id>/detailed_pdf/', views.export_students_detailed_pdf, name='export_students_detailed_pdf'),


    path('delete_score/<int:student_id>/<int:subject_id>/', views.delete_score, name='delete_score'),
    path('student/portal/', views.student_portal, name='student_portal'),
    path('student/result/<int:result_id>/', views.student_view_result, name='student_view_result'),
    path('student/result/<int:result_id>/download/', views.student_result_download, name='student_result_download'),
    

    # add these to urlpatterns where your other student URLs are
    path('student/cumulative/', views.student_cumulative_result, name='student_cumulative_result'),
    path('student/cumulative/download/', views.student_cumulative_result_download, name='student_cumulative_result_download'),

    path('school/<int:school_id>/class-score-settings/',views.class_score_settings, name='class_score_settings'),



]

    