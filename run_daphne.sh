#!/bin/bash

# This script runs the Django server with Daphne for ASGI/WebSocket support
echo "Starting Django with Daphne ASGI server..."
python -m daphne social_media.asgi:application -b 0.0.0.0 -p 8000
