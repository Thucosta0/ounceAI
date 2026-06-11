# 📁 Estrutura do Projeto OunceAI

## 🎯 Visão Geral

O projeto **OunceAI** é uma aplicação full-stack que combina um backend em **Python (Flask)** com um frontend em **React (Vite)**, containerizada com **Docker**. A aplicação fornece um dashboard de inteligência artificial com suporte a chatbot, analytics e marketing.

---

## 📂 Estrutura Completa de Arquivos

```text
OunceAI/
├── app/                          # Backend Python (Flask)
│   ├── main.py                   # Entrada principal da aplicação Flask
│   ├── core/                     # Configurações e conexões
│   │   ├── config.py             # Variáveis de configuração (BD, APIs)
│   │   └── database.py           # Conexões com PostgreSQL e MongoDB
│   ├── routes/                   # Endpoints da API
│   │   ├── analytics.py          # Rotas de análise de dados (Dashboard)
│   │   ├── chatbot.py            # Rotas do chatbot com IA
│   │   ├── marketing.py          # Rotas de marketing
│   │   └── settings.py           # Rotas de configurações
│   └── services/                 # Lógica de negócio
│       ├── ai_engine.py          # Motor de IA (Google Gemini)
│       └── marketing_service.py  # Serviço de marketing
│
├── docs/                         # Documentação
│   └── arquitetura.md            # Documentação da arquitetura
│
├── frontend/                     # Frontend React (Vite)
│   ├── package.json              # Dependências Node.js
│   ├── vite.config.js            # Configuração do build tool (Vite)
│   ├── eslint.config.js          # Regras de qualidade de código
│   ├── index.html                # Arquivo HTML principal
│   ├── public/                   # Arquivos estáticos públicos
│   ├── src/
│   │   ├── main.jsx              # Entrada do React
│   │   ├── App.jsx               # Componente raiz
│   │   ├── App.css               # Estilos globais
│   │   ├── index.css             # Reset CSS
│   │   ├── components/           # Componentes reutilizáveis
│   │   │   ├── Chat.jsx          # Componente do chat
│   │   │   └── Layout.jsx        # Layout principal (header, sidebar)
│   │   └── pages/                # Páginas da aplicação
│   │       ├── Configuracoes.jsx # Página de configurações
│   │       ├── Ofertas.jsx       # Página de ofertas
│   │       └── StrategicDashboard.jsx # Dashboard Estratégico (Home)
│
├── nginx/                        # Configurações de Servidor Web / Proxy
│   └── nginx.conf                # Configuração do Nginx
│
├── Dockerfile                    # Build para containerizar a app
├── docker-compose.yml            # Orquestração de containers (backend + frontend)
├── requirements.txt              # Dependências Python
├── ESTRUTURA_PROJETO.md          # Este documento com a árvore do projeto
├── .env                          # Variáveis de ambiente
├── .gitignore                    # Arquivos ignorados pelo Git
└── .dockerignore                 # Arquivos ignorados na build Docker
```

---

## 📋 Função de Cada Arquivo

### **Raiz do Projeto**

| Arquivo | Função |
|---------|--------|
| **Dockerfile** | Define como construir a imagem Docker da aplicação (build multi-stage: Node.js + Python) |
| **docker-compose.yml** | Orquestra containers (backend, frontend, banco de dados) |
| **requirements.txt** | Lista todas as dependências Python necessárias |
| **.env** | Armazena variáveis de ambiente sensíveis (credenciais, chaves de API) |
| **.gitignore** | Especifica arquivos/pastas que NÃO devem ser commitados no Git |
| **.dockerignore** | Especifica arquivos que não devem entrar na imagem Docker |
| **ESTRUTURA_PROJETO.md** | Mapa detalhado atualizado da arquitetura de diretórios |

### **Pasta `app/` - Backend Python**

#### `app/main.py`
- **Função**: Entrada principal da aplicação Flask
- **Responsabilidades**:
  - Inicializa a aplicação Flask
  - Configura CORS para permitir requisições do frontend
  - Implementa autenticação básica (Basic Auth)
  - Adiciona headers de segurança (X-Content-Type-Options, HSTS, etc.)
  - Importa e registra todos os blueprints (rotas essenciais)
  - Serve o frontend React compilado como arquivos estáticos

