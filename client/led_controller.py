#!/usr/bin/env python3
import socketio
import subprocess
import time
import sys
import os
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LEDController:
    def __init__(self, server_url, hub_location='1-1', port_number='2'):
        self.server_url = server_url
        self.hub_location = hub_location
        self.port_number = port_number
        self.current_state = 'off'
        self.sio = socketio.Client()
        self.setup_handlers()
        
    def setup_handlers(self):
        @self.sio.on('connect')
        def on_connect():
            logger.info(f"Connected to server at {self.server_url}")
            self.sio.emit('pi_connected')
            
        @self.sio.on('disconnect')
        def on_disconnect():
            logger.info("Disconnected from server")
            
        @self.sio.on('current_state')
        def on_current_state(data):
            state = data.get('state', 'off')
            logger.info(f"Received initial state: {state}")
            self.set_led(state)
            
        @self.sio.on('state_change')
        def on_state_change(data):
            state = data.get('state', 'off')
            logger.info(f"State change requested: {state}")
            self.set_led(state)
    
    def set_led(self, state):
        if state == self.current_state:
            logger.info(f"LED already in state: {state}")
            return
            
        action = 'on' if state == 'on' else 'off'
        cmd = ['sudo', 'uhubctl', '-l', self.hub_location, '-p', self.port_number, '-a', action]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.current_state = state
            logger.info(f"LED turned {state}")
            self.sio.emit('state_update', {'state': state})
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to control LED: {e}")
            logger.error(f"stderr: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
    
    def run(self):
        while True:
            try:
                logger.info(f"Attempting to connect to {self.server_url}")
                self.sio.connect(self.server_url)
                self.sio.wait()
            except Exception as e:
                logger.error(f"Connection error: {e}")
                logger.info("Retrying in 5 seconds...")
                time.sleep(5)

def main():
    parser = argparse.ArgumentParser(description='LED Controller for Raspberry Pi')
    parser.add_argument('--server', default='http://localhost:5000', 
                        help='Server URL (default: http://localhost:5000)')
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