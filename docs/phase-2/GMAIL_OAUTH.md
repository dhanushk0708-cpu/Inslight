# INSLIGHT — Google Gmail OAuth 2.0 Integration Guide
**Phase 2: Email Automation & Token Security**

---

## 1. Overview

INSLIGHT integrates with Google's Gmail API using OAuth 2.0 to allow users to securely dispatch business intelligence reports to stakeholders without requiring SMTP passwords or third-party email relays.

---

## 2. Configuration & Credentials

### 2.1 Credential File
- The pre-configured Google OAuth application JSON file is located at:
  `backend/google-oauth-credentials.json`
- **Security Check:** Verified that `backend/google-oauth-credentials.json` is strictly ignored by `.gitignore` and never committed to source control.
- **Configured Redirect URI:**
  `http://localhost:8000/api/v1/integrations/gmail/callback`
- **Frontend Origin:**
  `http://localhost:3000`

### 2.2 Minimum Scope Principle
To ensure user privacy and adhere to the principle of least privilege, INSLIGHT requests **only** the send permission:
- **Scope:** `https://www.googleapis.com/auth/gmail.send`
- INSLIGHT cannot read user inboxes, view email threads, or modify existing user messages.

---

## 3. OAuth 2.0 Authorization Code Flow

```text
[Frontend]                          [Backend]                      [Google OAuth]
     │                                  │                                │
     │──► GET /integrations/gmail/authorize                             │
     │    (Authenticated with JWT)      │                                │
     │◄── Return authorization_url ─────│                                │
     │    (Contains signed state token) │                                │
     │                                  │                                │
     │──────────────────────────────────────────────────────────────────►│
     │    User visits Google OAuth consent screen & approves             │
     │                                                                   │
     │◄──────────────────────────────────────────────────────────────────│
     │    Google redirects browser to:                                   │
     │    GET /api/v1/integrations/gmail/callback?code=...&state=...     │
     │                                  │                                │
     │                                  │──► Verify state CSRF token     │
     │                                  │──► Exchange code for tokens ──►│
     │                                  │◄── Access & Refresh Tokens ────│
     │                                  │──► Encrypt tokens with Fernet  │
     │                                  │──► Save to oauth_credentials   │
     │◄── Redirect 307 to: ─────────────│                                │
     │    http://localhost:3000?gmail_connected=true                    │
```

---

## 4. Token Security & Encryption at Rest

### 4.1 Fernet Symmetric Encryption
- Refresh and access tokens are sensitive credentials. Storing them in plaintext in a database creates a severe compliance and security vulnerability.
- INSLIGHT encrypts tokens before storing them in the `oauth_credentials` table using the **Fernet specification** (256-bit AES in CBC mode with HMAC SHA-256 authentication).
- The encryption key is deterministically derived from `settings.ENCRYPTION_KEY` or `settings.SECRET_KEY` using SHA-256:
```python
def get_fernet() -> Fernet:
    raw = settings.ENCRYPTION_KEY or settings.SECRET_KEY
    derived = hashlib.sha256(raw.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(derived)
    return Fernet(key)
```

### 4.2 CSRF Protection via State Parameter
- To prevent OAuth CSRF attacks, the authorization URL encodes a signed JWT containing the `user_id` and a 15-minute expiration timestamp.
- On callback, the backend decodes and verifies the signature of the `state` parameter before processing any authorization codes.

### 4.3 Automatic Token Refresh
When an access token expires:
1. `GmailService.get_valid_access_token` checks `cred.token_expiry <= now + 60s`.
2. Decrypts the stored refresh token.
3. Requests a fresh access token from `https://oauth2.googleapis.com/token`.
4. Re-encrypts and updates the database record seamlessly.

---

## 5. Email Dispatch (`GmailService.send_report_email`)

- **RFC 2822 Multipart MIME Message:** Encapsulates plain text body and file attachments (`application/pdf`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, or `text/csv`).
- **Base64 URL Encoding:** Message is URL-safe base64-encoded and sent via:
  `POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send`
- **Size Limitation:** Validates that attachments do not exceed Google's 25MB ceiling.
- **Delivery Confirmation:** Captures the unique `gmail_message_id` returned by Google and links it to the report history record.
