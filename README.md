# Dragonball Light Controller

A real-time LED control system that allows remote control of a USB-powered LED light connected to a Raspberry Pi. The system uses WebSockets for instant state synchronization between a web interface and the Raspberry Pi.

## How It Works

This application consists of two main components:

### 1. **Server** (Flask + Socket.IO)
A web server that provides:
- **Web Interface**: A simple UI for toggling the LED on/off
- **REST API**: HTTP endpoints for status queries and state changes
- **WebSocket Server**: Real-time bidirectional communication using Socket.IO

The server maintains the LED state in memory and broadcasts state changes to all connected clients (both web browsers and the Raspberry Pi).

**Key Files:**
- `server/app.py` - Flask application with Socket.IO integration
- `server/templates/index.html` - Web interface for controlling the LED
- `server/requirements.txt` - Python dependencies (Flask, Flask-SocketIO, eventlet)

### 2. **Client** (Raspberry Pi Controller)
A Python script that runs on the Raspberry Pi and:
- Connects to the server via WebSocket
- Listens for state change events
- Controls USB power using `uhubctl` to turn the LED on/off
- Reports state updates back to the server

**Key Files:**
- `client/led_controller.py` - Socket.IO client that controls USB power
- `client/requirements.txt` - Python dependencies (python-socketio)
- `client/led-controller.service` - systemd service configuration

## Architecture

```
┌─────────────────┐         WebSocket          ┌──────────────────┐
│   Web Browser   │◄──────────────────────────►│                  │
│  (Control UI)   │                             │  Flask Server    │
└─────────────────┘                             │  + Socket.IO     │
                                                │                  │
┌─────────────────┐         WebSocket          │  (Port 5005)     │
│  Raspberry Pi   │◄──────────────────────────►│                  │
│   + uhubctl     │                             └──────────────────┘
│   + LED Light   │
└─────────────────┘
```

**Communication Flow:**
1. User clicks toggle button in web interface
2. Browser sends state change request to server (via Socket.IO or REST API)
3. Server updates internal state and broadcasts change to all connected clients
4. Raspberry Pi receives the state change event
5. Pi executes `uhubctl` command to toggle USB port power
6. LED turns on or off instantly
7. Pi confirms state change back to server

## Deployment & Hosting

### Server Deployment

The server is deployed using **Docker** and **GitHub Actions CI/CD**:

1. **Automated Deployment Pipeline** (`.github/workflows/deploy.yml`):
   - Triggered on push to `main` branch
   - Validates Dockerfile with hadolint
   - Builds Docker image using buildx
   - Compresses and transfers image to remote server via SSH
   - Deploys using Docker Compose
   - Performs health checks to verify deployment

2. **Hosting Environment**:
   - Runs in a Docker container on a remote server
   - Uses Docker Compose for orchestration
   - Configured with restart policy (`unless-stopped`)
   - Connects to external `proxy-network` for reverse proxy integration
   - Exposed on port 5005

3. **Required GitHub Secrets**:
   - `SERVER_HOST` - Remote server IP/hostname
   - `SERVER_USER` - SSH username
   - `SERVER_SSH_KEY` - Private SSH key for authentication
   - `SECRET_KEY` - Flask secret key (set via environment variable)

4. **Health Monitoring**:
   - Docker health checks every 30 seconds
   - Deployment verification via `/api/status` endpoint
   - Automatic retries with exponential backoff

### Raspberry Pi Setup

The Raspberry Pi client runs as a systemd service:

1. Install `uhubctl` for USB power control
2. Install Python dependencies from `client/requirements.txt`
3. Configure `led-controller.service` with server URL
4. Enable service to start on boot: `sudo systemctl enable led-controller`

The client automatically reconnects if the connection is lost, ensuring reliable operation.

## Local Development

### Server
```bash
cd server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="dev-secret-key"
python app.py
```

Access the web interface at `http://localhost:5005`

### Client (Testing on Raspberry Pi)
```bash
cd client
pip3 install -r requirements.txt
python3 led_controller.py --server http://YOUR_SERVER_IP:5005 --hub 1-1 --port 2
```

## API Endpoints

- `GET /` - Web interface
- `GET /api/status` - Get current LED state and connected client count
- `POST /api/toggle` - Toggle LED state (body: `{"state": "on"}` or `{"state": "off"}`)

## WebSocket Events

**Server → Client:**
- `current_state` - Sent on connection with current LED state
- `state_change` - Broadcast when state changes

**Client → Server:**
- `pi_connected` - Raspberry Pi announces connection
- `state_update` - Pi confirms state change

## Requirements

### Server
- Python 3.8+
- Flask, Flask-SocketIO, eventlet
- Docker (for containerized deployment)

### Raspberry Pi
- Python 3
- `uhubctl` (USB hub control utility)
- `python-socketio` library

## Additional Documentation

- See `DEPLOYMENT.md` for detailed deployment instructions
- See `.github/workflows/deploy.yml` for CI/CD pipeline configuration
