"""
server_web.py - Servidor Flask + Socket.IO para monitoramento web de lives YouTube
Substitui OBS por uma interface HTML com grid responsivo
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from datetime import datetime as dt, timezone
import threading
import time
import logging
from youtube_web_manager import YouTubeWebManager
from log_config import log_terminal

# Configuração Flask
app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['SECRET_KEY'] = 'youtube-monitor-web-secret-2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', ping_timeout=120, ping_interval=25)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Estado global
youtube_manager = None
connected_clients = set()
update_thread = None
stop_update = threading.Event()

# Template HTML - Grid responsivo de lives


@app.route('/')
def index():
    """Serve a página HTML principal"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Endpoint de health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': dt.now(timezone.utc).isoformat(),
        'connected_clients': len(connected_clients),
        'manager_running': youtube_manager is not None
    })

@socketio.on('connect')
def handle_connect():
    """Cliente WebSocket conecta"""
    connected_clients.add(request.sid)
    log_terminal(f"Cliente conectado: {request.sid} (Total: {len(connected_clients)})", cor='green')
    
    # Enviar dados atuais imediatamente
    if youtube_manager:
        emit('streams_update', youtube_manager.get_streams_data())

@socketio.on('disconnect')
def handle_disconnect():
    """Cliente WebSocket desconecta"""
    connected_clients.discard(request.sid)
    log_terminal(f"Cliente desconectado: {request.sid} (Total: {len(connected_clients)})", cor='yellow')

def broadcast_update():
    """Thread que atualiza e envia dados para todos os clientes"""
    global youtube_manager
    
    try:
        youtube_manager = YouTubeWebManager()
        log_terminal("YouTubeWebManager iniciado com sucesso", cor='green')
    except Exception as e:
        log_terminal(f"Erro ao inicializar YouTubeWebManager: {e}", level='error', cor='red')
        return
    
    while not stop_update.is_set():
        try:
            # Executar ciclo de monitoramento
            youtube_manager.run_cycle()
            
            # Enviar dados para todos os clientes conectados
            if connected_clients:
                streams_data = youtube_manager.get_streams_data()
                socketio.emit('streams_update', streams_data, namespace='/')
            
            # Aguardar próximo ciclo
            time.sleep(youtube_manager.intervalo_execucao)
            
        except Exception as e:
            log_terminal(f"Erro no broadcast_update: {e}", level='error', cor='red')
            time.sleep(5)

def start_update_thread():
    """Inicia a thread de atualização em background"""
    global update_thread
    if update_thread is None or not update_thread.is_alive():
        stop_update.clear()
        update_thread = threading.Thread(target=broadcast_update, daemon=True)
        update_thread.start()
        log_terminal("Thread de atualização iniciada", cor='green')

if __name__ == '__main__':
    start_update_thread()
    
    try:
        log_terminal("Servidor iniciando em http://0.0.0.0:5000", cor='green')
        log_terminal("Acesse em: http://localhost:5000 ou http://<SEU_IP>:5000", cor='cyan')
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        log_terminal("Servidor encerrado pelo usuário", cor='yellow')
        stop_update.set()
