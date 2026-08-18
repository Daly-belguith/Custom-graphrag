# Custom GraphRAG Platform
**Built by [@Daly-belguith](https://github.com/Daly-belguith)**

Welcome to the **Custom GraphRAG Platform**! This project transforms the original Microsoft GraphRAG CLI tool into a fully standalone, Dockerized, multi-tenant API platform with a modern, glassmorphic UI.

## What's Inside?

We took the core Knowledge Graph capabilities of GraphRAG and wrapped them in a production-ready web platform.

### Core Features
* **Per-User Index Isolation**: Total privacy. User A's documents, Knowledge Graphs, and queries are strictly isolated from User B's.
* **Role-Based Access Control (RBAC)**: Supports `superadmin` and `user` roles.
* **Dual Authentication**: Session-based JWTs for the Frontend, and unique, regeneratable API Keys for REST API access.
* **AI Chat**: A multi-turn conversational interface that queries your Knowledge Graph directly.
* **Superadmin Dashboard**: Live Usage tracking, User CRUD, Prompt editing, and dynamic Environment/LLM settings via the UI.
* **100% Azure Decoupled**: Runs entirely on local files and LanceDB vector storage. Deploys anywhere Docker runs.

---

## 🚀 Quick Start Deployment

Deploy the platform on your local machine or a VPS in minutes.

1. **Clone the repo**
   ```bash
   git clone https://github.com/Daly-belguith/Custom-graphrag.git
   cd Custom-graphrag
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Open .env and insert your API keys (e.g. GRAPHRAG_API_KEY)
   ```

3. **Spin up with Docker Compose**
   ```bash
   docker-compose up --build -d
   ```

4. **Access the Platform**
   * Open `http://localhost:8000` in your browser.
   * Default Login: `admin` / `admin123`

---

## 📖 Walkthrough & Implementation Details

Here is a breakdown of the massive transformation that makes up this platform:

### 1. Decoupling and Architecture Cleanup
- **Azure Dependencies Removed:** All `azure-*` packages were stripped from the `pyproject.toml` files across the workspace. We made Azure imports "lazy", so they are only required if a user specifically configures `AzureManagedIdentity`.
- **Public PyPI Support:** The internal Microsoft package feed proxy was removed from the root `pyproject.toml`, allowing the project to build cleanly from public PyPI.

### 2. Authentication & Database Engine
- **SQLite + SQLAlchemy (`api_service/auth/`):** A robust, thread-safe database connection was implemented, saving to `data/graphrag_auth.db`.
- **RBAC (Role-Based Access Control):** Two roles were introduced:
  - `user`: Standard access restricted to their own documents and queries.
  - `superadmin`: God-mode access to all users, settings, and prompts.

### 3. The FastAPI Backend (`api_service/`)
A massive modular API was built with 14 distinct router files:
- **Documents & Indexing:** `POST /documents/upload` and `POST /indexing/start`. The system enforces **Per-User Index Isolation** — each user's files and Parquet graphs are segregated into `input/users/{user_id}` and `output/users/{user_id}`.
- **Query Engine:** Endpoints for Local, Global, Drift, and Basic search methods.
- **Usage & Rate Limiting:** All queries log token consumption and latency to the database. A sliding-window Rate Limiter middleware restricts requests per IP.
- **Settings & Prompts (Admin):** Superadmins can change the LLM Provider (OpenAI/DeepSeek/OpenRouter) dynamically via UI, edit `.env` variables, and modify the 13 core GraphRAG system prompts.

### 4. Modern Frontend SPA (`frontend/`)
We built a beautiful, Vanilla JS + CSS Single Page Application (SPA) utilizing a **Glassmorphism** dark mode aesthetic.
- **Interactive Tabbing:** Smooth navigation between My Documents, AI Chat, Search Playground, Graph Explorer, and API Tokens.
- **Superadmin Dashboard:** Exclusive tabs for User Management, System Usage Charts, Environment Config, Prompt Editing, and a Swagger Docs iframe.
- **Markdown & Code:** The AI Chat and Search results use `marked.js` and `highlight.js` to render beautiful responses with syntax highlighting.

---

## 📚 Further Reading

For a deeper dive into configuring different LLM Providers (DeepSeek, OpenRouter, Ollama) and understanding the architecture differences between Vector RAG and GraphRAG, check out the [GRAPHRAG_GUIDE.md](GRAPHRAG_GUIDE.md).

---
*Powered by [GraphRAG](https://github.com/microsoft/graphrag)*
