import os
import json
import base64
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
import httpx
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import logger
from app.core.security import create_access_token, decode_access_token, decrypt_secret, encrypt_secret
from app.models.user import User
from app.repositories.oauth_repository import OAuthRepository

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.send"


class GmailService:
    @classmethod
    def load_oauth_client_config(cls) -> Dict[str, Any]:
        """Safely load client_id, client_secret and redirect_uris from JSON without exposing them."""
        filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), settings.GOOGLE_OAUTH_CREDENTIALS_FILE)
        if not os.path.exists(filepath):
            # Fallback to local root
            filepath = settings.GOOGLE_OAUTH_CREDENTIALS_FILE

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Google OAuth credentials file not found at: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        config = data.get("web") or data.get("installed")
        if not config:
            raise ValueError("Invalid OAuth credentials file structure. Expected top-level 'web' key.")

        client_id = config.get("client_id")
        client_secret = config.get("client_secret")
        redirect_uris = config.get("redirect_uris", [settings.GMAIL_REDIRECT_URI])

        if not client_id or not client_secret:
            raise ValueError("Client ID or Client Secret missing in credentials file.")

        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uris[0] if redirect_uris else settings.GMAIL_REDIRECT_URI
        }

    @classmethod
    def get_authorization_url(cls, user_id: str) -> str:
        """
        Generate Google OAuth 2.0 authorization URL with CSRF-protected signed state token.
        """
        cfg = cls.load_oauth_client_config()
        # Create signed state token carrying user_id and expiration
        state_payload = create_access_token(subject=user_id, expires_delta=timedelta(minutes=15))

        params = {
            "client_id": cfg["client_id"],
            "redirect_uri": cfg["redirect_uri"],
            "response_type": "code",
            "scope": GMAIL_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "state": state_payload
        }
        return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

    @classmethod
    async def handle_oauth_callback(cls, db: Session, code: str, state: str) -> str:
        """
        Exchange authorization code for tokens, validate state, and persist encrypted credentials.
        """
        # Validate CSRF state token
        payload = decode_access_token(state)
        if not payload or "sub" not in payload:
            raise ValueError("Invalid or expired OAuth state parameter. Possible CSRF attempt.")

        user_id = payload["sub"]
        cfg = cls.load_oauth_client_config()

        # Exchange authorization code with Google token endpoint
        token_data = {
            "code": code,
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "redirect_uri": cfg["redirect_uri"],
            "grant_type": "authorization_code"
        }

        async with httpx.AsyncClient() as client:
            token_res = await client.post(GOOGLE_TOKEN_URL, data=token_data)
            if token_res.status_code != 200:
                logger.error(f"Google Token Exchange Failed: {token_res.text}")
                raise ValueError("Failed to exchange authorization code with Google.")

            tokens = token_res.json()
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")
            expires_in = tokens.get("expires_in", 3600)
            token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            # Retrieve connected Google user's email address
            email = None
            try:
                userinfo_res = await client.get(
                    GOOGLE_USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                if userinfo_res.status_code == 200:
                    email = userinfo_res.json().get("email")
            except Exception as e:
                logger.warning(f"Could not fetch Google user info: {e}")

        # Persist securely in database
        OAuthRepository.save_or_update(
            db=db,
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            email=email,
            token_expiry=token_expiry
        )
        return user_id

    @classmethod
    async def get_valid_access_token(cls, db: Session, user_id: str) -> str:
        """
        Retrieve valid access token, refreshing it automatically if expired.
        """
        cred = OAuthRepository.get_by_user_id(db, user_id)
        if not cred or not cred.is_connected:
            raise ValueError("Gmail is not connected. Please connect your Gmail account first.")

        access_token = decrypt_secret(cred.encrypted_access_token)
        refresh_token = decrypt_secret(cred.encrypted_refresh_token) if cred.encrypted_refresh_token else None

        # Check if token is expired or within 60s of expiring
        now = datetime.now(timezone.utc)
        expiry = cred.token_expiry
        if expiry:
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            is_expired = expiry <= (now + timedelta(seconds=60))
        else:
            is_expired = False

        if is_expired:
            if not refresh_token:
                raise ValueError("Gmail access token has expired and no refresh token is available. Please re-authenticate.")

            cfg = cls.load_oauth_client_config()
            refresh_data = {
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }

            async with httpx.AsyncClient() as client:
                res = await client.post(GOOGLE_TOKEN_URL, data=refresh_data)
                if res.status_code != 200:
                    logger.error(f"Token refresh failed: {res.text}")
                    raise ValueError("Failed to refresh Google access token. Please re-connect Gmail.")

                new_tokens = res.json()
                access_token = new_tokens.get("access_token")
                expires_in = new_tokens.get("expires_in", 3600)
                new_expiry = now + timedelta(seconds=expires_in)

                OAuthRepository.save_or_update(
                    db=db,
                    user_id=user_id,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    email=cred.email,
                    token_expiry=new_expiry
                )

        return access_token

    @classmethod
    async def send_report_email(
        cls,
        db: Session,
        user: User,
        recipients: List[str],
        subject: str,
        body: str,
        file_path: str,
        attachment_name: str,
        cc_recipients: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send business intelligence report via Gmail API with explicit verification and attachments.
        """
        if not recipients:
            raise ValueError("At least one recipient email address is required.")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Attachment file not found: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size > 25 * 1024 * 1024:
            raise ValueError(f"Attachment size ({file_size / (1024*1024):.1f}MB) exceeds Gmail's 25MB limit.")

        access_token = await cls.get_valid_access_token(db, user.id)

        # Build MIME multipart message
        msg = MIMEMultipart()
        msg["To"] = ", ".join(recipients)
        if cc_recipients:
            msg["Cc"] = ", ".join(cc_recipients)
        msg["Subject"] = subject
        msg["From"] = user.email

        # Email body
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Determine MIME type for attachment
        ext = attachment_name.lower().split(".")[-1]
        if ext == "pdf":
            maintype, subtype = "application", "pdf"
        elif ext in ("xlsx", "xls"):
            maintype, subtype = "application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            maintype, subtype = "text", "csv"

        with open(file_path, "rb") as f:
            part = MIMEBase(maintype, subtype)
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename=\"{attachment_name}\"")
            msg.attach(part)

        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

        # Send via Gmail API
        async with httpx.AsyncClient() as client:
            res = await client.post(
                GMAIL_SEND_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={"raw": raw_message}
            )

            if res.status_code not in (200, 201):
                logger.error(f"Gmail API send failed ({res.status_code}): {res.text}")
                raise ValueError(f"Gmail delivery rejected by Google ({res.status_code}): {res.text[:200]}")

            res_data = res.json()
            gmail_msg_id = res_data.get("id")

            return {
                "status": "success",
                "message": "Report emailed successfully via Gmail API",
                "gmail_message_id": gmail_msg_id,
                "recipients": recipients,
                "delivered_at": datetime.now(timezone.utc)
            }
