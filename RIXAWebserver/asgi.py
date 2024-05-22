"""
ASGI config for RIXAWebserver project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""
"""
ASGI config for RIXAWebserver project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RIXAWebserver.settings')
from django.conf import settings
django.setup()


from channels.auth import AuthMiddlewareStack

from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

import dashboard.routing
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
                AuthMiddlewareStack(URLRouter(dashboard.routing.websocket_urlpatterns))),
    # "plugin_system" : ChannelNameRouter({
    #     "thumbnails-generate": dashboard.consumers.EchoConsumer,
    #     # "thumbnails-delete": some_other_app,
    # })
    },

)

