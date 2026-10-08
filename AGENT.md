# LegalGPT - Project Memory & Agent Operating Guide

> **NOTICE FOR AGENTS**: Read this file first before searching or scanning the workspace. Do **NOT** perform recursive, unconstrained full-workspace scans (e.g. `Get-ChildItem -Recurse` or broad grep across the root). Use the file map and targeted workflows documented below.

---

## 1. Project Overview

**LegalGPT** is an AI-powered legal assistant tailored for the Indian Legal System. It provides research, statutory references (IPC, CrPC, CPC, BNS, BSA, BNSS, Constitution of India, etc.), and case analysis.

### System Architecture
```
                         ┌───────────────────────────────────────────────┐
                         │               Client Frontends                │
                         │  - React + Vite (frontend/ :3000)             │
                         │  - Svelte 5 + Vite (svelte-frontend/ :5173)   │
                         └──────────────────────┬────────────────────────┘
                                                │ REST / SSE Streaming
                                                ▼
                         ┌───────────────────────────────────────────────┐
                         │            FastAPI Backend (:8000)            │
                         │  - Auth & Chat APIs (app/api/)                │
                         │  - Agent Orchestrator (app/services/agent.py) │
                         │  - ChromaDB Vector Store (vector_store.py)    │
                         │  - Web Search Tool (app/tools/)               │
                         └──────────────────────┬────────────────────────┘
                                                │
                                    ┌───────────┴───────────┐
                                    ▼                       ▼
                         ┌────────────────────┐   ┌────────────────────┐
                         │ Legal Data (JSON)  │   │ Legal Data (PDFs)  │
                         │ backend/data/json/ │   │ backend/data/pdfs/ │
                         └────────────────────┘   └────────────────────┘
```

---

## 2. Directory & File Index

