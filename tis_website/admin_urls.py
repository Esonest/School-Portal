from django.urls import path
from . import admin_views


app_name = "tis_website_admin"



urlpatterns = [

    path(
        "",
        admin_views.website_dashboard,
        name="dashboard"
    ),


    path(
        "profile/",
        admin_views.website_profile,
        name="profile"
    ),

    path(
        "homepage/",
        admin_views.homepage_settings,
        name="homepage"
    ),



    path("news/",admin_views.news_list,name="news_list"),



    path(

        "news/create/",

        admin_views.news_create,

        name="news_create"

    ),



    path("news/<int:pk>/edit/",admin_views.news_update, name="news_update"),



    path(

        "news/<int:pk>/delete/",

        admin_views.news_delete,

        name="news_delete"

    ),

    path(
        "gallery/",
        admin_views.gallery_list,
        name="gallery_list"
    ),


    path(
        "gallery/create/",
        admin_views.gallery_create,
        name="gallery_create"
    ),


    path(
        "gallery/<int:pk>/edit/",
        admin_views.gallery_update,
        name="gallery_update"
    ),


    path(
        "gallery/<int:pk>/delete/",
        admin_views.gallery_delete,
        name="gallery_delete"
    ),


    path(

        "admissions/",

        admin_views.admission_list,

        name="admission_list"

    ),

    path(
    
            "admissions/<int:pk>/assign-exam/",
    
            admin_views.assign_admission_exam,
    
            name="assign_admission_exam"
    
        ),

    path(

        "admissions/<int:pk>/<str:status>/",

        admin_views.admission_update_status,

        name="admission_status"

    ),

    path(
        "admission/<int:pk>/",
        admin_views.admission_detail,
        name="admission_detail",
    ),

    path(
        "admission/track/",
        admin_views.admission_track,
        name="admission_track"
    ),

    path(
        "admission-letter/<int:pk>/",
        admin_views.download_admission_letter,
        name="download_admission_letter"
    ),



]
