from django.urls import path
from . import views
from django.views.generic import TemplateView

app_name = "liveclass"  

urlpatterns = [
    path("", views.liveclass_list, name="liveclass_list"),
    path("create/", views.liveclass_create, name="liveclass_create"),
    path("<int:pk>/edit/", views.liveclass_update, name="liveclass_update"),
    path("<int:pk>/delete/", views.liveclass_delete, name="liveclass_delete"),
    path("<int:pk>/join/", views.liveclass_join, name="liveclass_join"),
    path("<int:pk>/attendance/", views.attendance_dashboard, name="attendance_dashboard"),
    path("<int:pk>/start/", views.liveclass_start, name="liveclass_start"),
    path('leave/<int:pk>/', views.liveclass_leave, name='liveclass_leave'),
    path("join/<int:pk>/enable-camera/", views.liveclass_enable_camera, name="liveclass_enable_camera"),
    path('liveclass/<int:pk>/peers/', views.liveclass_peers, name='liveclass_peers'),
    
  
    path('api/liveclass/<int:pk>/token/', views.liveclass_token_api, name='liveclass_token_api'),
   
    path("<int:pk>/start-recording/", views.start_recording_api),
    path("api/translate/", views.translate, name="translate"),

    path("app/", views.liveclass_frontend, name="frontend"),
    path("<int:pk>/", views.liveclass_frontend),
    path("app/<path:path>", TemplateView.as_view(template_name="index.html")),

]

