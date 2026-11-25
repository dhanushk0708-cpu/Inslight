from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.oauth import OAuthCredential
from app.core.security import encrypt_secret, decrypt_secret


class OAuthRepository:
    @staticmethod
    def get_by_user_id(db: Session, user_id: str, provider: str = "google") -> Optional[OAuthCredential]:
        return db.query(OAuthCredential).filter(
            OAuthCredential.user_id == user_id,
            OAuthCredential.provider == provider,
            OAuthCredential.is_connected == True
        ).first()

    @staticmethod
    def save_or_update(
        db: Session,
        user_id: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        email: Optional[str] = None,
        token_expiry: Optional[datetime] = None,
        provider: str = "google",
        scope: str = "https://www.googleapis.com/auth/gmail.send"
    ) -> OAuthCredential:
        cred = db.query(OAuthCredential).filter(
            OAuthCredential.user_id == user_id,
            OAuthCredential.provider == provider
        ).first()

        enc_access = encrypt_secret(access_token)
        enc_refresh = encrypt_secret(refresh_token) if refresh_token else None

        if cred:
            cred.encrypted_access_token = enc_access
            if enc_refresh:
                cred.encrypted_refresh_token = enc_refresh
            if email:
                cred.email = email
            if token_expiry:
                cred.token_expiry = token_expiry
            cred.scope = scope
            cred.is_connected = True
            cred.updated_at = datetime.now(timezone.utc)
        else:
            cred = OAuthCredential(
                user_id=user_id,
                provider=provider,
                email=email,
                encrypted_access_token=enc_access,
                encrypted_refresh_token=enc_refresh,
                token_expiry=token_expiry,
                scope=scope,
                is_connected=True
            )
            db.add(cred)

        db.commit()
        db.refresh(cred)
        return cred

    @staticmethod
    def disconnect(db: Session, user_id: str, provider: str = "google") -> bool:
        cred = db.query(OAuthCredential).filter(
            OAuthCredential.user_id == user_id,
            OAuthCredential.provider == provider
        ).first()
        if not cred:
            return False
        cred.is_connected = False
        db.commit()
        return True
