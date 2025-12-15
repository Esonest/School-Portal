from django.urls import path
from . import views

app_name = "superadmin"

urlpatterns = [
    path("dashboard/", views.super_admin_dashboard, name="dashboard"),
    path("schools/", views.school_list, name="school_list"),
    path("schools/create/", views.school_create, name="school_create"),
    path("schools/<int:pk>/edit/", views.school_edit, name="school_edit"),
    path("schools/<int:pk>/delete/", views.school_delete, name="school_delete"),

    path("admins/", views.admin_list, name="admin_list"),
    path("admins/create/", views.admin_create, name="admin_create"),
    path("admins/<int:pk>/edit/", views.admin_edit, name="admin_edit"),
    path("admins/<int:pk>/delete/", views.admin_delete, name="admin_delete"),

    path("teachers/", views.teacher_list, name="teacher_list"),


    path("students/", views.student_list, name="student_list"),
    path("students/create/", views.create_student, name="create_student"),
    path("students/<int:student_id>/edit/", views.edit_student, name="edit_student"),
    path("students/<int:student_id>/delete/",views.delete_student, name="delete_student"),  # if you want delete
    path("students/bulk-upload/", views.bulk_upload_students, name="student_bulk_upload"),
    path("students/<int:student_id>/", views.student_profile, name="student_profile"),

    path("teachers/", views.teacher_list, name="teacher_list"),
    path("teachers/create/",views.teacher_create, name="teacher_create"),
    path("teachers/<int:teacher_id>/edit/", views.teacher_edit, name="teacher_edit"),
    path("teachers/<int:teacher_id>/delete/", views.teacher_delete, name="teacher_delete"),



    path("teachers/advanced/", views.teacher_list_advanced, name="teacher_list_advanced"),
    path("teachers/export/", views.export_teachers_excel, name="teacher_export"),
    path("teachers/import/", views.teacher_import, name="teacher_import"),


    # ---------- SCHOOL CLASS CRUD -----------
    path("classes/", views.class_list, name="class_list"),
    path("classes/create/", views.class_create, name="class_create"),
    path("classes/<int:class_id>/edit/", views.class_edit, name="class_edit"),
    path("classes/<int:class_id>/delete/", views.class_delete, name="class_delete"),

    # ---------- SUBJECT CRUD -----------
    path("subjects/", views.subject_list, name="subject_list"),
    path("subjects/create/", views.subject_create, name="subject_create"),
    path("subjects/<int:subject_id>/edit/", views.subject_edit, name="subject_edit"),
    path("subjects/<int:subject_id>/delete/", views.subject_delete, name="subject_delete"),


    path("", views.user_list, name="user_list"),
    path("create/", views.user_create, name="user_create"),
    path("<int:user_id>/edit/", views.user_update, name="user_update"),
    path("<int:user_id>/delete/", views.user_delete, name="user_delete"),
    path("<int:user_id>/", views.user_detail, name="user_detail"),


    path("super-admin/portals/",views.school_portal_setting_list, name="superadmin_portal_list"),
    path("super-admin/portals/<int:school_id>/edit/",views.school_portal_setting_update,name="superadmin_portal_update"),

]
