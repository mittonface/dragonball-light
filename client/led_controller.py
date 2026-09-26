#!/usr/bin/env python3
import socketio
import subprocess
import time
import sys
import os
import argparse
import logging
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# If the server hasn't answered a heartbeat this long, exit and let systemd restart us
WATCHDOG_TIMEOUT = 120
HEARTBEAT_INTERVAL = 30
HEARTBEAT_TIMEOUT = 10
UHUBCTL_TIMEOUT = 15

class LEDController:
    def __init__(self, server_url, hub_location='1-1', port_number='2'):
        self.server_url = server_url
        self.hub_location = hub_location
        self.port_number = port_number
        self.current_state = 'off'
        self.sio = None
        self.last_healthy = time.monotonic()

    def new_client(self):
        # Reconnection is handled by run() with a fresh client each time; the
        # library's own reconnect racing our loop left a zombie "connected" client.
        sio = socketio.Client(reconnection=False)

        @sio.on('connect')
        def on_connect():
            logger.info(f"Connected to server at {self.server_url}")
            self.last_healthy = time.monotonic()
            
        @sio.on('disconnect')
        def on_disconnect():
            logger.info("Disconnected from server")
            
        @sio.on('current_state')
        def on_current_state(data):
            state = data.get('state', 'off')
            logger.info(f"Received initial state: {state}")
            self.set_led(state)
            
        @sio.on('state_change')
        def on_state_change(data):
            state = data.get('state', 'off')
            logger.info(f"State change requested: {state}")
            self.set_led(state)

        return sio
    
    def set_led(self, state):
        # Always apply to hardware (uhubctl is idempotent) so a hub that drifted
        # out of sync with current_state still gets corrected.
        action = 'on' if state == 'on' else 'off'
        cmd = ['sudo', 'uhubctl', '-l', self.hub_location, '-p', self.port_number, '-a', action]
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=UHUBCTL_TIMEOUT)
            logger.info(f"LED turned {state}")
            # Only report actual changes, otherwise the server's broadcast echo would loop
            if state != self.current_state:
                self.current_state = state
                self.sio.emit('state_update', {'state': state})
        except subprocess.TimeoutExpired:
            logger.error(f"uhubctl timed out after {UHUBCTL_TIMEOUT}s")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to control LED: {e}")
            logger.error(f"stderr: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
    
    def watchdog(self):
        # sio.connected can stay True on a dead connection, so require the
        # server to actually answer a round trip.
        while True:
            time.sleep(HEARTBEAT_INTERVAL)
            sio = self.sio
            if sio is not None and sio.connected:
                try:
                    sio.call('heartbeat', timeout=HEARTBEAT_TIMEOUT)
                    self.last_healthy = time.monotonic()
                except Exception as e:
                    logger.warning(f"Heartbeat failed: {e!r}")
            if time.monotonic() - self.last_healthy > WATCHDOG_TIMEOUT:
                logger.error(f"No heartbeat for over {WATCHDOG_TIMEOUT}s, exiting so systemd restarts us")
                os._exit(1)

    def run(self):
        threading.Thread(target=self.watchdog, daemon=True).start()
        while True:
            self.sio = self.new_client()
            try:
                logger.info(f"Attempting to connect to {self.server_url}")
                self.sio.connect(self.server_url, wait_timeout=10)
                self.sio.wait()
            except Exception as e:
                logger.error(f"Connection error: {e}")
            finally:
                try:
                    self.sio.disconnect()
                except Exception:
                    pass
            logger.info("Retrying in 5 seconds...")
            time.sleep(5)

def main():
    parser = argparse.ArgumentParser(description='LED Controller for Raspberry Pi')
    parser.add_argument('--server', default='http://localhost:5005',
                        help='Server URL (default: http://localhost:5005)')
    parser.add_argument('--hub', default='1-1',
                        help='USB hub location (default: 1-1)')
    parser.add_argument('--port', default='2',
                        help='USB port number (default: 2)')
    
    args = parser.parse_args()
    
    controller = LEDController(args.server, args.hub, args.port)
    
    try:
        controller.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)

if __name__ == '__main__':
    main()