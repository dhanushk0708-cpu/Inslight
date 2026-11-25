from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.logging import logger
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.oauth_repository import OAuthRepository
from app.services.gmail_service import GmailService
from app.schemas.report import GmailStatusResponse

router = APIRouter(prefix="/integrations/gmail", tags=["Gmail Integration"])


@router.get("/authorize")
def authorize_gmail(
    user: User = Depends(get_current_user)
):
    """
    Generate Google OAuth 2.0 authorization URL for connecting Gmail API.
    """
    try:
        auth_url = GmailService.get_authorization_url(user.id)
        return {"authorization_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate authorization URL: {str(e)}")


@router.get("/callback")
async def gmail_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth 2.0 redirect callback, validate state CSRF token, and store encrypted credentials.
    """
    try:
        await GmailService.handle_oauth_callback(db=db, code=code, state=state)
        return RedirectResponse(url=f"{settings.FRONTEND_URL}?gmail_connected=true")
    except ValueError as ve:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}?gmail_error={ve}")
    except Exception as e:
        logger.error(f"OAuth Callback error: {e}", exc_info=True)
        return RedirectResponse(url=f"{settings.FRONTEND_URL}?gmail_error={str(e)[:50]}")


@router.get("/status", response_model=GmailStatusResponse)
def get_gmail_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Check if the authenticated user has a connected Gmail integration.
    """
    cred = OAuthRepository.get_by_user_id(db, user_id=user.id, provider="google")
    if cred and cred.is_connected:
        return GmailStatusResponse(is_connected=True, email=cred.email, provider="google")
    return GmailStatusResponse(is_connected=False, email=None, provider="google")


@router.post("/disconnect")
def disconnect_gmail(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Disconnect Gmail integration and revoke saved access.
    """
    success = OAuthRepository.disconnect(db, user_id=user.id, provider="google")
    return {"status": "success", "message": "Gmail account disconnected successfully."}
