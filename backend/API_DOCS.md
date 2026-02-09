# LegalGPT API Documentation

## API Base URL
```
http://localhost:8000
```

## Authentication

All chat endpoints require Bearer token authentication.

### Headers
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

## Endpoints

### 1. Register User

**POST** `/auth/register`

Create a new user account.

**Request Body:**
```json
{
  "username": "lawyer1",
  "password": "secure123"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "username": "lawyer1",
  "created_at": "2024-02-08T10:00:00Z"
}
```

---

### 2. Login

**POST** `/auth/login`

Authenticate and receive access token.

**Request Body:**
```json
{
  "username": "lawyer1",
  "password": "secure123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 3. Create Chat Thread

**POST** `/chat/threads`

Create a new conversation thread.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "title": "IPC Section 420 Query"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "title": "IPC Section 420 Query",
  "created_at": "2024-02-08T10:00:00Z",
  "updated_at": "2024-02-08T10:00:00Z"
}
```

---

### 4. Get All Threads

**GET** `/chat/threads`

Retrieve all chat threads for the authenticated user.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "title": "IPC Section 420 Query",
    "created_at": "2024-02-08T10:00:00Z",
    "updated_at": "2024-02-08T10:00:00Z"
  },
  {
    "id": 2,
    "title": "Consumer Protection Act",
    "created_at": "2024-02-08T11:00:00Z",
    "updated_at": "2024-02-08T11:00:00Z"
  }
]
```

---

### 5. Get Thread with History

**GET** `/chat/threads/{thread_id}`

Get a specific thread with all messages.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "thread": {
    "id": 1,
    "title": "IPC Section 420 Query",
    "created_at": "2024-02-08T10:00:00Z",
    "updated_at": "2024-02-08T10:00:00Z"
  },
  "messages": [
    {
      "id": 1,
      "role": "human",
      "content": "What is Section 420 IPC?",
      "tool_name": null,
      "tool_data": null,
      "created_at": "2024-02-08T10:01:00Z"
    },
    {
      "id": 2,
      "role": "tool",
      "content": "{\"documents\": [...]}",
      "tool_name": "search_legal_documents",
      "tool_data": {"query": "Section 420 IPC"},
      "created_at": "2024-02-08T10:01:05Z"
    },
    {
      "id": 3,
      "role": "ai",
      "content": "Section 420 of the Indian Penal Code...",
      "tool_name": null,
      "tool_data": null,
      "created_at": "2024-02-08T10:01:10Z"
    }
  ]
}
```

---

### 6. Send Message (Streaming)

**POST** `/chat/threads/{thread_id}/messages`

Send a message and receive streaming AI response via Server-Sent Events (SSE).

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "content": "What are the provisions under Section 420 IPC?"
}
```

**Response:** `200 OK` (Server-Sent Events Stream)

Stream format:
```
event: message_start
data: {"role": "assistant"}

event: tool_use_start
data: {"tool_name": "search_legal_documents"}

event: tool_use_end
data: {"tool_name": "search_legal_documents", "result": {...}}

event: content_delta
data: {"text": "Section"}

event: content_delta
data: {"text": " 420"}

event: content_delta
data: {"text": " IPC"}

event: message_end
data: {"content": "Section 420 IPC deals with..."}
```

**Event Types:**

- `message_start`: AI starts responding
- `tool_use_start`: AI begins using a tool
- `tool_use_end`: Tool execution complete with result
- `content_delta`: Streaming text chunks
- `message_end`: Complete response with full content
- `error`: Error occurred

**JavaScript Client Example:**
```javascript
const eventSource = new EventSource(
  'http://localhost:8000/chat/threads/1/messages',
  {
    headers: {
      'Authorization': 'Bearer ' + token
    }
  }
);

eventSource.addEventListener('content_delta', (event) => {
  const data = JSON.parse(event.data);
  console.log('Chunk:', data.text);
});

eventSource.addEventListener('tool_use_start', (event) => {
  const data = JSON.parse(event.data);
  console.log('Tool:', data.tool_name);
});

eventSource.addEventListener('message_end', (event) => {
  const data = JSON.parse(event.data);
  console.log('Complete:', data.content);
  eventSource.close();
});
```

---

### 7. Get Thread Messages

**GET** `/chat/threads/{thread_id}/messages`

Get all messages in a thread.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "role": "human",
    "content": "What is Section 420 IPC?",
    "tool_name": null,
    "tool_data": null,
    "created_at": "2024-02-08T10:01:00Z"
  },
  {
    "id": 2,
    "role": "ai",
    "content": "Section 420 IPC deals with...",
    "tool_name": null,
    "tool_data": null,
    "created_at": "2024-02-08T10:01:10Z"
  }
]
```

---

### 8. Delete Thread

**DELETE** `/chat/threads/{thread_id}`

Delete a chat thread and all its messages.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** `204 No Content`

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Username already registered"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid authentication credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Chat thread not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting

Currently not implemented. Recommended for production:
- 100 requests per minute per user
- 10 concurrent streaming connections per user

---

## Tools Available to AI

### 1. search_legal_documents

Searches legal documents in ChromaDB vector store.

**Parameters:**
- `query` (string, required): Search query
- `max_results` (integer, optional): Max results (default: 5)

**Example:**
```json
{
  "query": "Section 420 IPC fraud cases",
  "max_results": 5
}
```

### 2. get_document_by_reference

Retrieves specific document by ID.

**Parameters:**
- `doc_id` (string, required): Document identifier

**Example:**
```json
{
  "doc_id": "ipc_420"
}
```

---

## Database Schema

See README.md for complete database schema.

---

## Notes

1. All timestamps are in UTC
2. Passwords are hashed using bcrypt
3. JWT tokens expire after 7 days (configurable)
4. All endpoints use JSON for request/response except streaming endpoint
5. Streaming uses Server-Sent Events (SSE) with `text/event-stream` content type
