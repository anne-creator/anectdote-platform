# API Endpoints Specification

**Backend**: Python FastAPI  
**Base URL**: `http://localhost:8000`  
**Auth**: Clerk JWT (verified via JWKS)  
**Version**: 1.0 (MVP)

---

## Authentication

All endpoints marked **Clerk JWT** require an `Authorization: Bearer <token>` header. The token is a Clerk session JWT obtained from the frontend via `useAuth().getToken()`.

The backend verifies the token by:
1. Fetching Clerk's JWKS from `https://<clerk-domain>/.well-known/jwks.json` (cached)
2. Verifying the JWT signature against the public key
3. Extracting `sub` claim as `user_id`

Unauthenticated requests to protected endpoints return `401 Unauthorized`.

---

## Endpoints Summary

| # | Method | Path | Auth | Description |
|---|--------|------|------|-------------|
| 1 | GET | `/api/health` | None | Health check |
| 2 | POST | `/api/webhooks/clerk` | Svix signature | Clerk user sync webhook |
| 3 | GET | `/api/users/me` | Clerk JWT | Get current user profile |
| 4 | GET | `/api/documents` | Clerk JWT | List user's documents |
| 5 | POST | `/api/documents` | Clerk JWT | Create a document |
| 6 | GET | `/api/documents/{document_id}` | Clerk JWT | Get a document |
| 7 | PATCH | `/api/documents/{document_id}` | Clerk JWT | Update a document |
| 8 | DELETE | `/api/documents/{document_id}` | Clerk JWT | Delete a document |

---

## 1. Health Check

```
GET /api/health
```

**Auth:** None

**Response `200`:**
```json
{
  "status": "ok"
}
```

---

## 2. Clerk Webhook

```
POST /api/webhooks/clerk
```

**Auth:** Svix webhook signature verification (headers: `svix-id`, `svix-timestamp`, `svix-signature`)

**Handled events:**

| Event | Action |
|-------|--------|
| `user.created` | INSERT into `users` table (user_id, user_email, display_name) |
| `user.updated` | UPDATE `users` SET user_email, display_name |
| `user.deleted` | DELETE from `users` (CASCADE removes documents) |

**Request body:** Clerk webhook payload (varies by event type)

**Response `200`:**
```json
{
  "status": "ok"
}
```

**Error `400`:** Invalid webhook signature

---

## 3. Get Current User

```
GET /api/users/me
```

**Auth:** Clerk JWT

**Response `200`:**
```json
{
  "user_id": "user_2abc...",
  "user_email": "researcher@university.edu",
  "display_name": "Jane Smith",
  "created_at": "2026-03-02T10:30:00Z"
}
```

**Error `404`:** User not found in database (webhook may not have fired yet)

---

## 4. List Documents

```
GET /api/documents
```

**Auth:** Clerk JWT

Returns all documents belonging to the authenticated user, ordered by `created_at` descending.

**Response `200`:**
```json
[
  {
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user_2abc...",
    "title": "Lab Data Dashboard",
    "project_description": "We need a dashboard to visualize...",
    "status": "draft",
    "created_at": "2026-03-02T10:30:00Z"
  }
]
```

Returns `[]` if the user has no documents.

---

## 5. Create Document

```
POST /api/documents
```

**Auth:** Clerk JWT

**Request body:**
```json
{
  "title": "Lab Data Dashboard",
  "project_description": "We need a dashboard to visualize our research data..."
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `title` | string | Yes | 1-255 characters |
| `project_description` | string | Yes | 1-5000 characters (~600 words) |

The `user_id` is set automatically from the JWT. The `status` defaults to `draft`.

**Response `201`:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_2abc...",
  "title": "Lab Data Dashboard",
  "project_description": "We need a dashboard to visualize our research data...",
  "status": "draft",
  "created_at": "2026-03-02T10:30:00Z"
}
```

**Error `422`:** Validation error (missing/invalid fields)

---

## 6. Get Document

```
GET /api/documents/{document_id}
```

**Auth:** Clerk JWT

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `document_id` | UUID | The document's unique ID |

**Response `200`:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_2abc...",
  "title": "Lab Data Dashboard",
  "project_description": "We need a dashboard to visualize our research data...",
  "status": "draft",
  "created_at": "2026-03-02T10:30:00Z"
}
```

**Error `404`:** Document not found or does not belong to the authenticated user

---

## 7. Update Document

```
PATCH /api/documents/{document_id}
```

**Auth:** Clerk JWT

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `document_id` | UUID | The document's unique ID |

**Request body** (all fields optional, at least one required):
```json
{
  "title": "Updated Dashboard Title",
  "project_description": "Updated description...",
  "status": "submitted"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `title` | string | No | 1-255 characters |
| `project_description` | string | No | 1-5000 characters |
| `status` | string | No | One of: `draft`, `submitted`, `in_review`, `completed` |

**Response `200`:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_2abc...",
  "title": "Updated Dashboard Title",
  "project_description": "Updated description...",
  "status": "submitted",
  "created_at": "2026-03-02T10:30:00Z"
}
```

**Error `404`:** Document not found or does not belong to the authenticated user  
**Error `422`:** Validation error

---

## 8. Delete Document

```
DELETE /api/documents/{document_id}
```

**Auth:** Clerk JWT

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `document_id` | UUID | The document's unique ID |

**Response `204`:** No content (successful deletion)

**Error `404`:** Document not found or does not belong to the authenticated user

---

## Error Response Format

All error responses follow a consistent format:

```json
{
  "detail": "Human-readable error message"
}
```

**Standard HTTP status codes:**

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Created |
| `204` | Deleted (no content) |
| `400` | Bad request (e.g., invalid webhook signature) |
| `401` | Unauthorized (missing/invalid JWT) |
| `403` | Forbidden (valid JWT but insufficient permissions) |
| `404` | Not found (or not owned by the user) |
| `422` | Validation error (invalid request body) |
| `500` | Internal server error |

---

## CORS Configuration

The FastAPI backend allows cross-origin requests from the frontend:

- **Allowed origins:** `http://localhost:3000` (dev), production frontend URL
- **Allowed methods:** GET, POST, PATCH, DELETE, OPTIONS
- **Allowed headers:** Authorization, Content-Type
- **Credentials:** true
