from flask import Blueprint, jsonify, request
from datetime import datetime
from bson import ObjectId
from app.services.marketing_service import gerar_inteligencia_marketing
from app.core.database import get_mongo_client
from app.core.config import settings

marketing_bp = Blueprint('marketing', __name__)

@marketing_bp.route("", methods=["GET"])
@marketing_bp.route("/", methods=["GET"])
def get_ofertas():
    try:
        mongo_client = get_mongo_client()
        db = mongo_client[settings.MONGO_DB_NAME or "Oncinha"]
        collection = db[settings.MONGO_COLLECTION_NAME or "ofertas_ia"]
        
        ofertas_cursor = collection.find().sort("timestamp", -1).limit(20)
        ofertas = []
        for oferta in ofertas_cursor:
            oferta['_id'] = str(oferta['_id'])
            ofertas.append(oferta)
            
        return jsonify(ofertas), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@marketing_bp.route("/<oferta_id>", methods=["PUT"])
def update_oferta(oferta_id):
    try:
        mongo_client = get_mongo_client()
        db = mongo_client[settings.MONGO_DB_NAME or "Oncinha"]
        collection = db[settings.MONGO_COLLECTION_NAME or "ofertas_ia"]
        
        data = request.json
        # Only update the fields that we want to allow editing (e.g., 'frases')
        update_data = {}
        if 'frases' in data:
            update_data['frases'] = data['frases']
            
        if update_data:
            collection.update_one({"_id": ObjectId(oferta_id)}, {"$set": update_data})
            
        return jsonify({"message": "Oferta atualizada com sucesso!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@marketing_bp.route("", methods=["POST"])
@marketing_bp.route("/", methods=["POST"])
def create_oferta():
    try:
        mongo_client = get_mongo_client()
        db = mongo_client[settings.MONGO_DB_NAME or "Oncinha"]
        collection = db[settings.MONGO_COLLECTION_NAME or "ofertas_ia"]
        
        data = request.json
        data['timestamp'] = datetime.utcnow()
        result = collection.insert_one(data)
        data['_id'] = str(result.inserted_id)
        return jsonify(data), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@marketing_bp.route("/refresh-ai", methods=["POST"])
def atualizar_marketing():
    sucesso = gerar_inteligencia_marketing("Taboão da Serra")
    if sucesso:
        return jsonify({"message": "IA atualizada com sucesso!"})
    return jsonify({"error": "Erro ao atualizar a IA. Verifique as credenciais e tente novamente."}), 500