from django.urls import path
from . import views


app_name = "tis_website"



urlpatterns = [

    path(
        "<slug:school_slug>/",
        views.home,
        name="home"
    ),


    path(
        "<slug:school_slug>/about/",
        views.about,
        name="about"
    ),


    path(
        "<slug:school_slug>/academics/",
        views.academics,
        name="academics"
    ),


    path(
        "<slug:school_slug>/admissions/",
        views.admissions,
        name="admissions"
    ),


    path(
        "<slug:school_slug>/contact/",
        views.contact,
        name="contact"
    ),

    path(

        "admission/exam/<uuid:token>/",

        views.admission_exam_access,

        name="admission_exam_access"

    ),



    path(
        "admission/portal/<uuid:token>/",
        views.parent_admission_portal,
        name="parent_admission_portal"
    ),

    path(
        "admission/download-letter/<uuid:token>/",
        views.download_admission_letter,
        name="download_admission_letter"
    ),

    path(
        "admission/accept/<uuid:token>/",
        views.accept_admission,
        name="accept_admission"
    ),

    path(
        "admission/success/<uuid:token>/",
        views.acceptance_success,
        name="acceptance_success"
    ),

    path(
        "admission/payment/<uuid:token>/",
        views.admission_payment,
        name="admission_payment"

    ),

    path(
        "student-login-details/<uuid:token>/",
        views.student_login_details,
        name="student_login_details"
    ),


]