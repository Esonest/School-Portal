"""
URL configuration for school_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include(('django.contrib.auth.urls', 'auth'), namespace='auth')),
    path('', include('accounts.urls', namespace='accounts')),
    path('teachers/', include('teachers.urls', namespace='teachers')),
    path('students/', include('students.urls', namespace='students')),
    path('results/', include('results.urls', namespace='results')),
    path('finance/', include('finance.urls', namespace='finance')),
    path('attendance/', include('attendance.urls', namespace='attendance')),
    path('assignments/', include('assignments.urls', namespace='assignments')),
    path('cbt/', include('cbt.urls', namespace='cbt')),
    path('notes/', include('notes.urls', namespace='notes')),
    path('school_admin/', include('school_admin.urls', namespace='school_admin')),
    path("superadmin/", include("superadmin.urls", namespace='superadmin')),

   
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
