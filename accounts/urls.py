from django.urls import path
from .views import portal_selection, login_view, logout_view, home, open_portal,about, contact,help, contact_us

app_name = 'accounts'

urlpatterns = [
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('about/', about, name='about'),
    path('contact-info/', contact, name='contact'),
    path("contact/", contact_us, name="contact_us"),
    path('help/', help, name='help'),
    path('logout/', logout_view, name='logout'),
    path('portal-selection/', portal_selection, name='portal_selection'),
    # dynamic portals
    path("portal/<int:school_id>/<str:portal>/", open_portal, name="open_portal"),


]
