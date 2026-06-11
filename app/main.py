import os

from flask import Flask, jsonify, send_from_directory, request, Response
from flask_cors import CORS
from app.core.config import settings

# Diretório onde o React/Vite vai gerar a build estática
frontend_dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist'))

# Inicializa o Flask configurando a pasta de arquivos estáticos (Frontend React)
# static_url_path='' faz com que os arquivos em dist sejam servidos na raiz (ex: /assets/...)
app = Flask(__name__, static_folder=frontend_dist_path, static_url_path='')

# Adicionando CORS para permitir requisições locais
CORS(app)

# --- AUTENTICAÇÃO E WAF GLOBAL PARA /api/ ---
import jwt
import urllib.parse
JWT_SECRET = os.environ.get("JWT_SECRET", "super-secret-key-change-in-production")

# Padrões comuns de ataques
ATTACK_PATTERNS = ["<script", "union select", "select *", "drop table", "1=1", ".env", "etc/passwd", "wp-admin", "exec xp_"]

def is_malicious(req):
    # Verifica a URL
    url_decoded = urllib.parse.unquote(req.url).lower()
    if any(pattern in url_decoded for pattern in ATTACK_PATTERNS):
        return True
    
    # Verifica o corpo da requisição (se for JSON/texto)
    try:
        if req.is_json and req.data:
            body_str = req.get_data(as_text=True).lower()
            if any(pattern in body_str for pattern in ATTACK_PATTERNS):
                return True
    except:
        pass
        
    return False

@app.before_request
def require_login():
    # Honeypot / WAF simples
    if is_malicious(request):
        troll_html = """
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Acesso Negado</title>
            <style>
                body { background-color: #000; color: #fff; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; font-family: sans-serif; text-align: center; }
                img { max-width: 400px; margin-bottom: 20px; border-radius: 20px; }
                h1 { color: #ff3333; }
            </style>
        </head>
        <body>
            <img src="/imgtroll.webp" alt="Troll">
            <h1>Não foi dessa vez.</h1>
            <p>Tentativa de ataque registrada.</p>
        </body>
        </html>
        """
        return Response(troll_html, status=403, mimetype='text/html')

    # Permite OPTIONS (CORS) e health check sem token
    if request.method == 'OPTIONS' or request.path == '/health':
        return
    
    # Protege todas as rotas da API, exceto as rotas de autenticação
    if request.path.startswith("/api/") and not request.path.startswith("/api/auth/"):
        token = request.cookies.get('jwt_token')
        if not token:
            return jsonify({'error': 'Não autorizado. Faça o login.'}), 401
        try:
            jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except Exception:
            return jsonify({'error': 'Sessão expirada ou inválida.'}), 401

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# Importando todas as rotas (Blueprints do Flask)
from app.routes.chatbot import chatbot_bp
from app.routes.marketing import marketing_bp
from app.routes.settings import settings_bp
from app.routes.analytics import analytics_bp
from app.routes.auth import auth_bp, limiter

# --- REGISTRO DOS MÓDULOS (BLUEPRINTS) ---
app.register_blueprint(chatbot_bp, url_prefix="/api/chat")
app.register_blueprint(marketing_bp, url_prefix="/api/marketing")
app.register_blueprint(settings_bp, url_prefix="/api/settings")
app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
app.register_blueprint(auth_bp, url_prefix="/api/auth")

# Inicializa o Limiter no app
limiter.init_app(app)

# --- ROTA RAIZ (Servir o Frontend em React) ---
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react_app(path):
    """
    Serve a aplicação React (SPA).
    Qualquer rota que não seja /api/... vai retornar o index.html do React.
    """
    # Evitar conflito com rotas de API
    if path.startswith("api/"):
        return jsonify({"error": "Endpoint não encontrado"}), 404
        
    # Flask servirá arquivos estáticos automaticamente se existirem no static_folder
    # Se chegarmos aqui, é uma rota virtual do React ou um arquivo inexistente
    return send_from_directory(app.static_folder, "index.html")

@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint para monitoramento de infraestrutura"""
    return jsonify({"status": "online", "system": settings.APP_NAME, "version": settings.APP_VERSION})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=settings.DEBUG)