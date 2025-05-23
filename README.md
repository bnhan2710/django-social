# Django Social Media with WebSockets

A social media platform built with Django and WebSockets for real-time messaging.

## Features

- User authentication and profiles
- Posts and comments
- Likes and follows
- Real-time messaging with WebSockets
- Thread-based conversations
- Read receipts and typing indicators

## Local Development

### Prerequisites

- Python 3.8+
- Redis server
- Git

### Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd django_social_media
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run migrations:
   ```
   python manage.py migrate
   ```

4. Start the development server:
   ```
   ./start_server.sh
   ```

5. Visit http://localhost:8000 in your browser

## AWS EC2 Deployment

### Prerequisites

- AWS account
- EC2 instance (Ubuntu recommended)
- Domain name (optional)

### Deployment Steps

1. Connect to your EC2 instance:
   ```
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

2. Clone the repository:
   ```
   git clone <repository-url>
   cd django_social_media
   ```

3. Run the deployment script:
   ```
   chmod +x deploy_ec2.sh
   ./deploy_ec2.sh
   ```

4. The script will:
   - Install all required dependencies
   - Set up a Python virtual environment
   - Configure Nginx as a reverse proxy
   - Set up Supervisor to manage the application process
   - Configure systemd service for persistent operation
   - Start the application

5. Access your application at http://your-ec2-ip

### Running as a System Service

The deployment script configures your application to run as a system service, which means:

- It will continue running after you log out of the SSH session
- It will automatically restart if it crashes
- It will start automatically when the server reboots

To manage the service:

```bash
# Check status
sudo systemctl status django_social_media.service

# Start service
sudo systemctl start django_social_media.service

# Stop service
sudo systemctl stop django_social_media.service

# Restart service
sudo systemctl restart django_social_media.service

# View logs
sudo journalctl -u django_social_media.service
```

You can also use the included status check script:
```bash
./check_status.sh
```

### Environment Variables

For production, the deployment script automatically creates a `.env` file with:

- `DJANGO_SETTINGS_MODULE=social_media.settings_production`
- `DJANGO_SECRET_KEY=<randomly-generated-key>`

To add additional environment variables, edit the `.env` file:
```bash
nano .env
```

### SSL Configuration

To enable HTTPS:

1. Get an SSL certificate (e.g., using Let's Encrypt):
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

2. Set the following in settings_production.py:
   ```python
   SECURE_SSL_REDIRECT = True
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   SECURE_HSTS_SECONDS = 31536000  # 1 year
   SECURE_HSTS_INCLUDE_SUBDOMAINS = True
   SECURE_HSTS_PRELOAD = True
   ```

## Troubleshooting

### WebSocket Connection Issues

1. Check if Redis is running:
   ```
   redis-cli ping
   ```

2. Check Daphne logs:
   ```
   tail -f logs/daphne.log
   ```

3. Visit the WebSocket debug page at `/ws-debug/`

### Server Not Starting

1. Check systemd service status:
   ```
   sudo systemctl status django_social_media.service
   ```

2. Check supervisor logs:
   ```
   sudo supervisorctl status django_social_media
   sudo tail -f /var/log/supervisor/supervisord.log
   ```

3. Check Nginx logs:
   ```
   sudo tail -f /var/log/nginx/error.log
   ```

### After Server Reboot

The application should start automatically after a server reboot. If not:

1. Check if Redis is running:
   ```
   sudo systemctl status redis-server
   ```

2. Start Redis if needed:
   ```
   sudo systemctl start redis-server
   ```

3. Check and start the Django service:
   ```
   sudo systemctl start django_social_media.service
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

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
