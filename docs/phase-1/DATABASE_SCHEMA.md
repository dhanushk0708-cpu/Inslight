# INSLIGHT — Phase 1: Database Schema & Migrations
**Document ID:** `PHASE1-DB-01`
**Database Framework:** PostgreSQL + SQLAlchemy 2.0 + Alembic

---

## 1. Relational Entity-Relationship (ER) Model

```
 ┌─────────────────────────────────────────┐
 │                  USERS                  │
 ├─────────────────────────────────────────┤
 │ id: VARCHAR(36) [PK, UUID]             │
 │ name: VARCHAR(100)                      │
 │ email: VARCHAR(255) [UNIQUE, INDEX]     │
 │ hashed_password: VARCHAR(255)           │
 │ is_active: BOOLEAN [DEFAULT TRUE]       │
 │ created_at: TIMESTAMP WITH TIME ZONE    │
 └────────────────────┬────────────────────┘
                      │ 1
                      │
                      │ has many (CASCADE DELETE)
                      ▼ *
 ┌─────────────────────────────────────────┐
 │                DATASETS                 │
 ├─────────────────────────────────────────┤
 │ id: VARCHAR(36) [PK, UUID]             │
 │ user_id: VARCHAR(36) [FK -> users.id]   │
 │ original_filename: VARCHAR(255)         │
 │ table_name: VARCHAR(100)                │
 │ storage_path: VARCHAR(500)              │
 │ row_count: INTEGER                      │
 │ column_count: INTEGER                   │
 │ schema_metadata: TEXT [JSON]            │
 │ created_at: TIMESTAMP WITH TIME ZONE    │
 └────────────────────┬────────────────────┘
                      │ 1
                      │
                      │ associates with
                      ▼ 0..*
 ┌─────────────────────────────────────────┐
 │              CHAT_SESSIONS              │
 ├─────────────────────────────────────────┤
 │ id: VARCHAR(36) [PK, UUID]             │
 │ user_id: VARCHAR(36) [FK -> users.id]   │
 │ dataset_id: VARCHAR(36) [FK -> datasets]│
 │ title: VARCHAR(200)                     │
 │ created_at: TIMESTAMP WITH TIME ZONE    │
 └────────────────────┬────────────────────┘
                      │ 1
                      │
                      │ has many (CASCADE DELETE)
                      ▼ *
 ┌─────────────────────────────────────────┐
 │              CHAT_MESSAGES              │
 ├─────────────────────────────────────────┤
 │ id: VARCHAR(36) [PK, UUID]             │
 │ session_id: VARCHAR(36) [FK -> session] │
 │ role: VARCHAR(20) ['user', 'assistant'] │
 │ content: TEXT                           │
 │ metadata_json: TEXT [JSON]              │
 │ created_at: TIMESTAMP WITH TIME ZONE    │
 └─────────────────────────────────────────┘
```

---

## 2. Table Specifications

### 2.1 Table `users`
- Primary key: `id` (UUID string generated via `uuid.uuid4()`).
- Uniqueness: `email` is indexed and enforced unique.
- Passwords: Stored as bcrypt salted hashes (`hashed_password`). Plaintext passwords never touch database storage.

### 2.2 Table `datasets`
- Ownership: `user_id` foreign key referencing `users.id` with `ondelete="CASCADE"`.
- Separation of Storage: Instead of storing millions of tabular CSV rows inside PostgreSQL text columns, `storage_path` points to an isolated DuckDB file (`data/datasets/{user_id}/{dataset_id}.duckdb`).
- Metadata: `schema_metadata` stores JSON detailing column names, data types, semantic classifications, data quality scores, and sample values.

### 2.3 Table `chat_sessions` & `chat_messages`
- Manages persistent conversational threads per user.
- If a user deletes a dataset, `dataset_id` in `chat_sessions` is set to NULL (`ondelete="SET NULL"`), preserving conversation history without broken foreign keys.
- Deleting a chat session cascades to delete all associated messages.

---

## 3. Database Migration Management with Alembic

Alembic is configured in `backend/alembic/` to inspect SQLAlchemy `Base.metadata`.
- Initial migration script: `alembic/versions/2925db913e27_initial_schema_users_datasets_.py`.
- Migration command:
  ```bash
  alembic upgrade head
  ```
- Generates `alembic_version` tracking table ensuring versioned, safe rollbacks across PostgreSQL and SQLite databases.
