import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import liveclass.routing


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            liveclass.routing.websocket_urlpatterns
        )
    ),
})
