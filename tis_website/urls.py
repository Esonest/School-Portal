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

]