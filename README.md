# LegalGPT - AI Legal Assistant for the Indian Legal System

LegalGPT is an intelligent assistant designed to assist with Indian legal research, statutes (IPC, CrPC, CPC, BNS, BSA, Constitution of India), and case analysis.

## Project Structure

- **[`backend/`](file:///d:/Workspace/LegalGPT/backend)**: FastAPI backend powered by LangChain, LangGraph, DeepAgents, and ChromaDB vector store.
- **[`frontend/`](file:///d:/Workspace/LegalGPT/frontend)**: React + Vite web application with modern chat UI and streaming responses.
- **[`svelte-frontend/`](file:///d:/Workspace/LegalGPT/svelte-frontend)**: Svelte 5 + Vite chat application interface.

## Docker Setup

To run all apps via Docker Compose:

```bash
docker compose up --build -d
```

- **React App**: http://localhost:3000
- **Svelte App**: http://localhost:5173
- **FastAPI Backend**: http://localhost:8000 (Swagger docs: http://localhost:8000/docs)

For detailed deployment options and development live-reload instructions, refer to **[`DOCKER.md`](file:///d:/Workspace/LegalGPT/DOCKER.md)**.