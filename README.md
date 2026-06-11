# OunceAI - Plataforma Bimodal de Prevenção de Perdas

Bem-vindo ao **OunceAI**, um ecossistema avançado de inteligência artificial e visão computacional desenhado para revolucionar o varejo. A plataforma atua ativamente na prevenção de perdas nas gôndolas e oferece inteligência de dados (analytics) em tempo real, gerando relatórios de acurácia, proteção de receita e gestão de estoque.

---

## 🚀 Principais Funcionalidades

- **Dashboard Estratégico (React + ECharts):** Visualização em tempo real das métricas da loja. Painéis interativos estilo Power BI com "Cross-Filtering", KPIs de Acurácia da IA, Divergências Fantasmas e Impacto Financeiro.
- **Autenticação Segura (JWT & HttpOnly Cookies):** Sistema blindado contra ataques XSS e CSRF. Controle de acesso robusto com criptografia Scrypt e proteção contra força bruta (Rate Limiting).
- **Inteligência Artificial (Google Gemini):** Assistente virtual integrado (Chatbot) e gerador de campanhas de Marketing Baseadas em Clima e sazonalidade.
- **Banco de Dados Poliglota:**
  - **PostgreSQL (OLAP/OLTP):** Para dados transacionais e armazenamento de auditorias no formato Star Schema (Arquitetura ELT in-database).
  - **MongoDB:** Para armazenamento flexível de prompts e campanhas dinâmicas geradas por IA.
- **DataOps e Automação:** Infraestrutura totalmente containerizada usando Docker e proxy reverso configurado com Nginx (HTTPS/SSL Ativado).

---

## 🛠️ Stack Tecnológica

**Frontend:**
- React 18 (Vite)
- Tailwind CSS
- React Router DOM
- ECharts (ReactECharts)
- Lucide React (Ícones)

**Backend:**
- Python 3.11 (Flask)
- Flask-Limiter (Proteção)
- PyJWT & Werkzeug (Segurança)
- Psycopg2 & PyMongo (Bancos de Dados)
- Google Generative AI (Gemini)

**Infraestrutura & DevOps:**
- Docker & Docker Compose
- Nginx (Proxy Reverso & GZIP)
- PostgreSQL
- Certbot (Let's Encrypt SSL)

---

## ⚙️ Como Executar Localmente

### 1. Pré-requisitos
- Docker e Docker Compose instalados.
- Chave da API do Google Gemini.
- Conta e Cluster no MongoDB Atlas (opcional, pode usar local).

### 2. Configuração do Ambiente (.env)
Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis principais (não compartilhe suas senhas em repositórios públicos):
```ini
DB_HOST="ounceai_postgres"
DB_PORT=5432
DB_NAME="ounceai_db"
DB_USER="seu_usuario"
DB_PASSWORD="sua_senha"
GEMINI_KEY="sua_chave_aqui"
MONGO_URL="sua_string_de_conexao"
```

### 3. Build e Deploy com Docker
Para construir a imagem do Frontend (React) e iniciar a API (Flask) e o Nginx:
```bash
docker-compose up -d --build
```
A aplicação estará disponível em `http://localhost` (ou porta `8080` dependendo do mapeamento).

### 4. Povoando o Banco de Dados (Mock Data)
Se for o seu primeiro acesso e você quiser visualizar o Dashboard com dados:
```bash
docker exec -it ounceai_lp_web_1 python populate_db.py
```
Isso irá gerar métricas ricas simulando milhares de eventos da IA.

---

## 🛡️ Contribuição e Avaliação (Expotech)

Este projeto foi desenvolvido focado nos critérios exigidos para o **Trabalho Multidisciplinar (Engenharia de Dados & Software)**. O sistema cumpre rigorosamente os pilares de Arquitetura OLAP/OLTP, Governança (LGPD/Segurança), Pipeline ETL/ELT in-database e Otimização de Performance Cloud (Nginx cache/compressão).

*Desenvolvido por Thucosta0.*
