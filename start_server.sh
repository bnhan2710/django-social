#!/bin/bash

# Script to start the Django Social Media app with WebSocket support
echo "════════════════════════════════════════════"
echo "Starting Django Social Media with WebSockets"
echo "════════════════════════════════════════════"

# Check if Redis is running
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis server is already running"
else
    echo "🚀 Starting Redis server..."
    redis-server &
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis server started successfully"
    else
        echo "❌ Failed to start Redis server. Please start it manually."
        exit 1
    fi
fi

# Set environment variables
export DJANGO_SETTINGS_MODULE=social_media.settings

# Start the server with Daphne
echo "🚀 Starting Django with Daphne ASGI server..."
python3 -m daphne -b 0.0.0.0 -p 8000 social_media.asgi:application
