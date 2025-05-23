from django.urls import path, re_path
from . import consumers

websocket_urlpatterns = [
    # Main WebSocket URLs - should match with client-side JS
    path('messages/', consumers.ChatConsumer.as_asgi()),  # Primary path
    
    # Alternative paths for flexibility
    re_path(r'ws/messages/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'messages$', consumers.ChatConsumer.as_asgi()),  # Without trailing slash
    re_path(r'ws/messages$', consumers.ChatConsumer.as_asgi()),  # Without trailing slash
    
    # Additional paths for testing
    path('ws/', consumers.ChatConsumer.as_asgi()),
    path('chat/', consumers.ChatConsumer.as_asgi()),
]
