# INSLIGHT — Deployment & Setup Guide

## 1. Local Setup (Windows CMD)

### Prerequisites
- Python 3.11+
- Node.js 18+ / 20+
- Groq API Key (`GROQ_API_KEY`)

### Environment Configuration
1. **Backend:** Copy `backend\.env.example` to `backend\.env` and configure:
   - `SECRET_KEY` (strong random hex string)
   - `ENCRYPTION_KEY` (strong Fernet seed string)
   - `GROQ_API_KEY`
   - `DATABASE_URL` (`sqlite:///./data/inslight.db` for local demo, or PostgreSQL URI for production)
   - `CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000`
2. **Frontend:** Copy `frontend\.env.example` (or create `frontend\.env.local`) with:
   - `NEXT_PUBLIC_API_URL=http://localhost:8000`

### Database Setup & Migrations (from `backend\`)
```cmd
cd backend
.venv\Scripts\activate
alembic upgrade head
```

### Create Initial Administrator Securely
```cmd
cd backend
.venv\Scripts\python.exe scripts\create_admin.py --email admin@inslight.ai --name "System Admin"
```

### Backend Startup (from `backend\`)
```cmd
cd backend
.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Startup (from `frontend\`)
```cmd
cd frontend
npm install
npm run build
npm run start
```
*(Or `npm run dev` during active development.)*

---

## 2. Production Deployment Architecture (College / Cloud Single-Node)
- **Frontend:** Next.js deployed on Vercel or behind Nginx with `NEXT_PUBLIC_API_URL` pointing to the HTTPS backend domain.
- **Backend:** FastAPI (`uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2`) behind HTTPS reverse proxy (Nginx/Render/Railway).
- **Database:** Managed PostgreSQL (`DATABASE_URL=postgresql+psycopg2://...`) with `alembic upgrade head` run prior to server boot.
- **Persistent Storage:** Mount persistent volume for `DATASET_STORAGE_DIR` (`.duckdb` files) and `REPORT_STORAGE_DIR` (`.pdf`, `.xlsx`, `.pptx` exports).
- **OAuth / Gmail:** Update Google Cloud OAuth authorized redirect URI to `https://<backend-domain>/api/v1/integrations/gmail/callback` and `FRONTEND_URL=https://<frontend-domain>`.

---

## 3. Troubleshooting
- **`429 Too Many Requests` during heavy testing:** Increase `RATE_LIMIT_AUTH_PER_MIN` / `RATE_LIMIT_AI_PER_MIN` or set `RATE_LIMIT_ENABLED=false` in `.env`.
- **Next.js `Cannot find module './XX.js'`:** Stop `next dev`, delete `frontend\.next\`, and restart `npm run dev`.
- **Alembic `alembic current` empty on legacy SQLite:** Run `alembic stamp c7391abf0831` then `alembic upgrade head`.
