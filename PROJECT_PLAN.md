# GraphRAG Platform — Complete Transformation & Roadmap Plan

Transform **Custom GraphRAG** into a standalone, Dockerized, multi-tenant API platform with **Per-User Index Isolation**, Role-Based Access Control, Prompt Management, Usage Tracking, Graph Visualization, and an interactive Web Frontend.

---

## Architecture Decisions

* **Per-User Index Isolation**: Each user gets their own isolated knowledge graph, vectors, and cache:
  ```
  input/users/{user_id}/     # User's raw documents
  output/users/{user_id}/    # User's Parquet graph output & LanceDB vectors
  cache/users/{user_id}/     # User's indexing pipeline cache
  ```
* **Dual Authentication**: JWT tokens for frontend sessions + unique API keys for programmatic REST access.
* **Default Superadmin**: Auto-seeded on first boot (`admin` / `admin123`, configurable via `.env`).
* **Embedded Swagger Docs**: Served at `/docs` inside the frontend, requires login to interact.

---

## Roles & Access Control

### `superadmin`
* Full User CRUD: Create, update roles, reset passwords, delete users.
* Access all users' documents, indexes, and usage stats.
* Manage system prompts (view, edit, reset to default).
* Trigger indexing for any user. View global usage dashboard.
* Access Export Center, Graph Visualization for any user, and API Documentation.

### `user`
* Frontend login via username & password.
* Unique personal API key for programmatic REST access.
* Document management scoped strictly to their own files.
* Query execution against their own index only.
* View their own usage stats, notifications, and graph visualization.

---

## Core Objectives

### 1. Complete Azure Decoupling
* 100% removal of mandatory Azure dependencies from all `pyproject.toml` files.
* Lazy imports for optional Azure drivers (already completed).
* Remove Azure cognitive endpoint defaults from config.

### 2. Docker & Container Deployment
* `Dockerfile`: Multi-stage Python 3.11 build with GraphRAG + FastAPI + uvicorn.
* `docker-compose.yml`: Persistent volume mounts for `input/`, `output/`, `cache/`, `prompts/`, `data/`.
* `.env.example`: Template with all configurable variables (`JWT_SECRET`, `DEFAULT_ADMIN_PASSWORD`, `RATE_LIMIT_PER_MINUTE`, `GRAPHRAG_API_KEY`).
* Docker `HEALTHCHECK` using `/api/v1/health`.

### 3. FastAPI REST API Backend (`api_service/`)

#### Health & System
* `GET /api/v1/health`: Public health check (`status`, `version`, `uptime`).

#### Authentication & Login
* `POST /api/v1/auth/login`: Login → JWT + user info + role.
* `GET /api/v1/auth/me`: Current user profile & usage summary.

#### User Management (Superadmin Only)
* `GET /api/v1/users`: List all users with usage summaries.
* `POST /api/v1/users`: Create new user (auto-creates isolated directories).
* `GET /api/v1/users/{user_id}`: User details + stats.
* `PUT /api/v1/users/{user_id}`: Update role, status, or password.
* `DELETE /api/v1/users/{user_id}`: Delete user + their documents + index + logs.

#### API Token Management
* `GET /api/v1/tokens/my-token`: Get current user's API key.
* `POST /api/v1/tokens/regen`: Regenerate API key.

#### Scoped Document Management
* `POST /api/v1/documents/upload`: Upload file → `input/users/{user_id}/`.
* `GET /api/v1/documents`: List documents (user sees own; superadmin filters by `?user_id=`).
* `DELETE /api/v1/documents/{filename}`: Role-scoped delete.

