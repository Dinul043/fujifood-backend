"""
Auth Routes — HTTP endpoints for authentication.

Endpoints:
  POST /auth/admin/login         → Restaurant admin login (phone + password)
  POST /auth/otp/send            → Send OTP to customer phone
  POST /auth/otp/verify          → Verify OTP and get tokens
  POST /auth/refresh             → Refresh expired access token
  GET  /auth/me                  → Get current user profile
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import (
    AdminLoginRequest,
    OTPSendRequest,
    OTPSendResponse,
    OTPVerifyRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserProfileResponse,
    ErrorResponse,
)
from app.services.auth_service import AuthService
from app.api.v1.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post(
    "/admin/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}},
    summary="Restaurant admin login",
    description="Authenticate restaurant admin with phone number and password.",
)
async def admin_login(request: AdminLoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    user, error = service.login_admin(
        phone=request.phone,
        password=request.password,
        tenant_slug=request.tenant_slug,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error,
        )

    tokens = service.create_tokens(user)
    return TokenResponse(
        **tokens,
        user=UserProfileResponse.model_validate(user),
    )


@router.post(
    "/otp/send",
    response_model=OTPSendResponse,
    responses={400: {"model": ErrorResponse}},
    summary="Send OTP to customer",
    description="Sends a 4-digit OTP to the customer's phone number for login.",
)
async def send_otp(request: OTPSendRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    otp, error = service.generate_otp(
        phone=request.phone,
        tenant_slug=request.tenant_slug,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    # In development: return OTP in response for testing
    # In production: remove this and only send via SMS
    return OTPSendResponse(
        phone=request.phone,
        message=f"OTP sent successfully. [DEV MODE: OTP is {otp}]",
    )


@router.post(
    "/otp/verify",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}},
    summary="Verify OTP and authenticate customer",
    description="Verify the OTP code and return JWT tokens. Creates customer account if first time.",
)
async def verify_otp(request: OTPVerifyRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    user, error = service.verify_otp(
        phone=request.phone,
        otp=request.otp,
        tenant_slug=request.tenant_slug,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error,
        )

    tokens = service.create_tokens(user)
    return TokenResponse(
        **tokens,
        user=UserProfileResponse.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}},
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access token pair.",
)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    tokens, error = service.refresh_access_token(request.refresh_token)

    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error,
        )

    # Get user for profile
    from app.core.security import decode_token
    payload = decode_token(tokens["access_token"])
    user = db.query(User).filter(User.id == int(payload["sub"])).first()

    return TokenResponse(
        **tokens,
        user=UserProfileResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
    description="Returns the authenticated user's profile information.",
)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserProfileResponse.model_validate(current_user)
