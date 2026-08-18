# GraphRAG: Architecture, Multi-LLM Configuration, & VPS Deployment Guide

This guide provides a comprehensive overview of the **Custom GraphRAG** project architecture, how it differs from traditional RAG systems, how to configure it for multiple LLM providers (**OpenAI, DeepSeek, OpenRouter**), and how to deploy it on any Virtual Private Server (VPS).

---

## 1. Project Content & Codebase Architecture

GraphRAG is a modular Knowledge-Graph-powered Retrieval-Augmented Generation system. It extracts entities, relationships, and claims from unstructured text, builds a multi-level Knowledge Graph, computes community summaries, and enables both global and local search querying.

### Key Packages (`packages/`)
* [`packages/graphrag`](file:///c:/Users/mab28/Desktop/graphRag/graphrag/packages/graphrag): Core orchestration engine. Manages document chunking, prompt tuning, indexing workflows, and query execution modes (Local, Global, Drift, Basic).
* [`packages/graphrag-llm`](file:///c:/Users/mab28/Desktop/graphRag/graphrag/packages/graphrag-llm): LLM abstraction layer powered by **LiteLLM**. Handles completion calls, embeddings, tokenization, rate-limiting, and retry logic.
* [`packages/graphrag-vectors`](file:///c:/Users/mab28/Desktop/graphRag/graphrag/packages/graphrag-vectors): Vector storage abstractions (uses **LanceDB** on local disk by default).
* [`packages/graphrag-storage`](file:///c:/Users/mab28/Desktop/graphRag/graphrag/packages/graphrag-storage): Data storage abstractions (defaults to local file storage under `input/`, `output/`, `cache/`).
* [`packages/graphrag-chunking`](file:///c:/Users/mab28/Desktop/graphRag/graphrag/packages/graphrag-chunking), `graphrag-input`, `graphrag-cache`, `graphrag-common`.

---

## 2. How GraphRAG Works

GraphRAG operates in a two-phase architecture:

```
[Raw Text Documents] ──> [1. Indexing Pipeline (Offline)] ──> [Knowledge Graph & Summaries] ──> [2. Query Pipeline (Online)]
```

### Phase 1: Indexing Pipeline (Offline)
1. **Document Chunking:** Input text files are split into configured token chunks.
2. **Entity & Relationship Extraction:** An LLM scans text chunks to extract entities (people, organizations, locations), relationships, and claim triples.
3. **Graph Construction:** Constructs a Knowledge Graph with entity nodes and relationship edges.
4. **Hierarchical Clustering (Leiden Algorithm):** Groups entities into multi-level hierarchical communities.
5. **Community Summarization:** An LLM generates detailed summaries for each community at each level of the hierarchy.
6. **Vector Embedding:** Text chunks and entity descriptions are vectorized and stored in LanceDB.

### Phase 2: Query Pipeline (Online)
* **Global Search:** Answers dataset-wide holistic questions (*"What are the overarching themes?"*) by running a **Map-Reduce** algorithm across hierarchical community summaries.
* **Local Search:** Answers specific entity queries (*"How does entity X relate to Y?"*) by combining vector search with Knowledge Graph neighborhood traversal.
* **Drift Search:** Combines global summaries with iterative local graph expansion for complex reasoning.
* **Basic Search:** Standard vector similarity search on raw text chunks.

---

## 3. Difference: GraphRAG vs. Standard RAG

| Feature | Standard (Vector) RAG | GraphRAG |
| :--- | :--- | :--- |
| **Data Representation** | Unstructured text chunks + Vector Embeddings. | Knowledge Graph (Nodes, Edges, Claims) + Hierarchical Community Summaries + Vector Embeddings. |
| **Holistic Queries**<br>*(e.g., "What are the main themes?")* | **Poor Performance:** Fetches top-$k$ isolated chunks based on keyword matching; misses dataset-wide synthesis. | **Excels:** Uses Map-Reduce over hierarchical community summaries (Global Search). |
| **Relationship Discovery**<br>*(e.g., "How is X connected to Y?")* | **Struggles:** Relies purely on semantic similarity, missing multi-step connections across chunks. | **Excels:** Traverses graph edges and claim triples connecting distant entities (Local/Drift Search). |
| **Indexing Cost** | Low (only requires embedding computation). | Higher upfront cost (LLM extraction of entities, graph building, and community summarization). |
| **Infrastructure Needs** | Vector Database + LLM. | Local Disk / File Storage + Vector DB (LanceDB) + LLM. |

---

## 4. Multi-LLM Provider Configuration

GraphRAG uses **LiteLLM** under the hood, making it natively compatible with OpenAI, DeepSeek, OpenRouter, Anthropic, Ollama, and custom OpenAI-compatible endpoints.

All configurations are defined in `settings.yaml` (or generated via `graphrag init`).

### 1. OpenAI Configuration
```yaml
completion_models:
  default_completion_model:
    model_provider: openai
    model: gpt-4o-mini
    api_key: ${OPENAI_API_KEY}

embedding_models:
  default_embedding_model:
    model_provider: openai
    model: text-embedding-3-small
    api_key: ${OPENAI_API_KEY}
```

### 2. DeepSeek API Configuration
```yaml
completion_models:
  default_completion_model:
    model_provider: deepseek
    model: deepseek-chat # or deepseek-reasoner
    api_base: https://api.deepseek.com/v1
    api_key: ${DEEPSEEK_API_KEY}

embedding_models:
  default_embedding_model:
    # DeepSeek does not provide embedding models; pair with OpenAI or local embeddings
    model_provider: openai
    model: text-embedding-3-small
    api_key: ${OPENAI_API_KEY}
```

### 3. OpenRouter Configuration
```yaml
completion_models:
  default_completion_model:
    model_provider: openrouter
    model: deepseek/deepseek-chat # or openai/gpt-4o-mini, anthropic/claude-3.5-sonnet
    api_base: https://openrouter.ai/api/v1
    api_key: ${OPENROUTER_API_KEY}

embedding_models:
  default_embedding_model:
    model_provider: openrouter
    model: openai/text-embedding-3-small
    api_base: https://openrouter.ai/api/v1
    api_key: ${OPENROUTER_API_KEY}
```

### 4. Self-Hosted / Local Endpoint Configuration (Ollama / vLLM / LM Studio)
```yaml
completion_models:
  default_completion_model:
    model_provider: openai
    model: llama3 # or mistral, etc.
    api_base: http://localhost:11434/v1
    api_key: unused
```

---

## 5. Deployment Guide for Any VPS

GraphRAG requires no proprietary cloud services (like Azure Blob or CosmosDB) and runs completely standalone on local files and local LanceDB.

### Step 1: Ensure Local File Storage (`settings.yaml`)
```yaml
input_storage:
  type: file
  base_dir: "input"

output_storage:
  type: file
  base_dir: "output"

cache:
  type: json
  storage:
    type: file
    base_dir: "cache"

vector_store:
  type: lancedb
  db_uri: "output/lancedb"
```

### Step 2: Docker Containerization (`Dockerfile`)
Create a `Dockerfile` in the root of your project:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager for fast setup
RUN pip install uv

# Copy project files
COPY . /app

# Install GraphRAG packages in editable mode
RUN uv pip install --system -e packages/graphrag \
    -e packages/graphrag-llm \
    -e packages/graphrag-storage \
    -e packages/graphrag-vectors

EXPOSE 8000

CMD ["python", "-m", "graphrag", "--help"]
```

### Step 3: Deployment Commands on VPS
On your Ubuntu/Linux VPS:

```bash
# 1. Clone your custom repository
git clone https://github.com/Daly-belguith/Custom-graphrag.git
cd Custom-graphrag

# 2. Build Docker Image
docker build -t custom-graphrag .

# 3. Run Indexing via Docker
docker run --rm -v $(pwd):/app custom-graphrag python -m graphrag index --root /app

# 4. Run Global Search Query via Docker
docker run --rm -v $(pwd):/app custom-graphrag python -m graphrag query --root /app --method global "What are the main themes?"
```