#### Indexing Workflows & Notifications
* `POST /api/v1/indexing/start`: Trigger background indexing (user's own docs; superadmin can pass `?user_id=`).
* `GET /api/v1/indexing/status/{task_id}`: Poll live indexing status & logs.
* `GET /api/v1/notifications`: Fetch unread notifications (indexing completion alerts).
* `PUT /api/v1/notifications/{id}/read`: Mark notification as read.

#### Query Execution
* `POST /api/v1/query/local`: Local Search (user's own index).
* `POST /api/v1/query/global`: Global Map-Reduce Search.
* `POST /api/v1/query/drift`: Drift Search.
* `POST /api/v1/query/basic`: Basic vector similarity search.
* All queries log usage (tokens consumed, model, latency).

#### AI Chat (Conversational Interface)
* `POST /api/v1/chat`: Send a message in a conversation thread. The backend auto-selects the best search method (Local or Global) based on the query, retrieves context from the user's knowledge graph, and streams an LLM response.
* `GET /api/v1/chat/history`: Retrieve the user's conversation history (paginated).
* `DELETE /api/v1/chat/history`: Clear conversation history.
* Supports multi-turn context: previous messages in the thread are passed to the LLM for coherent follow-up answers.

#### Prompt Management (Superadmin Only)
* `GET /api/v1/prompts`: List all 13 system prompts with previews.
* `GET /api/v1/prompts/{name}`: Read full prompt content.
* `PUT /api/v1/prompts/{name}`: Update prompt text.
* `POST /api/v1/prompts/{name}/reset`: Reset prompt to original default.

#### LLM Provider Settings Management (Superadmin Only)
* `GET /api/v1/settings/llm`: Get current LLM provider configuration (completion model, embedding model, provider, api_base).
* `PUT /api/v1/settings/llm`: Update LLM provider settings. Supports switching between:
  * **OpenAI** (`model_provider: openai`, `model: gpt-4o-mini`)
  * **DeepSeek** (`model_provider: deepseek`, `api_base: https://api.deepseek.com/v1`)
  * **OpenRouter** (`model_provider: openrouter`, `api_base: https://openrouter.ai/api/v1`)
  * **Self-Hosted / Ollama** (`model_provider: openai`, `api_base: http://localhost:11434/v1`)
* `POST /api/v1/settings/llm/test`: Test connection to the configured LLM provider (sends a simple ping completion).
* Changes are written to `settings.yaml` and take effect immediately (no restart required).

#### Environment Configuration (Superadmin Only)
* `GET /api/v1/settings/env`: List all configurable environment variables with current values (secrets masked).
* `PUT /api/v1/settings/env`: Update environment variables. Writes to `.env` file. Supports:
  * `GRAPHRAG_API_KEY`: LLM provider API key.
  * `JWT_SECRET`: JWT signing secret.
  * `DEFAULT_ADMIN_PASSWORD`: Initial admin password.
  * `RATE_LIMIT_PER_MINUTE`: Per-user rate limit.
  * Custom variables.
* `POST /api/v1/settings/restart`: Graceful service restart to apply env changes that require it.

#### Usage Tracking & Rate Limiting
* `GET /api/v1/usage/me`: Current user's usage stats (queries, tokens, breakdown by model/search type).
* `GET /api/v1/usage/users/{user_id}`: Per-user stats (Superadmin only).
* `GET /api/v1/usage/global`: Platform-wide usage summary (Superadmin only).
* Per-user rate limiting (`RATE_LIMIT_PER_MINUTE` from `.env`) → `429 Too Many Requests`.

#### Graph Visualization
* `GET /api/v1/graph/entities`: Extracted entities from user's index.
* `GET /api/v1/graph/relationships`: Relationships (edges) from user's index.
* `GET /api/v1/graph/communities`: Community summaries with hierarchy levels.
* `GET /api/v1/graph/visualize`: JSON graph structure (`{ nodes, edges }`) for D3.js / Cytoscape.js rendering.

#### Export & Download
* `GET /api/v1/export/graph`: Full knowledge graph as JSON or GraphML.
* `GET /api/v1/export/entities`: Entities table as CSV.
* `GET /api/v1/export/relationships`: Relationships table as CSV.
* `GET /api/v1/export/communities`: Community reports as JSON.
* `GET /api/v1/export/query-history`: User's query history as CSV.

---

### 4. Interactive Web Frontend (`frontend/`)

#### Login View
* Modern login form (username & password). JWT stored in `localStorage`.

#### Regular User Tabs
* **AI Chat**: Full conversational chat interface. User types questions in natural language, the system retrieves context from their knowledge graph and streams an LLM-powered answer. Supports multi-turn conversations with chat history. Markdown rendering for responses with entity citations.
* **My Documents**: Drag-and-drop upload, file list, delete. Scoped to user's files only.
* **Search Playground**: Tabbed Local/Global/Drift/Basic search with markdown response rendering.
* **Graph Explorer**: Interactive D3.js / Cytoscape.js knowledge graph visualization.
* **My API Token**: View & copy unique API key. Regenerate button.
* **Notifications Bell**: Unread count badge. Indexing completion alerts.

#### Superadmin Tabs (all above plus)
* **User Management**: CRUD table, create user modal, role toggle, password reset, delete.
* **All Documents**: Browse and manage documents across all users.
* **Prompt Editor**: List prompts, in-page text editor, save, reset-to-default.
* **LLM Settings**: Provider selector dropdown (OpenAI / DeepSeek / OpenRouter / Custom), model name input, API base URL, "Test Connection" button with live status indicator.
* **Environment Config**: Editable key-value table for all `.env` variables (secrets masked with reveal toggle), save button, restart service button.
* **Usage Dashboard**: Charts showing per-user queries, token consumption, model breakdown.
* **System Indexer**: Trigger indexing for any user, live log stream, indexing history.
* **Export Center**: Download buttons for graph data, entities, relationships, communities, query history.
* **API Documentation**: Embedded Swagger UI (`/docs`) inside authenticated iframe.
