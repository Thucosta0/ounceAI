# app/core/database.py
import psycopg2
import requests
from typing import Optional
from pymongo import MongoClient
from app.core.config import settings

# --- HELPERS ---
def get_clima(cidade: str = "Taboão da Serra"):
    weather_key = settings.WEATHER_KEY
    if not weather_key: return "agradável"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={weather_key}&units=metric&lang=pt_br"
    try:
        # Timeout de 3 segundos para não travar o backend caso a API esteja lenta
        response = requests.get(url, timeout=3).json()
        if response.get("cod") != 200: return "agradável"
        return f"{response['weather'][0]['description']}, {response['main']['temp']}°C"
    except: return "agradável"

# --- POSTGRESQL (LOCAL) ---
def _get_connection():
    try:
        # print(f"DEBUG: Conectando ao Banco em {settings.DB_HOST}:{settings.DB_PORT} como {settings.DB_USER}")
        return psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            sslmode=settings.DB_SSLMODE
        )
    except psycopg2.OperationalError as e:
        print(f"⚠️ Erro ao conectar ao PostgreSQL no host '{settings.DB_HOST}': {e}")
        return None

# --- MONGODB  ---
def get_mongo_client():
    return MongoClient(settings.MONGO_URL)

