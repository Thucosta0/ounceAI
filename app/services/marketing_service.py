import datetime
import random
import json
from google import genai
from app.core.config import settings
from app.core.database import _get_connection, get_mongo_client, get_clima

# Inicializa o Gemini usando as configurações centralizadas
client = None
if settings.GEMINI_KEY: 
    client = genai.Client(api_key=settings.GEMINI_KEY)

def gerar_inteligencia_marketing(cidade: str):
    """Gera frases de neurovendas em lote e salva no MongoDB"""
    if not client:
        print("Erro: GEMINI_KEY não configurada no arquivo .env")
        return False
        
    clima_atual = get_clima(cidade)
    pacote_ofertas = []

    # 1. Busca produtos no PostgreSQL Local
    produtos_info = []
    conn = _get_connection()
    if not conn:
        return False
        
    try:
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id_sku, nome_produto, categoria FROM dim_produto")
        produtos = [(p['id_sku'], p['nome_produto'], p['categoria']) for p in cur.fetchall()]
        cur.close()
        conn.close()
        if not produtos:
            return False
        for p in produtos:
            produtos_info.append(f"- ID: {p[0]} | Nome: {p[1]} | Categoria: {p[2]}")
    except Exception as e:
        print(f"Erro ao buscar produtos para marketing: {e}")
        return False

    produtos_str = "\n".join(produtos_info)

    # 2. Gera frases para TODOS os produtos em uma única chamada (Batching)
    prompt = f"""# PERSONA
    Você é um Redator Publicitário Especialista em Neurovendas da OunceIA, focado em varejo de conveniência.
    # CONTEXTO
    - Localização: {cidade}
    - Clima Atual: {clima_atual}
    O cenário é um mini-mercado autônomo SmartShelf. O objetivo é conectar cada produto ao desejo atual do cliente.
    
    Aqui está a lista de produtos disponíveis no estoque:
    {produtos_str}

    # INSTRUÇÃO
    Para CADA produto da lista, crie 3 frases de marketing altamente persuasivas e curtas (máximo 15 palavras).
    Alterne apelos entre: clima atual, praticidade ou o prazer do consumo imediato.
    
    # FORMATO OBRIGATÓRIO
    Retorne EXATAMENTE um JSON válido no formato abaixo, sem formatação Markdown e sem blocos de código (```json).
    [
      {{"produto_id": 1, "frases": ["frase 1", "frase 2", "frase 3"]}},
      {{"produto_id": 2, "frases": ["frase 1", "frase 2", "frase 3"]}}
    ]
    """
    
    try:
        # Usamos o modelo atual e estável do Gemini
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        # Faz o parse do JSON retornado pelo Gemini
        respostas_json = json.loads(response.text)
        
        # Organiza o pacote associando com os nomes originais
        prod_map = {p[0]: p[1] for p in produtos}
        
        for item in respostas_json:
            p_id = item.get("produto_id")
            if p_id in prod_map:
                doc = {
                    "produto_id": p_id,
                    "nome": prod_map[p_id],
                    "contexto": {"clima": clima_atual, "cidade": cidade},
                    "frases": item.get("frases", []),
                    "timestamp": datetime.datetime.now()
                }
                pacote_ofertas.append(doc)
                
    except Exception as e:
        print(f"Erro ao processar lote no Gemini: {e}")
        return False

    # 3. Salva no MongoDB
    if pacote_ofertas:
        try:
            m_client = get_mongo_client()
            db = m_client[settings.MONGO_DB_NAME or "Oncinha"]
            col = db[settings.MONGO_COLLECTION_NAME or "ofertas_ia"]
            col.delete_many({"contexto.cidade": cidade})
            col.insert_many(pacote_ofertas)
            return True
        except Exception as db_e:
            print(f"Erro ao salvar no MongoDB: {db_e}")
            
    return False
