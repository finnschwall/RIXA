# chat/routing.py
from django.urls import re_path

from . import consumers

#currently all websockets are served by a single consumer
websocket_urlpatterns = [
re_path(r"^ws/", consumers.ChatConsumer.as_asgi()),
    # re_path(r"ws/chat/(?P<room_name>\w+)/$", consumers.ChatConsumer.as_asgi()),
]