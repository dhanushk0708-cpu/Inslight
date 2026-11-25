# INSLIGHT — Phase 1: Authentication & Authorization Flow
**Document ID:** `PHASE1-AUTH-01`
**Security Standard:** OAuth2 Bearer Tokens (JWT) + Bcrypt Password Hashing

---

## 1. Authentication Lifecycle

```
[User Browser]                      [FastAPI Backend]                 [Database]
      │                                     │                              │
      │ 1. POST /api/v1/auth/register       │                              │
      │    { name, email, password }        │                              │
      │────────────────────────────────────►│                              │
      │                                     │ Check duplicate email        │
      │                                     │─────────────────────────────►│
      │                                     │                              │
      │                                     │ Hash password with bcrypt    │
      │                                     │ Create user record           │
      │                                     │─────────────────────────────►│
      │                                     │                              │
      │                                     │ Generate JWT Access Token    │
      │                                     │ (Signed with HS256)          │
      │◄────────────────────────────────────│                              │
      │ 2. Response: { access_token, user } │                              │
      │                                     │                              │
      │ (Store token in localStorage)       │                              │
      │                                     │                              │
      │ 3. Authenticated Request:           │                              │
      │    GET /api/v1/datasets             │                              │
      │    Header: Authorization: Bearer    │                              │
      │────────────────────────────────────►│                              │
      │                                     │ Decode & verify JWT signature│
      │                                     │ Extract user_id ('sub')      │
      │                                     │ Query user record            │
      │                                     │─────────────────────────────►│
      │                                     │ Inject user into route       │
      │◄────────────────────────────────────│                              │
      │ 4. Response: User's private data    │                              │
```

---

## 2. Security Safeguards

1. **Password Hashing:**
   - Implemented via `bcrypt` with automatic salting (`bcrypt.gensalt()`).
   - Plaintext passwords are never logged, stored, or reflected.
2. **Access Token Generation:**
   - Tokens are signed with HMAC-SHA256 (`HS256`) using `settings.SECRET_KEY`.
   - Token payload:
     ```json
     {
       "sub": "user-uuid-v4",
       "iat": 1732430000,
       "exp": 1732516400
     }
     ```
   - Expiration default: 24 hours (1440 minutes). Expired tokens are immediately rejected with HTTP 401 Unauthorized.
3. **Protected Route Dependency Injection (`get_current_user`):**
   - Routes declare `user: User = Depends(get_current_user)`.
   - Rejects missing, malformed, or expired Bearer tokens.
   - Enforces `user.is_active` check.
4. **Clean Session Teardown:**
   - POST `/api/v1/auth/logout` instructs client to purge stored tokens.
   - 401 responses automatically purge client-side session state.
