# LED Control System Deployment Guide

## Server Setup (Docker)

### Using Docker Compose (Recommended)

1. Navigate to the server directory:
   ```bash
   cd server
   ```
2. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   # Edit .env to set your SECRET_KEY
   ```
3. Build and run with Docker Compose:
   ```bash
   docker-compose up -d
   ```
4. Check if it's running:
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```
5. The server will be available at `http://your-server-ip:5005`

### Using Docker directly

```bash
# Build the image
docker build -t led-control-server .

# Run the container
docker run -d \
  --name led-control \
  -p 5005:5005 \
  -e SECRET_KEY="your-secret-key" \
  --restart unless-stopped \
  led-control-server
```

## Server Setup (Without Docker)

1. Install Python 3.8+ on your server
2. Navigate to the server directory:
   ```bash
   cd server
   ```
3. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Set environment variables:
   ```bash
   export SECRET_KEY="your-secret-key-here"
   ```
6. Run the server:
   ```bash
   python app.py
   ```

For production, use a WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
```

## Raspberry Pi Client Setup

1. Install Python 3 and pip:
   ```bash
   sudo apt-get update
   sudo apt-get install python3 python3-pip
   ```
2. Install uhubctl:
   ```bash
   sudo apt-get install libusb-1.0-0-dev
   git clone https://github.com/mvp/uhubctl
   cd uhubctl
   make
   sudo make install
   ```
3. Copy the client files to your Pi (e.g., to `/home/pi/led-controller/`)
4. Install dependencies:
   ```bash
   cd /home/pi/led-controller
   pip3 install -r requirements.txt
   ```
5. Test the client:
   ```bash
   python3 led_controller.py --server http://YOUR_SERVER_IP:5005
   ```
6. Install as a systemd service:
   ```bash
   # Edit the service file to update the server IP
   sudo nano led-controller.service
   
   # Copy to systemd
   sudo cp led-controller.service /etc/systemd/system/
   
   # Enable and start the service
   sudo systemctl enable led-controller
   sudo systemctl start led-controller
   
   # Check status
   sudo systemctl status led-controller
   ```

## Security Considerations

1. Use HTTPS in production (configure nginx/apache as reverse proxy)
2. Implement authentication (API keys or JWT tokens)
3. Use environment variables for sensitive configuration
4. Restrict CORS origins in production
5. Set up firewall rules to limit access

## Monitoring

Check logs:
- Server: Check Flask output or log files
- Client: `sudo journalctl -u led-controller -f`