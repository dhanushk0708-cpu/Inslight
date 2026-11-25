# Database Migrations, Backup & Recovery

## Alembic Schema Management
Alembic is the authoritative migration mechanism (`backend/alembic.ini`, `backend/alembic/versions/`):
1. `b4280f8d0630` — Initial schema (Phase 1 & Phase 2 tables)
2. `c7391abf0831` — Phase 3 (`alerts`, `alert_rules`, `saved_dashboards`, `dataset_relationships`)
3. `2604d90ecb63` — Phase 4 (`users.role`, `notifications`, `audit_logs`, `presentations`)

### Migration Commands (from `backend/`)
```cmd
.venv\Scripts\alembic.exe current
.venv\Scripts\alembic.exe upgrade head
```
Rollback one revision:
```cmd
.venv\Scripts\alembic.exe downgrade -1
```

## Backup & Restore Strategy
### SQLite (Local / College Demo)
Consistent online backup using `sqlite3.Connection.backup()` (`backend/scripts/backup_db.py`):
```cmd
cd backend
.venv\Scripts\python.exe scripts\backup_db.py backup
```
Restore from a backup (automatically saves a `.pre_restore.bak` safety copy):
```cmd
cd backend
.venv\Scripts\python.exe scripts\backup_db.py restore --file .\data\backups\inslight_backup_YYYYMMDD_HHMMSS.db
```

### PostgreSQL (Production Deployment)
Use standard `pg_dump` / `pg_restore` against `DATABASE_URL`:
```bash
pg_dump "$DATABASE_URL" -Fc -f inslight_backup.dump
pg_restore -d "$DATABASE_URL" --clean --if-exists inslight_backup.dump
```
> **Note:** SQLite tests do not prove PostgreSQL-specific behavior; verify `alembic upgrade head` against a live PostgreSQL instance before production cutover.
