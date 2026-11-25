# INSLIGHT — Phase 1: Dataset-Aware RAG Architecture
**Document ID:** `PHASE1-RAG-01`
**Target:** `backend/app/services/rag_service.py`

---

## 1. Objective

Instead of stuffing thousands of raw rows or uncurated schemas into prompt windows, Inslight implements a **Dataset-Aware Retrieval-Augmented Generation (RAG)** pipeline tailored specifically for tabular Business Intelligence queries.

---

## 2. RAG Workflow for Tabular Data

```
User Question
      │
      ▼
[1. Resolve Authenticated Dataset]
      │
      ▼
[2. Extract Schema Metadata Catalog]
      │ Extracts: column names, SQL types, semantic roles,
      │ min/max/mean stats, unique value samples (top 4)
      ▼
[3. Token-Pruned Context Formatter]
      │ Prunes irrelevant columns to minimize prompt tokens
      │ Formats schema into strict DuckDB context string
      ▼
[4. Prompt Injection to LLM]
      │ Enforces strict rules:
      │ "ONLY use columns from the list above. Never invent columns."
      ▼
[5. Structured Query Output]
```

---

## 3. Metadata Catalog Extraction

Upon dataset upload, `DatasetService.profile_dataframe` extracts:
1. **Semantic Type:** Date, numeric, identifier, or categorical.
2. **Distinct Value Samples:** Up to 4 real distinct values per column to help the LLM match user phrasing to exact categorical strings (e.g. `region` -> `East, West, North, South`).
3. **Data Quality Score:** Evaluates null ratio across rows and columns.

This metadata is persisted in `datasets.schema_metadata` and retrieved strictly by dataset owner ID, guaranteeing zero context cross-contamination between users.
