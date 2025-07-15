from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*")

led_state = {"status": "off", "connected_clients": 0}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(led_state)

@app.route('/api/toggle', methods=['POST'])
def toggle_led():
    new_state = request.json.get('state', 'off')
    if new_state not in ['on', 'off']:
        return jsonify({"error": "Invalid state"}), 400
    
    led_state['status'] = new_state
    socketio.emit('state_change', {'state': new_state}, namespace='/')
    return jsonify({"status": new_state})

@socketio.on('connect')
def handle_connect():
    led_state['connected_clients'] += 1
    emit('current_state', {'state': led_state['status']})
    print(f"Client connected. Total clients: {led_state['connected_clients']}")

@socketio.on('disconnect')
def handle_disconnect():
    led_state['connected_clients'] -= 1
    print(f"Client disconnected. Total clients: {led_state['connected_clients']}")

@socketio.on('pi_connected')
def handle_pi_connected():
    print("Raspberry Pi connected")
    emit('current_state', {'state': led_state['status']})

@socketio.on('state_update')
def handle_state_update(data):
    current_state = data.get('state')
    led_state['status'] = current_state
    emit('state_change', {'state': current_state}, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5005))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)