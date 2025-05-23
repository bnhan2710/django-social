from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json
import socket
import os
import sys
import django
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@login_required(login_url='signin')
def websocket_debug(request):
    """Debug view for WebSocket diagnostics"""
    
    # System info
    debug_info = {
        'system': {
            'python_version': sys.version,
            'django_version': django.__version__,
            'hostname': socket.gethostname(),
            'ip': socket.gethostbyname(socket.gethostname()),
        },
        'request': {
            'is_secure': request.is_secure(),
            'host': request.get_host(),
            'path': request.path,
            'user_authenticated': request.user.is_authenticated,
            'user_id': request.user.id if request.user.is_authenticated else None,
            'user_name': request.user.username if request.user.is_authenticated else None,
        },
        'channels': {
            'channel_layer_configured': False,
        },
        'environment': {
            'settings_module': os.environ.get('DJANGO_SETTINGS_MODULE', 'Not set'),
        }
    }
    
    # Test channel layer
    try:
        channel_layer = get_channel_layer()
        debug_info['channels']['channel_layer_configured'] = True
        debug_info['channels']['channel_layer_type'] = str(type(channel_layer))
        
        # Try to send a test message
        try:
            test_group = f"test_group_{request.user.id}"
            async_to_sync(channel_layer.group_add)(test_group, "test_channel")
            async_to_sync(channel_layer.group_send)(
                test_group,
                {
                    "type": "test.message",
                    "text": "Hello, world!",
                }
            )
            debug_info['channels']['test_message_sent'] = True
        except Exception as e:
            debug_info['channels']['test_message_error'] = str(e)
    except Exception as e:
        debug_info['channels']['channel_layer_error'] = str(e)
    
    # WebSocket URLs
    debug_info['websocket_urls'] = [
        f"{'wss' if request.is_secure() else 'ws'}://{request.get_host()}/messages/",
        f"{'wss' if request.is_secure() else 'ws'}://{request.get_host()}/ws/messages/",
        f"{'wss' if request.is_secure() else 'ws'}://{request.get_host()}/ws/",
        f"{'wss' if request.is_secure() else 'ws'}://{request.get_host()}/chat/",
    ]
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(debug_info)
    
    return render(request, 'websocket_debug.html', {'debug_info': json.dumps(debug_info, indent=2)})
