from flask import Blueprint, request, jsonify, make_response
import jwt
import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from app.core.database import _get_connection
import os
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

auth_bp = Blueprint('auth', __name__)

# Configuração de Rate Limiting para evitar força bruta
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Secret key for JWT
JWT_SECRET = os.environ.get("JWT_SECRET", "super-secret-key-change-in-production")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('jwt_token')
        if not token:
            return jsonify({'message': 'Token está faltando!'}), 401
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            current_user = data['username']
        except Exception as e:
            return jsonify({'message': 'Token é inválido ou expirou!'}), 401
        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # Limite rigoroso apenas para o login
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Credenciais inválidas'}), 401

    username = data.get('username')
    password = data.get('password')

    conn = _get_connection()
    if not conn:
        return jsonify({'message': 'Erro de conexão com o banco de dados'}), 500

    try:
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users_ounceai WHERE username = %s", (username,))
        result = cur.fetchone()
        
        if result and check_password_hash(result[0], password):
            token = jwt.encode({
                'username': username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=12)
            }, JWT_SECRET, algorithm="HS256")
            
            resp = make_response(jsonify({'message': 'Login realizado com sucesso'}))
            # Set HttpOnly cookie to prevent XSS attacks
            resp.set_cookie(
                'jwt_token', 
                token, 
                httponly=True, 
                secure=True, 
                samesite='Strict',
                max_age=12*60*60
            )
            return resp
        else:
            return jsonify({'message': 'Usuário ou senha incorretos'}), 401
    except Exception as e:
        return jsonify({'message': f'Erro interno: {str(e)}'}), 500
    finally:
        conn.close()

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Credenciais inválidas'}), 400

    username = data.get('username')
    password = data.get('password')

    conn = _get_connection()
    if not conn:
        return jsonify({'message': 'Erro de conexão com o banco de dados'}), 500

    try:
        cur = conn.cursor()
        
        # Verifica se usuário já existe
        cur.execute("SELECT id FROM users_ounceai WHERE username = %s", (username,))
        if cur.fetchone():
            return jsonify({'message': 'Nome de usuário já está em uso.'}), 409

        # Insere novo usuário com hash da senha
        hashed_password = generate_password_hash(password, method='scrypt')
        cur.execute("INSERT INTO users_ounceai (username, password_hash) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()

        return jsonify({'message': 'Usuário cadastrado com sucesso!'}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'Erro ao registrar: {str(e)}'}), 500
    finally:
        conn.close()

@auth_bp.route('/logout', methods=['POST'])
def logout():
    resp = make_response(jsonify({'message': 'Logout realizado com sucesso'}))
    resp.set_cookie('jwt_token', '', expires=0, httponly=True, secure=True, samesite='Strict')
    return resp

@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify():
    return jsonify({'status': 'authenticated'}), 200
