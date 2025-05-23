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
    sudo service redis-server start
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis server started successfully"
    else
        echo "❌ Failed to start Redis server. Please start it manually."
        exit 1
    fi
fi

# Load environment variables if .env file exists
if [ -f .env ]; then
    echo "📝 Loading environment variables from .env file"
    export $(grep -v '^#' .env | xargs)
else
    # Set default environment variables
    echo "📝 Setting default environment variables"
    export DJANGO_SETTINGS_MODULE=social_media.settings
fi

# Check if running in background mode
if [ "$1" == "--background" ] || [ "$1" == "-b" ]; then
    echo "🚀 Starting Django with Daphne ASGI server in background mode..."
    
    # Create logs directory if it doesn't exist
    mkdir -p logs
    
    # Start the server with nohup to keep it running after terminal closes
    nohup bash -c '
        # Try different paths to find daphne
        if command -v daphne &> /dev/null; then
            daphne -b 0.0.0.0 -p 8000 social_media.asgi:application
        elif [ -f ~/.local/bin/daphne ]; then
            ~/.local/bin/daphne -b 0.0.0.0 -p 8000 social_media.asgi:application
        else
            echo "❌ Daphne not found. Please install it with: pip install daphne"
            exit 1
        fi
    ' > logs/daphne.log 2>&1 &
    
    echo "✅ Server started in background mode. PID: $!"
    echo "📝 Logs available at: $(pwd)/logs/daphne.log"
    echo "📊 To check if server is running: ps aux | grep daphne"
    echo "🛑 To stop the server: pkill -f daphne"
else
    echo "🚀 Starting Django with Daphne ASGI server..."
    
    # Try different paths to find daphne
    if command -v daphne &> /dev/null; then
        echo "Using system daphne"
        daphne -b 0.0.0.0 -p 8000 social_media.asgi:application
    elif [ -f ~/.local/bin/daphne ]; then
        echo "Using user-installed daphne"
        ~/.local/bin/daphne -b 0.0.0.0 -p 8000 social_media.asgi:application
    else
        echo "❌ Daphne not found. Installing daphne..."
        pip install daphne
        ~/.local/bin/daphne -b 0.0.0.0 -p 8000 social_media.asgi:application
    fi
fi
