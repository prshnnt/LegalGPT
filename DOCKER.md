# Docker Deployment Guide for LegalGPT

This guide explains how to build, run, and manage the containerized LegalGPT application stack.

---

## Architecture Overview

| Service | Technology | Container Port | Host Port | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **`backend`** | FastAPI, Uvicorn, Python 3.12 | `8000` | `8000` | Core AI legal assistant API, ChromaDB vector store, auth & chat endpoints |
| **`frontend`** | React, Vite, Nginx | `80` | `3000` | Primary React web chat application |
| **`svelte-frontend`** | Svelte 5, Vite, Nginx | `80` | `5173` | Svelte-based alternative chat interface |

---

## Prerequisites

1. **Docker Desktop** installed and running on your system.
2. An environment file at `backend/.env` containing your LLM and API keys (copy from `backend/.env.example` if not already set).

---

## Quick Start (Production Mode)

To build and start all three services together:

```bash
docker compose up --build -d
```

### Accessing the Services
- **React Frontend**: [http://localhost:3000](http://localhost:3000)
- **Svelte Frontend**: [http://localhost:5173](http://localhost:5173)
- **FastAPI Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### Stopping the Services

```bash
docker compose down
```

To stop and remove associated volumes (resets vector DB & state):
```bash
docker compose down -v
```

---

## Development Mode (Live Hot-Reload)

To run the stack with local source files mounted for instant hot-reloading:

```bash
docker compose -f docker-compose.dev.yml up
```

Any code changes made in `backend/`, `frontend/`, or `svelte-frontend/` will reflect immediately inside the containers.

---

## Running Individual Services

### 1. Backend Service

```bash
# Build
docker build -t legalgpt-backend ./backend

# Run with environment variables
docker run -d \
  --name legalgpt-backend \
  -p 8000:8000 \
  --env-file ./backend/.env \
  -v chroma_data:/app/chroma_db \
  legalgpt-backend
```

### 2. React Frontend

```bash
# Build
docker build -t legalgpt-frontend-react ./frontend

# Run
docker run -d \
  --name legalgpt-frontend-react \
  -p 3000:80 \
  legalgpt-frontend-react
```

### 3. Svelte Frontend

```bash
# Build
docker build -t legalgpt-frontend-svelte ./svelte-frontend

# Run
docker run -d \
  --name legalgpt-frontend-svelte \
  -p 5173:80 \
  legalgpt-frontend-svelte
```

---

## Configuration & Environment Variables

The backend automatically picks up values from `backend/.env`. Supported configurations include:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PORT` | API listener port | `8000` |
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite://` (in-memory) |
| `CHROMA_PERSIST_DIR` | Directory for persisted ChromaDB vector store | `/app/chroma_db` |
| `GEMINI_API_KEY` | Google Gemini API Key | Optional |
| `GROQ_API_KEY` | Groq API Key | Optional |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | Optional |
| `TAVILY_API_KEY` | Tavily Search API Key | Optional |
| `OLLAMA_BASE_URL` | Ollama service endpoint | `https://api.ollama.com/` |
| `VITE_API_BASE_URL` | API endpoint used by frontends | `http://localhost:8000` |

---

## Volumes & Persistence

- **`chroma_data`**: Persists legal embeddings and ChromaDB vector index across container restarts.
- **`backend_data`**: Stores local database files and document datasets.
