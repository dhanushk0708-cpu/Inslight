from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.rate_limit import limit_auth_requests
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(limit_auth_requests)])
def register(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account and return JWT access token."""
    try:
        user = AuthService.register_user(db, name=req.name, email=req.email, password=req.password)
        token = AuthService.generate_token_for_user(user)
        AuditService.log_action(
            db=db,
            user_id=user.id,
            action="register",
            resource_type="user",
            resource_id=user.id,
            status="success",
            metadata={"email": user.email, "role": user.role},
        )
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
    except ValueError as e:
        AuditService.log_action(
            db=db,
            action="register",
            resource_type="user",
            status="failure",
            metadata={"email": req.email, "reason": str(e)},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(limit_auth_requests)])
def login(req: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate user with email/password and return JWT access token."""
    user = AuthService.authenticate_user(db, email=req.email, password=req.password)
    if not user:
        AuditService.log_action(
            db=db,
            action="login",
            resource_type="user",
            status="failure",
            metadata={"email": req.email},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = AuthService.generate_token_for_user(user)
    AuditService.log_action(
        db=db,
        user_id=user.id,
        action="login",
        resource_type="user",
        resource_id=user.id,
        status="success",
        metadata={"email": user.email, "role": user.role},
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(user: User = Depends(get_current_user)):
    """Fetch profile of currently authenticated user."""
    return UserResponse.model_validate(user)


@router.post("/logout")
def logout(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Logout current user (client invalidates local token)."""
    AuditService.log_action(
        db=db,
        user_id=user.id,
        action="logout",
        resource_type="user",
        resource_id=user.id,
        status="success",
    )
    return {"message": "Successfully logged out."}
