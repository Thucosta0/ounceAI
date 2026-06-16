from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URL = "mongodb+srv://dbOncinha:Expotech2026@cluster0.ydxsizd.mongodb.net/?retryWrites=true&w=majority"

try:
    client = MongoClient(MONGO_URL)
    db = client["Oncinha"]
    col = db["ofertas_ia"]
    print("✅ Ounce Stock: Conectado ao MongoDB")
except Exception as e:
    print(f"❌ Erro: {e}")

@app.get("/api/frase/{produto_id}")
@app.get("/api/frases/{produto_id}")
async def get_frases(produto_id: int):
    try:
        # Busca pelo campo 'produto_id' que agora está preenchido como número
        doc = col.find_one({"produto_id": produto_id})
        if doc and "frases" in doc:
            return {"frases": doc["frases"]}
        return {"frases": ["OUNCE STOCK", "OFERTA DO DIA"]}
    except:
        return {"frases": ["SISTEMA EM MANUTENÇÃO"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3001)