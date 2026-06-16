from pymongo import MongoClient

# 1. Configurações de Conexão
MONGO_URL = "mongodb+srv://dbOncinha:Expotech2026@cluster0.ydxsizd.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "Oncinha"
COLLECTION_NAME = "ofertas_ia"

def rodar_visor_terminal():
    try:
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        col = db[COLLECTION_NAME]
        
        # Testa a conexão
        client.admin.command('ping')
        print("✅ Conectado ao MongoDB Atlas!")
        print("-" * 40)

        # 2. Busca todos os documentos
        produtos = list(col.find({}, {"_id": 0}))

        if not produtos:
            print("⚠️ Nenhuma oferta encontrada no banco.")
            return

        # 3. Exibição formatada
        for item in produtos:
            nome_banco = item.get('produto', 'Sem Nome')
            frases = item.get('frases', [])

            # Identifica qual é o produto para o visor
            tipo = ""
            if "Coca-Cola" in nome_banco:
                tipo = "🥤 CATEGORIA: COCA-COLA"
            elif "Guaraná" in nome_banco:
                tipo = "🍏 CATEGORIA: GUARANÁ"
            else:
                tipo = "📦 CATEGORIA: OUTROS"

            print(f"{tipo}")
            print(f"Nome no Banco: {nome_banco}")
            print("Frases Cadastradas:")
            
            if frases:
                for i, frase in enumerate(frases, 1):
                    print(f"  {i}. {frase}")
            else:
                print("  (X) Nenhuma frase encontrada para este item.")
            
            print("-" * 40)

    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    rodar_visor_terminal()