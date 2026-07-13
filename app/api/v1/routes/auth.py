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
    CustomerLoginRequest,
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
    "/customer/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}},
    summary="Customer email + password login",
)
async def customer_login(request: CustomerLoginRequest, db: Session = Depends(get_db)):
    """Customer logs in with email + password."""
    service = AuthService(db)
    user, error = service.login_customer(
        email=request.email,
        password=request.password,
        tenant_slug=request.tenant_slug,
    )
    if error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error)
    tokens = service.create_tokens(user)
    return TokenResponse(**tokens, user=UserProfileResponse.model_validate(user))


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
        phone=request.phone or "",
        tenant_slug=request.tenant_slug,
        email=request.email,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    # In development: return OTP in response for testing
    identifier = request.email or request.phone
    return OTPSendResponse(
        phone=identifier or "",
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
        phone=request.phone or "",
        otp=request.otp,
        tenant_slug=request.tenant_slug,
        email=request.email,
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


@router.post(
    "/forgot-password/send",
    summary="Send password reset OTP to email",
)
async def send_reset_otp_route(request: OTPSendRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    otp, error = service.send_reset_otp(
        email=request.email or "",
        tenant_slug=request.tenant_slug,
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"success": True, "message": f"Reset OTP sent. [DEV: OTP is {otp}]"}


@router.post(
    "/forgot-password/reset",
    summary="Verify OTP and set new password",
)
async def reset_password_route(request: OTPVerifyRequest, new_password: str = "", db: Session = Depends(get_db)):
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    service = AuthService(db)
    success, error = service.reset_password(
        email=request.email or "",
        otp=request.otp,
        new_password=new_password,
        tenant_slug=request.tenant_slug,
    )
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"success": True, "message": "Password reset successfully"}


@router.patch(
    "/profile",
    response_model=UserProfileResponse,
    summary="Update user profile (name, phone, password)",
)
async def update_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    name: str = None,
    phone: str = None,
    password: str = None,
):
    service = AuthService(db)
    user, error = service.update_user_profile(current_user.id, name=name, phone=phone, password=password)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return UserProfileResponse.model_validate(user)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
    description="Returns the authenticated user's profile information.",
)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserProfileResponse.model_validate(current_user)
