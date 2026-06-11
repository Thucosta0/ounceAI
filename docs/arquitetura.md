# Arquitetura e Stacks do Projeto OunceAI

O projeto OunceAI é um sistema de monitoramento de inventário inteligente para mini-mercados autônomos (SmartShelf), com recursos de marketing gerados por Inteligência Artificial.

## ⚙️ Backend (Servidor e API)
- **Linguagem Principal:** Python 3.11
- **Framework Web:** Flask (utilizado para gerenciar rotas da API e servir os arquivos estáticos do frontend).
- **Conexão Relacional:** psycopg2 (Driver para conexão direta e performática com o banco PostgreSQL).
- **Conexão NoSQL:** PyMongo (Para acesso ao banco MongoDB).
- **Inteligência Artificial:** Google Generative AI (Gemini 3.1 Flash Lite) utilizado para processamento do Chatbot e geração de ofertas/frases de marketing.

## 🎨 Frontend (Interface do Usuário)
- **Biblioteca Base:** React 19
- **Build Tool:** Vite (substitui ferramentas mais antigas como Webpack/CRA para garantir builds ultrarrápidos).
- **Estilização:** Tailwind CSS 4 (Framework de classes utilitárias para design responsivo e moderno).
- **Roteamento:** React Router DOM (Gerencia a navegação SPA entre Dashboard, Ofertas e Chat).
- **Ícones:** Lucide React.

## 🗄️ Bancos de Dados
- **PostgreSQL (Local):** Banco de dados relacional que armazena os Produtos (nome, código de barras, peso) e o controle de estoque em tempo real.
- **MongoDB:** Banco de dados NoSQL utilizado para salvar registros de interações (Logs) e o histórico de Ofertas de Marketing geradas pela IA.

## 🚀 Infraestrutura & DevOps
- **Containerização:** Docker e Docker Compose (Build multi-stage separando a compilação do Node.js e o runtime do Python).
- **Servidor Web / Proxy Reverso:** Nginx (Gerencia o tráfego do subdomínio e encaminha para o container Flask na porta 8000).
- **Segurança HTTPS:** Certbot / Let's Encrypt (Fornece certificados SSL válidos e gratuitos).
- **Autenticação:** Proteção via HTTP Basic Auth nativa no Flask para todo o painel, exigindo usuário e senha antes do carregamento.
- **Hospedagem:** Servidor VPS KingHost.

## 📌 Histórico de Evolução
- **Otimização Recente:** O projeto inicialmente possuía módulos pesados de Visão Computacional (OpenCV, YOLO, PyTorch). Estes foram removidos da base de código para focar a aplicação exclusivamente em gerenciamento web, painel administrativo e integrações via IA, resultando em um servidor muito mais leve e rápido.
