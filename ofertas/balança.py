import requests
import time
import json

# --- CONFIGURAÇÕES UPSTASH ---
# Note que mudamos de /set/ para /get/ para recuperar os dados
UPSTASH_GET_URL = "https://neat-mackerel-90223.upstash.io/get/"
UPSTASH_TOKEN = "Bearer gQAAAAAAAWBvAAIncDIwOWZiYjEwMzIwZDE0OWRmYTI3ZjU2YjkzNDllNjlkZHAyOTAyMjM"

headers = {
    "Authorization": UPSTASH_TOKEN
}

def ler_upstash(chave):
    url = f"{UPSTASH_GET_URL}{chave}"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            dados = response.json()
            # O Upstash retorna um JSON tipo: {"result": "{\"id_equipamento\":\"shelf_01\",\"valor\":0.00}"}
            resultado_str = dados.get("result")
            if resultado_str:
                # Converte a string do resultado de volta para um dicionário Python
                return json.loads(resultado_str)
        return None
    except Exception as e:
        return f"Erro de conexão: {e}"

print("[SISTEMA] Iniciando leitura na nuvem (Upstash)... Pressione Ctrl+C para sair.\n")

try:
    while True:
        # Lê as duas chaves que o seu ESP32 está salvando
        dados_peso = ler_upstash("shelf_01_peso")
        dados_variacao = ler_upstash("shelf_01_variacao")

        print("--- DADOS RECEBIDOS DO UPSTASH ---")
        
        if dados_peso:
            print(f"Peso Atual   : {dados_peso.get('valor')} g")
        else:
            print("Peso Atual   : Nenhum dado encontrado.")
            
        if dados_variacao:
            print(f"Variação     : {dados_variacao.get('delta')} g")
        else:
            print("Variação     : Nenhum dado encontrado.")
            
        print("----------------------------------\n")
        
        # Pausa de 2 segundos para não estourar o limite de requisições gratuitas da API
        time.sleep(1)

except KeyboardInterrupt:
    print("\n[SISTEMA] Leitura encerrada pelo usuário.")