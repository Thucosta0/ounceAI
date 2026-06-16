import os
import re
import threading
import time
from flask import Blueprint, request, jsonify

settings_bp = Blueprint('settings', __name__)
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')

def read_env_var(key):
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    # Remove the key= part and any quotes
                    value = line[len(key)+1:].strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    return value
    except Exception as e:
        print(f"Erro lendo .env: {e}")
    return ""

def update_env_var(key, new_value):
    # Sanitização básica para evitar injeção de novas variáveis ou corrupção do .env
    if new_value:
        new_value = new_value.replace('\n', '').replace('\r', '').replace('"', "'")
        
    try:
        lines = []
        key_found = False
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        with open(env_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.strip().startswith(f"{key}="):
                    # Wrap the new value in quotes to be safe
                    f.write(f'{key}="{new_value}"\n')
                    key_found = True
                else:
                    f.write(line)
            
            # If the key didn't exist in the file, append it
            if not key_found:
                if lines and not lines[-1].endswith('\n'):
                    f.write('\n')
                f.write(f'{key}="{new_value}"\n')
        return True
    except Exception as e:
        print(f"Erro escrevendo .env: {e}")
        return False

def restart_server_delayed():
    """Restart the Flask app by exiting the process. Docker will bring it back up."""
    def restart():
        time.sleep(1.5)
        os._exit(0)
    threading.Thread(target=restart).start()

@settings_bp.route("", methods=["GET"])
@settings_bp.route("/", methods=["GET"])
def get_settings():
    gemini_key = read_env_var("GEMINI_KEY")
    # Para segurança básica visual, podemos mascarar um pouco a chave (se quiser)
    # Mas como já é autenticado, enviaremos normal
    return jsonify({
        "gemini_key": gemini_key
    }), 200

@settings_bp.route("", methods=["POST"])
@settings_bp.route("/", methods=["POST"])
def update_settings():
    data = request.json
    gemini_key = data.get("gemini_key")
    
    if gemini_key is not None:
        # Tenta atualizar o GEMINI_KEY e também a variável VITE que pode ser usada pelo front
        success1 = update_env_var("GEMINI_KEY", gemini_key)
        success2 = update_env_var("VITE_GEMINI_API_KEY", gemini_key)
        
        # Atualiza o ambiente em memória para ter efeito imediato sem reiniciar
        os.environ["GEMINI_KEY"] = gemini_key
        os.environ["VITE_GEMINI_API_KEY"] = gemini_key
        
        from app.core.config import settings
        settings.GEMINI_KEY = gemini_key
        
        if success1 or success2:
            return jsonify({"message": "Configuração salva com sucesso!"}), 200
        else:
            return jsonify({"error": "Falha ao gravar no arquivo .env"}), 500
    
    return jsonify({"error": "Nenhum dado fornecido"}), 400
