# LegalGPT API Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                    (React/Next.js/etc)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/SSE
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Server                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    API Routes                           │ │
│  │  - /auth/*  (Authentication)                           │ │
│  │  - /chat/*  (Chat Management & Streaming)             │ │
│  └──────────────┬────────────────┬────────────────────────┘ │
│                 │                │                           │
│                 ↓                ↓                           │
│  ┌──────────────────┐  ┌─────────────────────┐            │
│  │   Auth Service   │  │   Agent Service      │            │
│  │  - JWT tokens    │  │  - Claude API calls  │            │
│  │  - Password hash │  │  - Streaming SSE     │            │
│  └──────────────────┘  │  - Tool execution    │            │
│                        └──────────┬────────────┘            │
│                                   │                          │
│                                   ↓                          │
│                        ┌─────────────────────┐              │
│                        │   Legal Tools        │              │
│                        │  - Document search   │              │
│                        │  - Reference lookup  │              │
│                        └──────────┬───────────┘              │
└───────────────────────────────────┼──────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
         ┌──────────────────┐          ┌──────────────────┐
         │   PostgreSQL      │          │    ChromaDB      │
         │                   │          │                  │
         │  - Users          │          │  - Legal docs    │
         │  - ChatThreads    │          │  - Embeddings    │
         │  - ChatMessages   │          │  - Metadata      │
         │  - Checkpoints    │          │                  │
         └───────────────────┘          └──────────────────┘
                    ↑
                    │
         ┌──────────────────┐
         │  Anthropic API    │
         │   (Claude AI)     │
         └───────────────────┘
```

## Request Flow

### 1. User Authentication Flow

```
Frontend → POST /auth/register → API
                                   ↓
                          Hash password (bcrypt)
                                   ↓
                          Store in PostgreSQL
                                   ↓
                          Return user data

Frontend → POST /auth/login → API
                                ↓
                       Verify credentials
                                ↓
                       Generate JWT token
                                ↓
                       Return access_token
```

### 2. Chat Message Flow (Streaming)

```
Frontend → POST /chat/threads/{id}/messages
           + Authorization: Bearer <token>
           + Body: {"content": "user message"}
                                   ↓
                          Verify JWT token
                                   ↓
                          Get user from DB
                                   ↓
                    Verify thread ownership
                                   ↓
                    Save user message to DB
                                   ↓
                    Get conversation history
                                   ↓
        ┌─────────────────────────────────────┐
        │        Deep Agent Service            │
        │  1. Build message array              │
        │  2. Add system prompt                │
        │  3. Call Claude API (streaming)      │
        │  4. Process stream events            │
        └─────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ↓               ↓               ↓
    Text chunks    Tool calls      Message end
         │               │               │
         │               ↓               │
         │     Execute tool function     │
         │     (Search ChromaDB)         │
         │               │               │
         │     Save tool call to DB      │
         │               │               │
         └───────────────┴───────────────┘
                         │
                         ↓
             Stream SSE events to frontend:
               - message_start
               - content_delta (text chunks)
               - tool_use_start
               - tool_use_end
               - message_end
                         │
                         ↓
                Save AI response to DB
                         │
                         ↓
                Save checkpoint to DB
```

## Data Models

### User Model
```python
class User:
    id: int (PK)
    username: str (unique)
    hashed_password: str
    created_at: datetime
    
    # Relationships
    chat_threads: List[ChatThread]
```

### ChatThread Model
```python
class ChatThread:
    id: int (PK)
    user_id: int (FK)
    title: str
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    user: User
    messages: List[ChatMessage]
    checkpoints: List[ChatCheckpoint]
```

### ChatMessage Model
```python
class ChatMessage:
    id: int (PK)
    thread_id: int (FK)
    role: Enum[human, ai, tool]
    content: str
    tool_name: str (optional)
    tool_data: dict (optional, JSON)
    created_at: datetime
    
    # Relationships
    thread: ChatThread
```

### ChatCheckpoint Model
```python
class ChatCheckpoint:
    id: int (PK)
    thread_id: int (FK)
    checkpoint_data: dict (JSON)
    created_at: datetime
    
    # Relationships
    thread: ChatThread
```

## Component Responsibilities

### API Layer (`app/api/`)
- **auth.py**: User registration and login endpoints
- **chat.py**: Thread and message management, streaming
- **dependencies.py**: JWT verification and user authentication

### Core Layer (`app/core/`)
- **config.py**: Environment configuration and settings
- **auth.py**: Password hashing and JWT token utilities
- **prompts.py**: System prompts and memory management

### Database Layer (`app/db/`)
- **session.py**: Database connection and session management

### Models Layer (`app/models/`)
- **database.py**: SQLAlchemy ORM models

### Schemas Layer (`app/schemas/`)
- **chat.py**: Pydantic models for request/response validation

### Services Layer (`app/services/`)
- **agent.py**: DeepAgent integration and streaming logic
- **vector_store.py**: ChromaDB interface for document retrieval

### Tools Layer (`app/tools/`)
- **legal_tools.py**: Tool definitions and execution functions

## Security Considerations

### Authentication
- Passwords hashed with bcrypt (cost factor: 12)
- JWT tokens with HS256 algorithm
- Token expiry: 7 days (configurable)
- Bearer token authentication for all protected endpoints

### Authorization
- User ownership verification for all thread operations
- No cross-user data access
- Thread and message access control

### Data Protection
- Environment variables for sensitive data
- No hardcoded credentials
- SQL injection protection via SQLAlchemy ORM
- Input validation via Pydantic schemas

## Scalability Considerations

### Current Architecture
- Single server deployment
- Synchronous database operations
- In-memory session management

### Future Improvements
1. **Horizontal Scaling**
   - Load balancer
   - Multiple API instances
   - Shared Redis for session storage

2. **Database Optimization**
   - Connection pooling
   - Read replicas
   - Query optimization
   - Indexing strategy

3. **Caching Layer**
   - Redis for frequently accessed data
   - Response caching
   - Vector search result caching

4. **Async Operations**
   - Async database queries
   - Async ChromaDB calls
   - Task queue for background jobs

## Deployment Architecture

```
┌─────────────────────────────────────────┐
│              Load Balancer               │
└────────────┬────────────────────────────┘
             │
     ┌───────┴────────┐
     ↓                ↓
┌─────────┐      ┌─────────┐
│ API     │      │ API     │
│ Server 1│      │ Server 2│
└────┬────┘      └────┬────┘
     │                │
     └────────┬───────┘
              ↓
     ┌────────────────┐
     │   PostgreSQL   │
     │   (Primary)    │
     └────────────────┘
              │
     ┌────────┴────────┐
     ↓                 ↓
┌──────────┐    ┌──────────┐
│ Replica 1│    │ Replica 2│
└──────────┘    └──────────┘
```

## Monitoring and Logging

### Recommended Tools
- **Application Monitoring**: Sentry or Datadog
- **Logging**: ELK Stack or CloudWatch
- **Performance**: New Relic or AppDynamics
- **Uptime**: UptimeRobot or Pingdom

### Key Metrics
- Request latency
- Error rate
- Token usage (Anthropic API)
- Database query performance
- ChromaDB search latency
- Active connections
- Memory usage

## Environment Configuration

### Development
```
DEBUG=True
DATABASE_URL=postgresql://localhost:5432/legalgpt_dev
```

### Production
```
DEBUG=False
DATABASE_URL=postgresql://prod-host:5432/legalgpt
CORS_ORIGINS=https://yourdomain.com
```

## API Versioning Strategy

Current: No versioning (v1 implicit)

Future: URL-based versioning
```
/v1/auth/login
/v1/chat/threads
/v2/chat/threads (with new features)
```