### 📁 Root Configuration
| File | Purpose |
|------|---------|
| [`AGENT.md`](file:///d:/Workspace/LegalGPT/AGENT.md) | Agent memory, file index, and operational workflow guide |
| [`README.md`](file:///d:/Workspace/LegalGPT/README.md) | High-level project summary and quickstart |
| [`DOCKER.md`](file:///d:/Workspace/LegalGPT/DOCKER.md) | Docker Compose and deployment guide |
| [`docker-compose.yml`](file:///d:/Workspace/LegalGPT/docker-compose.yml) | Multi-container production deployment |
| [`docker-compose.dev.yml`](file:///d:/Workspace/LegalGPT/docker-compose.dev.yml) | Multi-container development with hot reload |
| [`.gitignore`](file:///d:/Workspace/LegalGPT/.gitignore) | Git ignore rules |

---

### 📁 `backend/` (FastAPI + LangChain + ChromaDB)
*Path: `d:\Workspace\LegalGPT\backend`*

#### Core Application Code:
- [`backend/main.py`](file:///d:/Workspace/LegalGPT/backend/main.py): FastAPI app entrypoint, CORS, router mounting, lifespan
- **API Endpoints (`backend/app/api/`)**:
  - [`chat.py`](file:///d:/Workspace/LegalGPT/backend/app/api/chat.py): Chat endpoints, query handling, streaming responses
  - [`auth.py`](file:///d:/Workspace/LegalGPT/backend/app/api/auth.py): Authentication, login, user registration
  - [`dependencies.py`](file:///d:/Workspace/LegalGPT/backend/app/api/dependencies.py): FastAPI dependency injection (DB sessions, current user)
- **Core & Config (`backend/app/core/`)**:
  - [`config.py`](file:///d:/Workspace/LegalGPT/backend/app/core/config.py): Pydantic settings, environment variables
  - [`auth.py`](file:///d:/Workspace/LegalGPT/backend/app/core/auth.py): JWT token creation and password hashing
- **Database & Models (`backend/app/db/`, `backend/app/models/`)**:
  - [`app/db/session.py`](file:///d:/Workspace/LegalGPT/backend/app/db/session.py): SQLAlchemy engine and sessionmaker
  - [`app/models/database.py`](file:///d:/Workspace/LegalGPT/backend/app/models/database.py): User and conversation SQL models
  - [`app/models/services.py`](file:///d:/Workspace/LegalGPT/backend/app/models/services.py): Internal data classes / helper models
  - [`app/schemas/chat.py`](file:///d:/Workspace/LegalGPT/backend/app/schemas/chat.py): Pydantic request/response schemas
- **Services & Agents (`backend/app/services/`)**:
  - [`agent.py`](file:///d:/Workspace/LegalGPT/backend/app/services/agent.py): LangGraph/LangChain agent reasoning loop, tool invocation
  - [`vector_store.py`](file:///d:/Workspace/LegalGPT/backend/app/services/vector_store.py): ChromaDB embeddings and similarity search
- **Tools & Prompts (`backend/app/tools/`, `backend/app/prompts/`)**:
  - [`app/tools/web_search_tool.py`](file:///d:/Workspace/LegalGPT/backend/app/tools/web_search_tool.py): Tavily / web search integration
  - [`app/prompts/SYSTEM_PROMPT.md`](file:///d:/Workspace/LegalGPT/backend/app/prompts/SYSTEM_PROMPT.md): System prompt for the legal reasoning model
  - [`app/prompts/SKILLS.md`](file:///d:/Workspace/LegalGPT/backend/app/prompts/SKILLS.md): Legal skills descriptions and operational constraints

#### Datasets & Corpora:
- **`backend/data/json/`**: Structured statutory sections (BNS, CrPC, CPC, IPC, Constitution of India, HMA, IDA, IEA, MVA, NIA, BSA)
- **`backend/data/pdfs/`**: Raw source Acts and official legal gazette documents

#### Configuration & Env:
- [`backend/pyproject.toml`](file:///d:/Workspace/LegalGPT/backend/pyproject.toml), [`requirements.txt`](file:///d:/Workspace/LegalGPT/backend/requirements.txt), [`Dockerfile`](file:///d:/Workspace/LegalGPT/backend/Dockerfile)

---

### 📁 `frontend/` (React 18 + Vite + Tailwind CSS + Radix UI)
*Path: `d:\Workspace\LegalGPT\frontend`*

- **Configuration**:
  - [`package.json`](file:///d:/Workspace/LegalGPT/frontend/package.json): Package name `legalgpt-frontend`, scripts (`dev`, `build`)
  - [`vite.config.ts`](file:///d:/Workspace/LegalGPT/frontend/vite.config.ts), [`postcss.config.mjs`](file:///d:/Workspace/LegalGPT/frontend/postcss.config.mjs)
  - [`Dockerfile`](file:///d:/Workspace/LegalGPT/frontend/Dockerfile), [`nginx.conf`](file:///d:/Workspace/LegalGPT/frontend/nginx.conf)
- **Entry & App**:
  - [`src/main.tsx`](file:///d:/Workspace/LegalGPT/frontend/src/main.tsx): React root mount
  - [`src/app/App.tsx`](file:///d:/Workspace/LegalGPT/frontend/src/app/App.tsx): Top-level state, layout, active conversation handling
- **Chat Components (`frontend/src/app/components/`)**:
  - [`ChatHeader.tsx`](file:///d:/Workspace/LegalGPT/frontend/src/app/components/ChatHeader.tsx): Top header bar with title and actions
  - [`ChatMessage.tsx`](file:///d:/Workspace/LegalGPT/frontend/src/app/components/ChatMessage.tsx): Markdown rendering, citation badges, bubble styles
  - [`MessageInput.tsx`](file:///d:/Workspace/LegalGPT/frontend/src/app/components/MessageInput.tsx): Query input box with send button and shortcuts
  - [`EmptyState.tsx`](file:///d:/Workspace/LegalGPT/frontend/src/app/components/EmptyState.tsx): Welcome hero and suggestion cards
  - [`Sidebar.tsx`](file:///d:/Workspace/LegalGPT/frontend/src/app/components/Sidebar.tsx): Chat history, conversation list, new chat button
  - [`AuthModal.tsx`](file:///d:/Workspace/LegalGPT/frontend/src/app/components/AuthModal.tsx): Login / Sign-up dialog
  - [`ThinkingIndicator.tsx`](file:///d:/Workspace/LegalGPT/frontend/src/app/components/ThinkingIndicator.tsx): Live streaming/thinking animation
- **UI Primitives (`frontend/src/app/components/ui/`)**:
  - Complete shadcn/Radix UI set: `button.tsx`, `dialog.tsx`, `card.tsx`, `input.tsx`, `dropdown-menu.tsx`, `tooltip.tsx`, `scroll-area.tsx`, etc.
- **Services & Types**:
  - [`src/app/services/api.ts`](file:///d:/Workspace/LegalGPT/frontend/src/app/services/api.ts): Backend API calls, SSE streaming reader
  - [`src/app/types/chat.ts`](file:///d:/Workspace/LegalGPT/frontend/src/app/types/chat.ts): Type definitions for messages, chats, user states
- **Styles (`frontend/src/styles/`)**:
  - `index.css`, `tailwind.css`, `theme.css`, `fonts.css`

---

### 📁 `svelte-frontend/` (Svelte 5 + Vite + TypeScript)
*Path: `d:\Workspace\LegalGPT\svelte-frontend`*

- **Configuration**:
  - [`package.json`](file:///d:/Workspace/LegalGPT/svelte-frontend/package.json), [`svelte.config.js`](file:///d:/Workspace/LegalGPT/svelte-frontend/svelte.config.js), [`vite.config.ts`](file:///d:/Workspace/LegalGPT/svelte-frontend/vite.config.ts)
  - [`Dockerfile`](file:///d:/Workspace/LegalGPT/svelte-frontend/Dockerfile), [`nginx.conf`](file:///d:/Workspace/LegalGPT/svelte-frontend/nginx.conf)
- **Components (`svelte-frontend/src/lib/components/`)**:
  - `ChatHeader.svelte`, `ChatMessage.svelte`, `MessageInput.svelte`, `EmptyState.svelte`, `Sidebar.svelte`, `AuthModal.svelte`, `ThinkingIndicator.svelte`
- **Services & Types (`svelte-frontend/src/lib/`)**:
  - `services/api.ts`, `types/chat.ts`

---

## 3. Strict Search & Workflow Rules for Agents

### 🚫 NEVER DO:
1. **Never run recursive scans across the root directory**:
   - Do NOT run `Get-ChildItem -Recurse` from `d:\Workspace\LegalGPT`.
   - Do NOT grep without filtering out `node_modules`, `.venv`, `.git`, `dist`, `.vite`.
2. **Never search repeatedly in multiple round-trips**:
   - Check this memory file first (`AGENT.md`). The files and locations are already mapped above!
   - Navigate straight to the relevant file using `view_file` or targeted `grep_search`.

### ✅ ALWAYS DO (One-Go Workflow):
1. **Identify the subsystem immediately**:
   - Backend logic? Go directly to `backend/app/...`
   - React UI? Go directly to `frontend/src/app/...`
   - Svelte UI? Go directly to `svelte-frontend/src/lib/...`
   - Configuration / Docker? Go directly to root config files (`docker-compose.yml`, `DOCKER.md`, etc.)
2. **If searching within a subsystem, target only its source folder**:
   - Searching frontend: set `SearchPath: d:\Workspace\LegalGPT\frontend\src`
   - Searching backend: set `SearchPath: d:\Workspace\LegalGPT\backend\app`
   - Searching svelte: set `SearchPath: d:\Workspace\LegalGPT\svelte-frontend\src`
3. **Always exclude dependency folders if searching repo-wide**:
   - Set `Includes: ["!**/node_modules/**", "!**/.venv/**", "!**/.git/**", "!**/dist/**"]`.

---

## 4. Common Developer Commands

| Subsystem | Development | Production Build / Run |
|-----------|-------------|------------------------|
| **Docker (All)** | `docker compose -f docker-compose.dev.yml up` | `docker compose up --build -d` |
| **Backend** | `uvicorn main:app --reload --port 8000` (in `backend/`) | `uvicorn main:app --host 0.0.0.0 --port 8000` |
| **React Frontend** | `npm.cmd run dev` (in `frontend/`) | `npm.cmd run build` |
| **Svelte Frontend**| `npm.cmd run dev` (in `svelte-frontend/`) | `npm.cmd run build` |
