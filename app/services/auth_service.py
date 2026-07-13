"""
Auth Service — business logic for authentication.

Handles:
  - Restaurant admin login (phone + password → JWT)
  - Customer OTP generation and verification
  - Token refresh
  - User creation (internal)

All database operations go through repositories.
This layer contains ONLY business logic — no HTTP concerns.
"""
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User, UserRole, UserStatus
from app.models.tenant import Tenant, TenantStatus


class AuthService:
    """Authentication business logic."""

    def __init__(self, db: Session):
        self.db = db
        # In-memory OTP store (replace with Redis in production)
        # Format: {"tenant_id:phone": {"otp": "1234", "expires_at": datetime}}
        # TODO: Replace with Redis for horizontal scaling

    # ─── Restaurant Admin Login ────────────────────────────────────

    def login_admin(self, phone: str, password: str, tenant_slug: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Authenticate restaurant admin with phone + password.

        Returns:
            (user, None) on success
            (None, error_message) on failure
        """
        # Resolve tenant
        tenant = self._get_active_tenant(tenant_slug)
        if not tenant:
            return None, "Restaurant not found or inactive"

        # Find user
        user = (
            self.db.query(User)
            .filter(
                User.tenant_id == tenant.id,
                User.phone == phone,
                User.role == UserRole.RESTAURANT_ADMIN,
                User.deleted_at.is_(None),
            )
            .first()
        )

        if not user:
            return None, "Invalid credentials"

        if user.status != UserStatus.ACTIVE:
            return None, "Account is suspended"

        if not user.password_hash:
            return None, "Password not set. Contact support."

        if not verify_password(password, user.password_hash):
            return None, "Invalid credentials"

        return user, None

    # ─── Customer OTP Flow ─────────────────────────────────────────

    def generate_otp(self, phone: str, tenant_slug: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate OTP for customer login.

        Returns:
            (otp_code, None) on success
            (None, error_message) on failure
        """
        tenant = self._get_active_tenant(tenant_slug)
        if not tenant:
            return None, "Restaurant not found or inactive"

        # Generate 4-digit OTP
        otp = "".join(random.choices(string.digits, k=4))

        # Store OTP (in-memory for dev, Redis for production)
        _otp_store[f"{tenant.id}:{phone}"] = {
            "otp": otp,
            "expires_at": datetime.utcnow() + timedelta(minutes=5),
            "tenant_id": tenant.id,
        }

        # TODO: Send OTP via SMS provider (Twilio, MSG91, etc.)
        # For development, OTP is returned in the response (remove in production)

        return otp, None

    def verify_otp(self, phone: str, otp: str, tenant_slug: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Verify OTP and return/create customer user.

        Returns:
            (user, None) on success
            (None, error_message) on failure
        """
        tenant = self._get_active_tenant(tenant_slug)
        if not tenant:
            return None, "Restaurant not found or inactive"

        # Check OTP
        key = f"{tenant.id}:{phone}"
        stored = _otp_store.get(key)

        if not stored:
            return None, "OTP not found. Please request a new one."

        if datetime.utcnow() > stored["expires_at"]:
            del _otp_store[key]
            return None, "OTP expired. Please request a new one."

        if stored["otp"] != otp:
            return None, "Invalid OTP"

        # OTP verified — clean up
        del _otp_store[key]

        # Find or create customer
        user = (
            self.db.query(User)
            .filter(
                User.tenant_id == tenant.id,
                User.phone == phone,
                User.role == UserRole.CUSTOMER,
                User.deleted_at.is_(None),
            )
            .first()
        )

        if not user:
            # First-time customer — create account
            user = User(
                tenant_id=tenant.id,
                phone=phone,
                role=UserRole.CUSTOMER,
                status=UserStatus.ACTIVE,
                phone_verified=True,
                is_active=True,
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

        return user, None

    # ─── Token Generation ──────────────────────────────────────────

    def create_tokens(self, user: User) -> dict:
        """
        Generate access + refresh token pair for an authenticated user.
        """
        access_token = create_access_token(
            subject=user.id,
            role=user.role,
            tenant_id=user.tenant_id,
        )
        refresh_token = create_refresh_token(
            subject=user.id,
            role=user.role,
            tenant_id=user.tenant_id,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    # ─── Token Refresh ─────────────────────────────────────────────

    def refresh_access_token(self, refresh_token: str) -> Tuple[Optional[dict], Optional[str]]:
        """
        Validate refresh token and issue new access token.

        Returns:
            (token_dict, None) on success
            (None, error_message) on failure
        """
        payload = decode_token(refresh_token)

        if not payload:
            return None, "Invalid or expired refresh token"

        if payload.get("type") != "refresh":
            return None, "Invalid token type"

        user_id = int(payload["sub"])
        user = (
            self.db.query(User)
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .first()
        )

        if not user or user.status != UserStatus.ACTIVE:
            return None, "User not found or inactive"

        tokens = self.create_tokens(user)
        return tokens, None

    # ─── Internal: Create Restaurant Admin ─────────────────────────

    def create_restaurant_admin(
        self,
        tenant_id: int,
        name: str,
        phone: str,
        password: str,
        email: Optional[str] = None,
    ) -> User:
        """
        Create a restaurant admin user.
        Called internally by our operations team during restaurant onboarding.
        """
        user = User(
            tenant_id=tenant_id,
            name=name,
            phone=phone,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.RESTAURANT_ADMIN,
            status=UserStatus.ACTIVE,
            phone_verified=True,
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    # ─── Helpers ───────────────────────────────────────────────────

    def _get_active_tenant(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug, only if active."""
        return (
            self.db.query(Tenant)
            .filter(
                Tenant.slug == slug,
                Tenant.status == "active",
                Tenant.deleted_at.is_(None),
            )
            .first()
        )


# ─── In-memory OTP store (replace with Redis in production) ────────
_otp_store: dict = {}
