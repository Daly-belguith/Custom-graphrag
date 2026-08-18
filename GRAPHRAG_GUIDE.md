# GraphRAG Platform: Architecture, Features, & Deployment Guide

This guide provides a comprehensive overview of the **Custom GraphRAG Platform**, a massive transformation of the original Microsoft GraphRAG CLI tool into a standalone, multi-tenant, Dockerized API platform with a modern UI.

---

## 1. Project Transformation Phases

We executed a comprehensive 5-phase plan to transform the original codebase:

### Phase 1: Complete Azure Decoupling
* Stripped all `azure-*` packages from the dependencies across `graphrag-llm`, `graphrag-storage`, `graphrag-vectors`, and the root `pyproject.toml`.
* Made Azure imports "lazy" (loaded only at runtime if `AzureManagedIdentity` auth is specifically requested).
* Removed internal Microsoft package feed proxies so the project builds cleanly via public PyPI.

### Phase 2: Authentication Engine & Database
* Built a custom `api_service/auth` module using SQLite and SQLAlchemy.
* **Role-Based Access Control (RBAC):** Two user roles (`superadmin` and `user`).
* **Dual Auth System:** 
  * `JWT Tokens`: Used for frontend session persistence.
  * `API Keys`: Auto-generated keys for programmatic REST API access.
* Added Auto-seeding to generate the first superadmin account automatically on the first boot.

### Phase 3: Modular FastAPI Backend
Developed a robust FastAPI backend exposed on port `8000` with 14 functional router modules:
* **Per-User Index Isolation:** Each user's documents and Knowledge Graph data are heavily isolated inside `input/users/{user_id}/` and `output/users/{user_id}/`.
* **Query & Chat Endpoints:** Exposes Local, Global, Drift, and Basic search methods, along with an AI Chat endpoint that maintains multi-turn conversation history.
* **Admin Controls:** Endpoints for User CRUD, Usage Tracking, dynamic LLM Settings, Environment Configuration, and System Prompt Management.

### Phase 4: Docker & Environment Setup
* Containerized the platform with a multi-stage Python 3.11 `Dockerfile`.
* Built a `docker-compose.yml` with persistent volume mounts for `data/`, `input/`, `output/`, `cache/`, and `prompts/`.
* Added `.env.example` to centralize all configurations (JWT secrets, default passwords, rate limits, API keys).

### Phase 5: Modern Frontend Web Application
Built a premium Single Page Application (SPA) using HTML, Vanilla JS, and Vanilla CSS with a **Glassmorphism** dark mode aesthetic.
* **User Dashboard:** Drag-and-drop document upload, AI Chat playground, Graph Explorer, API Token management.
* **Superadmin Dashboard:** User CRUD table, Environment Config editor, Usage charts, and embedded Swagger API docs.

---

## 2. Multi-LLM Provider Configuration

The platform uses **LiteLLM** under the hood, making it natively compatible with OpenAI, DeepSeek, OpenRouter, Anthropic, Ollama, and custom endpoints.

Superadmins can change the LLM provider dynamically via the Frontend UI (**Settings -> LLM Provider**), or manually configure it.

### OpenAI Example
```yaml
completion_models:
  default_completion_model:
    model_provider: openai
    model: gpt-4o-mini
    api_key: ${GRAPHRAG_API_KEY}
```

### DeepSeek API Example
```yaml
completion_models:
  default_completion_model:
    model_provider: deepseek
    model: deepseek-chat
    api_base: https://api.deepseek.com/v1
    api_key: ${GRAPHRAG_API_KEY}
```

### OpenRouter Example
```yaml
completion_models:
  default_completion_model:
    model_provider: openrouter
    model: deepseek/deepseek-chat
    api_base: https://openrouter.ai/api/v1
    api_key: ${GRAPHRAG_API_KEY}
```

---

## 3. How to Deploy the Platform

Because we decoupled all Azure dependencies, the GraphRAG Platform runs on any standard VPS (Ubuntu/Debian, DigitalOcean, AWS EC2, Hetzner, etc.) using Docker.

### 1. Clone & Configure
```bash
git clone https://github.com/Daly-belguith/Custom-graphrag.git
cd Custom-graphrag

# Copy the environment template
cp .env.example .env

# Edit .env and add your LLM API Keys and secure the JWT_SECRET
nano .env
```

### 2. Start the Platform
Run the platform in detached mode:
```bash
docker-compose up --build -d
```

### 3. Access the UI
Open your browser and navigate to your server's IP address on port `8000`:
* URL: `http://<your-vps-ip>:8000`
* Default Admin Login: `admin` / `admin123`

*(Make sure to change the admin password or create your personal account immediately after logging in).*

---

## 4. Platform API Documentation

The platform exposes a massive RESTful API. Once deployed, Superadmins can interact with the embedded **Swagger UI** inside the platform, or visit `/docs` directly.

### Core Endpoints

**Authentication & Users**
* `POST /api/v1/auth/login` - Authenticate and retrieve JWT.
* `GET /api/v1/auth/me` - Retrieve current user profile.
* `GET /api/v1/users` - List all users (Superadmin).
* `POST /api/v1/users` - Create a new user (Superadmin).

**Documents & Indexing**
* `POST /api/v1/documents/upload` - Upload a `.txt`/`.csv` file to the user's isolated directory.
* `POST /api/v1/indexing/start` - Trigger the background GraphRAG indexing pipeline.

**Queries & Chat**
* `POST /api/v1/chat` - Multi-turn conversational AI over the knowledge graph.
* `POST /api/v1/query/local` - Entity-focused neighborhood search.
* `POST /api/v1/query/global` - Map-Reduce holistic theme search.

*To authorize programmatic calls, pass the API Key in the headers:*
`Authorization: Bearer <your_api_key>`
