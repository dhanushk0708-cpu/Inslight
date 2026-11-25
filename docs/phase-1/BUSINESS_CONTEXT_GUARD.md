# INSLIGHT — Phase 1: AI Business Context Guard
**Document ID:** `PHASE1-GUARD-01`
**Target:** `backend/app/services/business_guard.py`

---

## 1. Problem Statement

A specialized Business Intelligence assistant must focus strictly on analyzing business performance, financial metrics, tabular datasets, and strategic forecasting. Without a guardrail layer, users could ask general trivia ("Who is the Prime Minister of India?"), general programming requests ("Write a Python script"), or casual chatter. This causes token waste, confusing hallucinated SQL queries, and breaks the application's domain purpose.

---

## 2. 5-Layer Hybrid Validation Architecture

```
User Question
      │
      ▼
┌────────────────────────────────────────────────────────┐
│ Layer 1: Deterministic Pattern Evaluation              │
│ - Fast regex pattern matcher                           │
│ - Evaluates business keywords vs. non-business topics  │
└──────────────────────────┬─────────────────────────────┘
                           │ If Ambiguous
                           ▼
┌────────────────────────────────────────────────────────┐
│ Layer 2: LLM Intent Classification                     │
│ - Zero-shot classification via Groq Cloud              │
│ - Returns structured JSON: is_business, requires_data  │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Layer 3: Dataset Schema Relevance                      │
│ - Checks if question mentions dataset terms/metrics    │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Layer 4: Dataset Requirement Verification              │
│ - If question requires dataset but none uploaded:      │
│   "Please upload a business dataset..."                │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Layer 5: Execution or Polite Domain Rejection          │
└────────────────────────────────────────────────────────┘
```

---

## 3. Supported vs. Rejected Queries

| User Question | Evaluation Layer | Decision | Outcome / Response |
|---|---|---|---|
| *"What is my total revenue?"* | Layer 1 (Deterministic) | **ALLOW** | Proceeds to SQL generation |
| *"Show monthly sales trends by category"* | Layer 1 (Deterministic) | **ALLOW** | Proceeds to SQL generation |
| *"What is the percentage increase from 100 to 150?"* | Layer 1 / 2 | **ALLOW** | Handled as business calculation |
| *"Who is the Prime Minister of India?"* | Layer 1 (Deterministic) | **REJECT** | Returns Domain Rejection Message |
| *"Write a Python program to sort numbers"* | Layer 1 (Deterministic) | **REJECT** | Returns Domain Rejection Message |
| *"Tell me a joke"* | Layer 1 (Deterministic) | **REJECT** | Returns Domain Rejection Message |
| *"What is 1 + 1?"* | Layer 1 (Deterministic) | **REJECT** | Returns Domain Rejection Message |

### Domain Rejection Message:
```text
I'm Inslight, your AI Business Intelligence assistant. I can help you analyze business data, understand performance, identify trends, generate insights and support data-driven decisions.

Your question appears to be outside my business intelligence capabilities. Please ask me something related to your business data.
```
