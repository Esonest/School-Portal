from django.urls import path
from . import views
from django.views.generic import TemplateView

app_name = "liveclass"  

urlpatterns = [
    path("", views.liveclass_list, name="liveclass_list"),
    path("create/", views.liveclass_create, name="liveclass_create"),
    path("api/translate/", views.translate, name="translate"),
    path("app/", views.liveclass_frontend, name="frontend"),
    path("app/<path:path>", TemplateView.as_view(template_name="index.html")),


    path("<int:pk>/edit/", views.liveclass_update, name="liveclass_update"),
    path("<int:pk>/delete/", views.liveclass_delete, name="liveclass_delete"),
    path("<int:pk>/join/", views.liveclass_join, name="liveclass_join"),
    path("<int:pk>/attendance/", views.attendance_dashboard, name="attendance_dashboard"),
    path("<int:pk>/start/", views.liveclass_start, name="liveclass_start"),
    path ('leave/<int:pk>/', views.liveclass_leave, name='liveclass_leave'),
    path("join/<int:pk>/enable-camera/", views.liveclass_enable_camera, name="liveclass_enable_camera"),
    path('liveclass/<int:pk>/peers/', views.liveclass_peers, name='liveclass_peers'),
    path('api/liveclass/<int:pk>/token/', views.liveclass_token_api, name='liveclass_token_api'),
    path("api/liveclass/<int:pk>/waiting/", views.waiting_list, name="waiting_list"),
    path("api/liveclass/<int:pk>/approve/", views.approve_student, name="approve_student"),
    path("api/liveclass/<int:pk>/reject/", views.reject_student, name="reject_student"),
    path("api/liveclass/<int:pk>/request/", views.request_join_liveclass, name="request_join"),
    path("api/liveclass/<int:pk>/status/", views.check_waiting_status, name="check_status"),
    path("api/liveclass/<int:pk>/waiting-heartbeat/", views.waiting_heartbeat),
    path("api/liveclass/<int:pk>/approve-all/", views.approve_all_students),
    path("api/liveclass/<int:pk>/assign-breakout/",views.assign_breakout,name="assign_breakout"),
    path("api/liveclass/<int:pk>/reject-all/", views.reject_all_students),
    path("api/liveclass/<int:pk>/remove-student/",views.remove_student,name="remove_student"),
    path("api/liveclass/<int:pk>/removed-students/",views.removed_students,name="removed_students"),
    path("api/liveclass/<int:pk>/breakout-token/",views.breakout_token,name="breakout_token"),
    path("api/liveclass/<int:pk>/breakout-assignments/",views.breakout_assignments,name="breakout_assignments"),
    path("api/liveclass/<int:pk>/start-recording/",views.start_recording_api,name="start_recording_api"),
    path("api/liveclass/<int:pk>/stop-recording/",views.stop_recording_api,name="stop_recording_api"),
    path("webhooks/recording/",views.recording_webhook,name="recording_webhook"),
    path("api/liveclass/<int:pk>/recording-status/",views.recording_status_api,name="recording_status_api"),
    


        # ==========================================================
    # PUBLIC LIVE EVENT
    # ==========================================================

    path(
        "events/create/",
        views.public_event_create,
        name="public_event_create",
    ),

    path(
        "event/<slug:event_slug>/edit/",
        views.public_event_edit,
        name="public_event_edit",
    ),

    path(
        "event/<slug:event_slug>/",
        views.public_event,
        name="public_event",
    ),

    path(
        "event/<slug:event_slug>/manage/",
        views.public_event_manage,
        name="public_event_manage",
    ),

    path(
        "event/<slug:event_slug>/delete/",
        views.public_event_delete,
        name="public_event_delete",
    ),

    path(
        "events/",
        views.public_event_list,
        name="public_event_list",
    ),

    path(
        "event/<slug:event_slug>/teacher-room/",
        views.public_event_teacher_room,
        name="public_event_teacher_room",
    ),

    path(
        "api/liveclass/event/<slug:event_slug>/join/",
        views.public_event_join,
        name="public_event_join",
    ),

    path(
        "api/liveclass/event/<slug:event_slug>/token/",
        views.public_event_token_api,
        name="public_event_token_api",
    ),

    path(
        "api/liveclass/event/<slug:event_slug>/teacher-token/",
        views.public_event_teacher_token_api,
        name="public_event_teacher_token_api",
    ),

    path(
        "event/<slug:event_slug>/room/",
        views.public_event_guest_room,
        name="public_event_guest_room",
    ),


    path(
        "api/liveclass/event/<slug:event_slug>/heartbeat/",
        views.public_event_guest_heartbeat,
        name="public_event_guest_heartbeat",
    ),

    path(
        "api/liveclass/event/<slug:event_slug>/leave/",
        views.public_event_guest_leave,
        name="public_event_guest_leave",
    ),

    path(
        "api/liveclass/event/<slug:event_slug>/end/",
        views.public_event_end,
        name="public_event_end",
    ),


    path("<int:pk>/", views.liveclass_frontend),

]

