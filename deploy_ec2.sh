#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# Django Social Media with WebSockets - AWS EC2 Deployment Script
# ═══════════════════════════════════════════════════════════════════════════

set -e  # Exit immediately if a command exits with a non-zero status

echo "════════════════════════════════════════════════════════════════════"
echo "🚀 Django Social Media with WebSockets - AWS EC2 Deployment"
echo "════════════════════════════════════════════════════════════════════"

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Install Python and required dependencies
echo "📦 Installing Python and required dependencies..."
sudo apt-get install -y python3 python3-pip python3-dev python3-venv redis-server nginx supervisor python3-tk

# Create and activate virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install required Python packages
echo "📦 Installing Python packages..."
pip install django channels channels_redis daphne uvicorn gunicorn

# Install project dependencies from requirements.txt if it exists
if [ -f requirements.txt ]; then
    echo "📦 Installing project dependencies from requirements.txt..."
    pip install -r requirements.txt
fi

# Fix common import issues
echo "🔧 Checking for and fixing common import issues..."
if grep -q "from turtle import" core/models.py; then
    echo "⚠️ Found problematic 'turtle' import in models.py. Fixing..."
    # Create backup
    cp core/models.py core/models.py.bak
    # Replace 'from turtle import update' with 'from django.db.models import update_or_create'
    sed -i 's/from turtle import update/# Removed problematic import: from turtle import update/' core/models.py
    echo "✅ Fixed turtle import in models.py"
fi

# Ensure Redis is running
echo "🔄 Ensuring Redis server is running..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Create logs directory
mkdir -p logs

# Create supervisor configuration for Daphne
echo "⚙️ Setting up supervisor configuration..."
sudo tee /etc/supervisor/conf.d/django_social_media.conf > /dev/null << EOF
[program:django_social_media]
command=${PWD}/venv/bin/daphne -b 0.0.0.0 -p 8000 social_media.asgi:application
directory=${PWD}
user=$(whoami)
autostart=true
autorestart=true
environment=DJANGO_SETTINGS_MODULE="social_media.settings_production",DJANGO_SECRET_KEY="$(openssl rand -hex 32)"
stdout_logfile=${PWD}/logs/daphne.log
stderr_logfile=${PWD}/logs/daphne_error.log
stopasgroup=true
killasgroup=true
priority=1000
EOF

# Create systemd service file as a backup option
echo "⚙️ Setting up systemd service..."
sudo tee /etc/systemd/system/django_social_media.service > /dev/null << EOF
[Unit]
Description=Django Social Media with WebSockets
After=network.target redis-server.service
Wants=redis-server.service

[Service]
User=$(whoami)
Group=$(id -gn)
WorkingDirectory=${PWD}
Environment="DJANGO_SETTINGS_MODULE=social_media.settings_production"
Environment="DJANGO_SECRET_KEY=$(openssl rand -hex 32)"
ExecStart=${PWD}/venv/bin/daphne -b 0.0.0.0 -p 8000 social_media.asgi:application
Restart=on-failure
RestartSec=5s
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Create Nginx configuration
echo "⚙️ Setting up Nginx configuration..."
sudo tee /etc/nginx/sites-available/django_social_media > /dev/null << EOF
server {
    listen 80;
    server_name _;  # Replace with your domain name or EC2 public IP

    location /static/ {
        alias ${PWD}/static/;
    }

    location /media/ {
        alias ${PWD}/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;  # Extend timeout for WebSocket connections
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/django_social_media /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Run Django migrations
# echo "🔄 Running Django migrations..."
# export DJANGO_SETTINGS_MODULE=social_media.settings_production
# python manage.py migrate

# Collect static files
echo "📂 Collecting static files..."
python manage.py collectstatic --noinput

# # Create a .env file for environment variables
# echo "📝 Creating .env file..."
# cat > .env << EOF
# DJANGO_SETTINGS_MODULE=social_media.settings_production
# DJANGO_SECRET_KEY=$(openssl rand -hex 32)
# EOF

# Enable and start services
echo "🔄 Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable django_social_media.service
sudo systemctl start django_social_media.service
sudo systemctl restart nginx

# Configure supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart django_social_media

# Create a start script for manual execution if needed
echo "📝 Creating start script..."
cat > start_server.sh << EOF
#!/bin/bash

echo "════════════════════════════════════════════"
echo "Starting Django Social Media with WebSockets"
echo "════════════════════════════════════════════"

# Activate virtual environment
source venv/bin/activate

# Load environment variables
if [ -f .env ]; then
    export \$(grep -v '^#' .env | xargs)
fi

# Check if Redis is running
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis server is already running"
else
    echo "🚀 Starting Redis server..."
    sudo systemctl start redis-server
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis server started successfully"
    else
        echo "❌ Failed to start Redis server. Please start it manually."
        exit 1
    fi
fi

# Start the server with Daphne
echo "🚀 Starting Django with Daphne ASGI server..."
./venv/bin/daphne -b 0.0.0.0 -p 8000 social_media.asgi:application
EOF

chmod +x start_server.sh

# Create a status check script
echo "📝 Creating status check script..."
cat > check_status.sh << EOF
#!/bin/bash

echo "════════════════════════════════════════════"
echo "Django Social Media Status Check"
echo "════════════════════════════════════════════"

echo "📊 Systemd Service Status:"
sudo systemctl status django_social_media.service

echo "📊 Supervisor Status:"
sudo supervisorctl status django_social_media

echo "📊 Redis Status:"
redis-cli ping

echo "📊 Nginx Status:"
sudo systemctl status nginx

echo "📊 Open Ports:"
sudo netstat -tulpn | grep -E ':(80|8000)'
EOF

chmod +x check_status.sh

echo "════════════════════════════════════════════════════════════════════"
echo "✅ Deployment complete! Your Django Social Media app is now running."
echo "════════════════════════════════════════════════════════════════════"
echo "📝 Notes:"
echo "- The application is running on port 80 (HTTP)"
echo "- WebSockets are configured and running"
echo "- The application will continue running after you log out"
echo "- To check status: ./check_status.sh"
echo "- To manually start: sudo systemctl start django_social_media.service"
echo "- To restart: sudo systemctl restart django_social_media.service"
echo "- Logs are available in the logs directory"
echo "════════════════════════════════════════════════════════════════════" 