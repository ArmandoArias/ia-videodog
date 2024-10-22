# run.py

import eventlet
eventlet.monkey_patch()

try:
    from app import app, socketio
except ImportError as e:
    print(f"Error importing app or socketio: {e}")
    raise

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
