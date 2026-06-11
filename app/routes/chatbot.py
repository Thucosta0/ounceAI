from flask import Blueprint, request, jsonify
from app.services.ai_engine import gerar_resposta_gepeteco

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route("", methods=["POST"])
@chatbot_bp.route("/", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({"error": "Mensagem não fornecida."}), 400
        
    resposta = gerar_resposta_gepeteco(user_message)
    return jsonify({"response": resposta})