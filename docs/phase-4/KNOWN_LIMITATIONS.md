# Known Limitations

1. **In-Memory Rate Limiter:** `SlidingWindowRateLimiter` stores request timestamps in process memory; in a multi-worker deployment each worker maintains its own counter (acceptable for single-node college/small-team deployments without Redis).
2. **External Gmail OAuth Consent:** Live Gmail email delivery requires Google Cloud OAuth credentials, redirect URI matching, and interactive browser consent by a whitelisted test user.
3. **Scheduled Reports Timezone:** Weekly/monthly schedules execute on UTC `+7 days` / `+30 days` intervals rather than custom per-user timezone cron expressions.
4. **Local SQLite vs PostgreSQL:** Local development and automated tests run on SQLite; PostgreSQL deployment requires running `alembic upgrade head` against the target PostgreSQL instance.
5. **Browser Voice API:** Speech-to-Text (`SpeechRecognition`) depends on Chrome/Edge Web Speech API support and user microphone permission.
