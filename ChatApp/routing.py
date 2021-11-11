from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter,URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path
from public_chat.consumers import PublicChatConsumer
from chat.consumers import ChatConsumer,CallConsumer
from notifications.consumers import NotificationConsumer

application = ProtocolTypeRouter({
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            #URL router()
            URLRouter([
                path("public_chat/<room_id>/",PublicChatConsumer.as_asgi()),
                path("chat/<room_id>/",ChatConsumer.as_asgi()),
                path("",NotificationConsumer.as_asgi()),
                path("call/", CallConsumer.as_asgi()),
            ])
        )
    )
})