#### `app/core/config.py`
- **Função**: Centraliza todas as configurações da aplicação
- **Variáveis**:
  - `APP_NAME`, `APP_VERSION`, `DEBUG`
  - Credenciais do PostgreSQL
  - Credenciais do MongoDB
  - Chaves de APIs externas (Gemini, OpenWeather)
  - Usa `pydantic` para validação de dados

#### `app/core/database.py`
- **Função**: Gerencia todas as conexões com bancos de dados
- **Responsabilidades**:
  - Conexão com PostgreSQL
  - Conexão com MongoDB (para ofertas)
  - Função `get_clima()` para buscar clima via API OpenWeather
  - Helpers para operações comuns no banco

#### `app/routes/analytics.py`
- **Função**: Endpoints principais para análise de dados do painel central
- **Responsabilidades**: Alimentar os KPIs e gráficos do Dashboard Estratégico (`/api/analytics/stats`).

#### `app/routes/chatbot.py`
- **Função**: Endpoints do chatbot com IA
- **Responsabilidades**: Recebe mensagens do usuário via POST, aciona o motor de IA (Gemini) e retorna respostas contextualizadas.

#### `app/routes/marketing.py`
- **Função**: Endpoints para campanhas e estratégias de marketing
- **Responsabilidades**: Integração com o banco de dados (MongoDB) e com o motor de IA para criar e gerenciar frases dinâmicas de marketing (Neurovendas).

#### `app/routes/settings.py`
- **Função**: Endpoints para configurações da aplicação
- **Responsabilidades**: Salvar e recuperar chaves de API e preferências do usuário.

#### `app/services/ai_engine.py`
- **Função**: Motor central de inteligência artificial da aplicação
- **Responsabilidades**:
  - Integração com Google Gemini API
  - Construção de prompts complexos usando dados de clima, arquitetura, MongoDB e PostgreSQL (`get_contexto_ounce_ai`).

#### `app/services/marketing_service.py`
- **Função**: Lógica de geração de conteúdo publicitário (Neurovendas)
- **Responsabilidades**: Processamento em lote de frases promocionais usando a IA e baseadas nos produtos ativos.

---

### **Pasta `frontend/` - React (Vite)**

| Arquivo | Função |
|---------|--------|
| **package.json** | Define dependências Node.js, scripts (dev, build, lint) e versão do projeto |
| **vite.config.js** | Configuração do build tool Vite (otimização, assets, plugins) |
| **eslint.config.js** | Regras de lint e padronização do código JavaScript/React |
| **index.html** | Arquivo HTML raiz que carrega a aplicação React |

#### `src/main.jsx` & `src/App.jsx`
- **Função**: Ponto de entrada do React e Componente raiz da aplicação
- **Responsabilidades**: Configuração das rotas (React Router) e encapsulamento dos layouts principais.

#### `src/App.css` e `src/index.css`
- **Função**: Estilos globais e reset de CSS (TailwindCSS configurado).

#### `src/components/`
- **`Chat.jsx`**: Interface visual e integração front-end do assistente de IA.
- **`Layout.jsx`**: Layout estrutural principal (barra lateral de navegação e cabeçalho mobile).

#### `src/pages/`
- **`StrategicDashboard.jsx`**: Página principal da aplicação. Um painel executivo (BI) que consome os dados de analytics para exibir faturamento, gráficos de funil, impactos por categoria e matrizes de acurácia.
- **`Ofertas.jsx`**: Painel para geração e gerenciamento das frases de marketing criadas pela IA.
- **`Configuracoes.jsx`**: Tela para atualizar configurações sensíveis como chaves de API (Gemini).

---

### **Outras Pastas Importantes**

#### `docs/`
- **`arquitetura.md`**: Descrição profunda das decisões arquiteturais e design do ecossistema.

#### `nginx/`
- **`nginx.conf`**: Configuração do servidor web e proxy reverso responsável pelo tráfego HTTP.
