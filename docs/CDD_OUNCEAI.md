# Cognitive Driven Development (CDD) - OunceAI

## 1. Introdução

Este documento detalha o design e a estrutura do **OunceAI** sob a perspectiva do **Cognitive Driven Development (CDD)**. O CDD é uma abordagem de engenharia de software que visa minimizar a **carga cognitiva** intrínseca necessária para que um desenvolvedor entenda, mantenha e evolua um código. 

O OunceAI é um sistema inteligente focado em **varejo autônomo (SmartShelves)**. Ele atua processando dados de inventário físico, eventos de auditoria e utilizando Inteligência Artificial (Google Gemini) para gerar insights analíticos e campanhas de marketing (neurovendas).

---

## 2. Princípios do CDD Aplicados no OunceAI

No OunceAI, buscamos aplicar o limite da capacidade de compreensão humana em cada componente (normalmente mensurado por ICPs - Intrinsic Complexity Points). As diretrizes centrais são:

1. **Separação Estrita de Responsabilidades:** Rotas (Routes) não processam lógicas pesadas; Serviços (Services) não sabem que estão rodando na web.
2. **Contexto Controlado:** Um arquivo deve fazer apenas o que seu nome propõe. (ex: `marketing_service.py` foca apenas em marketing).
3. **Mínimo Acoplamento de Bibliotecas:** Uso restrito a bibliotecas essenciais para evitar fadiga cognitiva de documentações extensas.

---

## 3. Análise Cognitiva da Arquitetura

O ecossistema é dividido em **Módulos Cognitivos Isolados**. Um engenheiro que trabalha no frontend não precisa entender o motor de IA, e o engenheiro de IA não precisa entender a árvore do React.

### 3.1. Backend (Python/Flask)

O backend possui uma carga cognitiva baixa, pois utiliza o padrão de **Blueprints (Rotas Modulares)** e **Camada de Serviço**.

* **ICP de Rotas (Routes):** Baixo (1 a 3 pontos).
  * Arquivos como `app/routes/marketing.py` ou `app/routes/analytics.py` têm apenas a responsabilidade de receber um JSON (ou Request), chamar a camada de serviço apropriada, e retornar um Response. Não há SQL bruto nestes arquivos, o que reduz drasticamente o esforço de leitura.

* **ICP de Serviços (Services):** Médio (4 a 6 pontos).
  * Aqui reside a regra de negócio. O `app/services/ai_engine.py` consolida os dados do banco (Postgres/Mongo) para alimentar o prompt do Gemini.
  * A complexidade aqui é justificada, mas isolada. Se houver uma falha no prompt da IA, o desenvolvedor sabe exatamente que precisa olhar apenas a pasta `services/`.

* **ICP de Core/Config:** Muito Baixo (1 ponto).
  * Arquivos puros de configuração (`config.py`) ou instanciamento de conexões (`database.py`). Não há ramificações (IFs) ou lógicas complexas.

### 3.2. Frontend (React/Vite)

O frontend foi desenhado para evitar o "Prop Drilling" (passagem excessiva de propriedades), que é um dos maiores vilões da carga cognitiva no React.

* **ICP de Páginas (Pages):** Médio (3 a 5 pontos).
  * Arquivos como `StrategicDashboard.jsx` ou `Ofertas.jsx`. Eles são responsáveis por buscar os dados (fetch) e orquestrar a exibição.
  * *Estratégia de Redução:* No `StrategicDashboard.jsx`, os gráficos ECharts poderiam inflar o arquivo, mas a sintaxe declarativa do ReactECharts mantém a estrutura visual limpa.

* **ICP de Componentes (Components):** Baixo (1 a 2 pontos).
  * `Chat.jsx` e `Layout.jsx` são componentes puros de interface, focados em UI/UX e gerenciamento de estado local. 

---

## 4. Fluxos de Dados (Data Flow) Simplificados

Para entender o sistema rapidamente, os fluxos de dados seguem uma linha reta:

### Fluxo A: Geração de Ofertas (Marketing)
1. **Frontend:** Usuário clica em "Gerar Novas Ofertas" em `Ofertas.jsx`.
2. **Rota:** `POST /api/marketing/refresh-ai` recebe a requisição (`marketing.py`).
3. **Serviço:** `gerar_inteligencia_marketing()` é acionado.
4. **Infraestrutura:** Busca produtos no PostgreSQL, busca clima atual, constrói prompt, chama API do Gemini e salva resultado no MongoDB.
5. **Retorno:** JSON de sucesso volta ao Frontend.

### Fluxo B: Chatbot Especialista
1. **Frontend:** Usuário digita dúvida no `Chat.jsx`.
2. **Rota:** `POST /api/chat` recebe a mensagem (`chatbot.py`).
3. **Serviço:** `gerar_resposta_gepeteco()` é acionado.
4. **Contexto (Cérebro):** O motor puxa dados de Vendas (SQL), Últimas Ofertas (NoSQL) e Arquitetura do sistema (`arquitetura.md`).
5. **Retorno:** Resposta gerada pela IA é devolvida à tela do usuário.

---

## 5. Práticas de Clean Code Adotadas

Para suportar o CDD, as seguintes práticas estão aplicadas na base de código atual:

- **DRY (Don't Repeat Yourself):** Rotas antigas com funcionalidades duplicadas (como o antigo `dashboard.py` e rotas secundárias no `chatbot.py`) foram extirpadas. Toda a inteligência do painel converge para o `analytics.py`.
- **Early Return:** Uso intenso de retornos antecipados em validações no backend, evitando "código em formato de flecha" (múltiplos IFs aninhados).
- **Sem Magia Negra (No Black Magic):** As conexões com os bancos são feitas de forma direta e declarativa, sem uso excessivo de ORMs complexos (como SQLAlchemy) quando consultas cruas do PostgreSQL (`psycopg2`) se provam mais eficientes e legíveis para a carga analítica.

---

## 6. Conclusão

A arquitetura do OunceAI baseada no CDD garante que o projeto seja **escalável humanamente**. Novos desenvolvedores podem ser integrados ao projeto compreendendo um módulo de cada vez, sem a necessidade de manter o sistema inteiro carregado em suas memórias de curto prazo. O design favorece a previsibilidade: o nome de uma pasta ou arquivo indica com precisão matemática o seu conteúdo e limite de responsabilidade.
