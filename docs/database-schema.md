# Database Schema Specification

**Database**: Supabase PostgreSQL  
**Project URL**: `https://ebkouymlnspckprnotrv.supabase.co`  
**Version**: 1.0 (MVP)

---

## Entity Relationship

```
users (1) ────────< project_documents (many)
```

One user can have zero or more project documents. Each project document belongs to exactly one user.

---

## Tables

### users

Stores authenticated user records. The primary key (`user_id`) comes directly from Clerk's authentication response, ensuring a 1:1 mapping with the identity provider.


| Column         | Type         | Constraints           | Default        | Description                            |
| -------------- | ------------ | --------------------- | -------------- | -------------------------------------- |
| `user_id`      | VARCHAR(255) | PRIMARY KEY, NOT NULL | *(from Clerk)* | Clerk auth user ID                     |
| `user_email`   | VARCHAR(255) | NOT NULL, UNIQUE      |                | User email address                     |
| `display_name` | VARCHAR(255) |                       | NULL           | User display name (from Clerk profile) |
| `created_at`   | TIMESTAMPTZ  | NOT NULL              | `NOW()`        | Row creation timestamp (UTC)           |


**DDL:**

```sql
CREATE TABLE users (
    user_id      VARCHAR(255) PRIMARY KEY,
    user_email   VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(user_email);
```

### project_documents

Stores project description documents submitted by users. Each document is owned by exactly one user via a foreign key.


| Column                | Type         | Constraints           | Default             | Description                              |
| --------------------- | ------------ | --------------------- | ------------------- | ---------------------------------------- |
| `document_id`         | UUID         | PRIMARY KEY, NOT NULL | `gen_random_uuid()` | Globally unique document ID              |
| `user_id`             | VARCHAR(255) | NOT NULL, FK → users  |                     | Owning user's Clerk ID                   |
| `title`               | VARCHAR(255) | NOT NULL              |                     | Human-readable document title            |
| `project_description` | TEXT         | NOT NULL              |                     | Project description content (~600 words) |
| `status`              | VARCHAR(50)  | NOT NULL              | `'draft'`           | Workflow status                          |
| `created_at`          | TIMESTAMPTZ  | NOT NULL              | `NOW()`             | Row creation timestamp (UTC)             |


**Status values:** `draft` → `submitted` → `in_review` → `completed`

**DDL:**

```sql
CREATE TABLE project_documents (
    document_id         UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             VARCHAR(255) NOT NULL,
    title               VARCHAR(255) NOT NULL,
    project_description TEXT         NOT NULL,
    status              VARCHAR(50)  NOT NULL DEFAULT 'draft',
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_project_documents_user_id ON project_documents(user_id);
```

---

## Row Level Security (RLS)

Both tables have RLS enabled. The backend uses the **service role key** which bypasses RLS. These policies serve as defense-in-depth and prepare for future direct-client access.

```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_documents ENABLE ROW LEVEL SECURITY;

-- Users can only read their own row
CREATE POLICY "Users can read own row" ON users
    FOR SELECT USING (user_id = current_setting('request.jwt.claim.sub', true));

-- Users can only access their own documents
CREATE POLICY "Users can read own documents" ON project_documents
    FOR SELECT USING (user_id = current_setting('request.jwt.claim.sub', true));

CREATE POLICY "Users can insert own documents" ON project_documents
    FOR INSERT WITH CHECK (user_id = current_setting('request.jwt.claim.sub', true));

CREATE POLICY "Users can update own documents" ON project_documents
    FOR UPDATE USING (user_id = current_setting('request.jwt.claim.sub', true));

CREATE POLICY "Users can delete own documents" ON project_documents
    FOR DELETE USING (user_id = current_setting('request.jwt.claim.sub', true));

-- Service role has full access (used by backend)
CREATE POLICY "Service role full access users" ON users
    FOR ALL USING (current_setting('role') = 'service_role');

CREATE POLICY "Service role full access documents" ON project_documents
    FOR ALL USING (current_setting('role') = 'service_role');
```

---

## Future Columns (Not in MVP)

These were identified during planning but deferred:

**users:**

- `organization_name` (VARCHAR) — which NGO/research lab the user belongs to

**project_documents:**

- `updated_at` (TIMESTAMPTZ)
- `is_deleted` (BOOLEAN) — soft deletes
- `encryption_key_version` (VARCHAR) — when encryption is introduced

