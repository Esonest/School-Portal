from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/liveclass/(?P<pk>\d+)/$', consumers.LiveClassConsumer.as_asgi()),
]
