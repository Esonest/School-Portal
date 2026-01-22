
from django.urls import path
from . import views

app_name = 'school_admin'
urlpatterns = [
    path('super_admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('school_admin/<int:school_id>/', views.school_admin_dashboard, name='school_admin_dashboard'),


    path("<int:school_id>/", views.student_list, name="admin_student_list"),
    path("<int:school_id>/create/", views.student_create, name="admin_student_create"),
    path("<int:school_id>/edit/<int:student_id>/", views.student_edit, name="admin_student_edit"),
    path("<int:school_id>/delete/<int:student_id>/", views.student_delete, name="admin_student_delete"),


     # Admin
    path('admin/<int:school_id>/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/<int:school_id>/exam/create/', views.exam_create, name='exam_create'),
    path( "admin/<int:school_id>/exam/<int:exam_id>/preview/", views.exam_preview,name="exam_preview"),

    path('admin/<int:school_id>/exam/<int:exam_id>/edit/', views.exam_edit, name='exam_edit'),
    path('admin/<int:school_id>/exam/<int:exam_id>/delete/', views.exam_delete, name='exam_delete'),
    path('admin/<int:school_id>/exam/<int:exam_id>/toggle/', views.exam_toggle_active, name='exam_toggle'),
    

    path("school_admin/admin/<int:school_id>/exam/<int:exam_id>/preview/",views.preview_questions,name="preview_questions"),

    path( "admin/<int:school_id>/exam/<int:exam_id>/questions/",views.question_list, name="question_list"),
    # ➤ Bulk-add up to 50 questions
    path("admin/<int:school_id>/exam/<int:exam_id>/questions/bulk-add/",views.bulk_question_admin,name="bulk_question_admin"),

    path('admin/<int:school_id>/exam/<int:exam_id>/questions/', views.manage_questions, name='manage_questions'),
    path('admin/<int:school_id>/exam/<int:exam_id>/questions/add/', views.question_create, name='question_create'),
    path('admin/<int:school_id>/exam/<int:exam_id>/questions/<int:question_id>/edit/', views.question_edit, name='question_edit'),
    path('admin/<int:school_id>/exam/<int:exam_id>/questions/<int:question_id>/delete/', views.question_delete, name='question_delete'),

    # Student-facing routes (below)
    path('take/<int:exam_id>/', views.start_exam, name='start_exam'),
    path('take/<int:exam_id>/q/<int:page>/', views.exam_question_page, name='exam_page'),
    path('take/<int:exam_id>/submit/', views.submit_exam, name='submit_exam'),
    path('results/<int:exam_id>/', views.view_result, name='view_result'),

    path("admin/<int:school_id>/exam/<int:exam_id>/submissions/",views.submissions_list,name="submissions_list"),
    path('admin/<int:school_id>/exam/<int:exam_id>/submission/<int:submission_id>/',views.submission_detail, name='submission_detail'),

    # CBT Admin URLs

    path("admin/<int:school_id>/exam/<int:exam_id>/activate/", views.activate_exam, name="activate_exam"),
    path("admin/<int:school_id>/exam/<int:exam_id>/deactivate/", views.deactivate_exam, name="deactivate_exam"),
    path("admin/<int:school_id>/exam/<int:exam_id>/delete/", views.delete_exam, name="delete_exam"),

    # Result Dashboard
    path('admin/<int:school_id>/results/', views.result_dashboard, name='result_dashboard'),

    # Scores CRUD
    path('admin/<int:school_id>/scores/', views.score_list, name='score_list'),
    path('admin/<int:school_id>/score/create/', views.score_create_edit, name='score_create'),
    path('admin/<int:school_id>/score/<int:score_id>/edit/', views.score_create_edit, name='score_edit'),
    path('admin/score/<int:score_id>/delete/', views.score_delete, name='score_delete'),

    # Psychomotor CRUD
    path('admin/<int:school_id>/psychomotors/', views.psychomotor_list, name='psychomotor_list'),
    path('admin/<int:school_id>/psychomotor/create/', views.psychomotor_create_edit, name='psychomotor_create'),
    path('admin/<int:school_id>/psychomotor/<int:record_id>/edit/', views.psychomotor_create_edit, name='psychomotor_edit'),
    path('admin/psychomotor/<int:record_id>/delete/', views.psychomotor_delete, name='psychomotor_delete'),

    # Affective CRUD
    path('admin/<int:school_id>/affectives/', views.affective_list, name='affective_list'),
    path('admin/<int:school_id>/affective/create/', views.affective_create_edit, name='affective_create'),
    path('admin/<int:school_id>/affective/<int:record_id>/edit/', views.affective_create_edit, name='affective_edit'),
    path('admin/affective/<int:record_id>/delete/', views.affective_delete, name='affective_delete'),


     # Result Comments
    path('admin/<int:school_id>/result_comments/', views.result_comment_list, name='result_comment_list'),
    path('admin/<int:school_id>/result_comment/<int:comment_id>/edit/', views.result_comment_create_edit, name='result_comment_edit'),
    path('admin/result_comment/<int:comment_id>/delete/', views.result_comment_delete, name='result_comment_delete'),

    # School Admin Lesson Notes CRUD
    path('lesson-notes/', views.lessonnote_list, name='lessonnote_list'),
    path('lesson-notes/add/', views.lessonnote_create_edit, name='lessonnote_add'),
    path('lesson-notes/<int:pk>/edit/', views.lessonnote_create_edit, name='lessonnote_edit'),
    path('lesson-notes/<int:pk>/delete/', views.lessonnote_delete, name='lessonnote_delete'),
    path('lesson-notes/dashboard/<int:school_id>/', views.lesson_dashboard, name='lessonnote_dashboard'),
    

    #aasignment
    path('assignments/dashboard/<int:school_id>/', views.assignment_dashboard, name='assignment_dashboard'),
    path('assignments/<int:school_id>/', views.assignment_list, name='assignment_list'),
    path('assignments/<int:school_id>/create/', views.assignment_create_edit, name='assignment_create'),
    path('assignments/<int:school_id>/<int:pk>/edit/', views.assignment_create_edit, name='assignment_edit'),
    path('assignments/<int:school_id>/<int:pk>/delete/', views.assignment_delete, name='assignment_delete'),
    path('assignments/<int:school_id>/<int:pk>/submissions/', views.assignment_submissions, name='assignment_submissions'),

    # Attendance
    path("<int:school_id>/attendance/", views.attendance_list, name="admin_attendance_list"),
    path("<int:school_id>/attendance/add/", views.attendance_create, name="admin_attendance_create"), 
    path("<int:school_id>/attendance/<int:record_id>/edit/", views.attendance_edit, name="admin_attendance_edit"), 
    path("<int:school_id>/attendance/<int:record_id>/delete/", views.attendance_delete, name="admin_attendance_delete"),

    # Teacher 
    path('<int:school_id>/teachers/', views.teacher_list, name='teacher_list'),
    path('<int:school_id>/teachers/create/', views.teacher_create, name='teacher_create'),
    path('<int:school_id>/teachers/<int:teacher_id>/edit/', views.teacher_edit, name='teacher_edit'), 
    path('<int:school_id>/teachers/<int:teacher_id>/delete/', views.teacher_delete, name='teacher_delete'),
    

    path('school/<int:school_id>/block-unblock-students/', views.block_unblock_students,name='block_unblock_students'),



    path("classes/", views.admin_class_list, name="admin-class-list"),
    path("classes/<int:class_id>/students/", views.admin_class_students, name="admin-class-students"),
    path('students/<int:student_id>/results/', views.admin_student_results,name='admin-student-results'),
    path("score/<int:score_id>/edit/", views.admin_edit_score, name="admin-edit-score"),
    path('student/<int:student_id>/cumulative/', views.admin_student_cumulative, name='admin-student-cumulative'),
    path('classes/<int:class_id>/cumulative/', views.admin_class_cumulative, name='admin-class-cumulative'),
    path("promote/class/<int:class_id>/", views.promote_students, name="promote_students"),
    path("repeat/student/<int:student_id>/", views.repeat_student, name="repeat_student"),


    path("school/<int:school_id>/class-subject-teachers/",views.class_subject_teacher_list, name="class_subject_teacher_list"),
    path("school/<int:school_id>/class-subject-teachers/create/",views.class_subject_teacher_create,name="class_subject_teacher_create"),
    path("school/<int:school_id>/class-subject-teachers/<int:pk>/edit/",views.class_subject_teacher_update,name="class_subject_teacher_update"),
    path("school/<int:school_id>/class-subject-teachers/<int:pk>/delete/",views.class_subject_teacher_delete,name="class_subject_teacher_delete"),

    path("accountants/<int:school_id>/", views.accountant_list, name="accountant_list"),
    path("accountants/<int:school_id>/create/", views.accountant_create, name="accountant_create"),
    path("accountants/<int:pk>/edit/", views.accountant_update, name="accountant_update"),
    path("accountants/<int:pk>/toggle/", views.accountant_toggle_status, name="accountant_toggle"),


   
    path("", views.question_bank_list, name="question_bank_list"),
    path("add/", views.question_bank_create, name="question_bank_create"),
    path('<int:pk>/edit/', views.question_bank_update, name='question_bank_update'),
    path("<int:question_id>/delete/", views.question_bank_delete, name="question_bank_delete"),
    # Import questions into exam
    path("import/<int:exam_id>/",views.import_questions_to_exam,name="import_questions_to_exam"),


    path("school-admin/term-settings/",views.school_term_settings,name="school_term_settings"),


]



   

     



