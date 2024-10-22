# run.py
"""
Este script inicializa y ejecuta una aplicación Flask utilizando SocketIO y Eventlet.
Importa y aplica el parche de Eventlet para mejorar la concurrencia. Luego, intenta importar
la aplicación Flask y el objeto SocketIO desde el módulo `app`. Si la importación falla, 
imprime un mensaje de error y lanza una excepción.
Si el script se ejecuta directamente (no importado como módulo), inicia el servidor 
SocketIO en la dirección '0.0.0.0' y el puerto 5000, con el modo de depuración desactivado.
Dependencias:
- eventlet
- Flask
- Flask-SocketIO
Uso:
    python run.py
"""

import eventlet
eventlet.monkey_patch()

try:
    from app import app, socketio
except ImportError as e:
    print(f"Error importing app or socketio: {e}")
    raise

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
