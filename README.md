# Django Social Media with WebSockets

This is a Django social media application that uses WebSockets for real-time messaging.

## Running the Server

To properly run this server with WebSocket support, use the provided script:

```bash
./start_server.sh
```

This script will:

1. Check if Redis is running (required for WebSockets)
2. Start Redis if it's not already running
3. Start the Daphne ASGI server on port 8000

## Troubleshooting WebSocket Connections

If you're having issues with WebSocket connections:

1. Make sure the server is running with Daphne (not the standard `python manage.py runserver`)
2. Visit `/test-websocket/` to use the WebSocket testing tool
3. Check `/ws-debug/` for server-side WebSocket configuration information
4. Ensure Redis is running with `redis-cli ping` (should return "PONG")

## WebSocket URLs

The following WebSocket URLs are configured:

- `/messages/` - Primary WebSocket endpoint for messaging
- `/ws/messages/` - Alternative WebSocket endpoint
- `/ws/` - Simplified WebSocket endpoint
- `/chat/` - Another alternative WebSocket endpoint

## Development Notes

- The WebSocket implementation uses Django Channels
- Redis is used as the channel layer backend for WebSockets
- Authentication is required for using WebSocket functionality
