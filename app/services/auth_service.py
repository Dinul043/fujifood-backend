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

    # ─── Customer Email + Password Login ─────────────────────────

    def login_customer(self, email: str, password: str, tenant_slug: str) -> Tuple[Optional[User], Optional[str]]:
        """Authenticate customer with email + password."""
        tenant = self._get_active_tenant(tenant_slug)
        if not tenant:
            return None, "Restaurant not found or inactive"

        user = (
            self.db.query(User)
            .filter(
                User.tenant_id == tenant.id,
                User.email == email,
                User.role == UserRole.CUSTOMER,
                User.deleted_at.is_(None),
            )
            .first()
        )
        if not user:
            return None, "Invalid email or password"
        if not user.password_hash:
            return None, "Password not set. Please use OTP login or reset your password."
        if user.status != UserStatus.ACTIVE:
            return None, "Account is suspended"
        if not verify_password(password, user.password_hash):
            return None, "Invalid email or password"

        return user, None

    # ─── Customer OTP Flow ─────────────────────────────────────────

    def generate_otp(self, phone: str, tenant_slug: str, email: str = None, is_signup: bool = False) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate OTP for customer login (email or phone).
        Stores OTP in database. Sends via email if email provided.
        If is_signup=True, rejects existing emails.

        Returns:
            (otp_code, None) on success
            (None, error_message) on failure
        """
        tenant = self._get_active_tenant(tenant_slug)
        if not tenant:
            return None, "Restaurant not found or inactive"

        # Determine identifier
        identifier = email if email else phone
        if not identifier:
            return None, "Either email or phone is required"

        # If signup mode, check if email already has an account
        if is_signup and email:
            existing = (
                self.db.query(User)
                .filter(
                    User.tenant_id == tenant.id,
                    User.email == email,
                    User.role == UserRole.CUSTOMER,
                    User.deleted_at.is_(None),
                )
                .first()
            )
            if existing:
                return None, "An account with this email already exists. Please sign in instead."

        # Generate 4-digit OTP
        otp = "".join(random.choices(string.digits, k=4))

        # Invalidate all previous unused OTPs for this identifier
        from app.models.otp_token import OTPToken
        from app.models.base import now_ist
        self.db.query(OTPToken).filter(
            OTPToken.tenant_id == tenant.id,
            OTPToken.phone == identifier,
            OTPToken.is_used == False,
        ).update({"is_used": True})

        # Store new OTP
        otp_record = OTPToken(
            tenant_id=tenant.id,
            phone=identifier,
            otp=otp,
            purpose="login",
            expires_at=now_ist() + timedelta(minutes=5),
        )
        self.db.add(otp_record)
        self.db.commit()

        # Send OTP via email if email provided
        if email:
            from app.utils.email import send_otp_email
            send_otp_email(email, otp)

        return otp, None

    def verify_otp(self, phone: str, otp: str, tenant_slug: str, email: str = None) -> Tuple[Optional[User], Optional[str]]:
        """
        Verify OTP and return/create customer user.
        Checks OTP from database.

        Returns:
            (user, None) on success
            (None, error_message) on failure
        """
        tenant = self._get_active_tenant(tenant_slug)
        if not tenant:
            return None, "Restaurant not found or inactive"

        identifier = email if email else phone
        if not identifier:
            return None, "Either email or phone is required"

        from app.models.otp_token import OTPToken
        otp_record = (
            self.db.query(OTPToken)
            .filter(
                OTPToken.tenant_id == tenant.id,
                OTPToken.phone == identifier,
                OTPToken.is_used == False,
            )
            .order_by(OTPToken.created_at.desc())
            .first()
        )

        if not otp_record:
            return None, "OTP not found or expired. Please request a new one."

        if otp_record.otp != otp:
            otp_record.attempts += 1
            self.db.commit()
            if otp_record.attempts >= 3:
                otp_record.is_used = True
                self.db.commit()
                return None, "Too many failed attempts. Please request a new OTP."
            return None, "Invalid OTP"
            self.db.commit()
            if otp_record.attempts >= 3:
                otp_record.is_used = True
                self.db.commit()
                return None, "Too many failed attempts. Please request a new OTP."
            return None, "Invalid OTP"

        # OTP verified — mark as used
        otp_record.is_used = True
        self.db.commit()

        # Find or create customer (use phone or email as identifier)
        lookup_field = User.email if email else User.phone
        lookup_value = email if email else phone

        user = (
            self.db.query(User)
            .filter(
                User.tenant_id == tenant.id,
                lookup_field == lookup_value,
                User.role == UserRole.CUSTOMER,
                User.deleted_at.is_(None),
            )
            .first()
        )

        if not user:
            # First-time customer — check if email already exists (prevent duplicates)
            existing = (
                self.db.query(User)
                .filter(
                    User.tenant_id == tenant.id,
                    User.email == email,
                    User.deleted_at.is_(None),
                )
                .first()
            )
            if existing:
                return existing, None  # Return existing user (they can login)

            # Create new customer — use email as phone if phone is empty (unique constraint)
            user = User(
                tenant_id=tenant.id,
                phone=phone if phone else email,
                email=email,
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

    # ─── Forgot Password: Send Reset OTP ─────────────────────────

    def send_reset_otp(self, email: str, tenant_slug: str) -> Tuple[Optional[str], Optional[str]]:
        """Send OTP for password reset. Uses dedicated password_reset_tokens table."""
        tenant = self._get_active_tenant(tenant_slug)
        if not tenant:
            return None, "Restaurant not found or inactive"

        user = (
            self.db.query(User)
            .filter(User.tenant_id == tenant.id, User.email == email, User.deleted_at.is_(None))
            .first()
        )
        if not user:
            return None, "No account found with this email"

        otp = "".join(random.choices(string.digits, k=4))

        from app.models.password_reset_token import PasswordResetToken
        from app.models.base import now_ist
        reset_token = PasswordResetToken(
            tenant_id=tenant.id,
            user_id=user.id,
            email=email,
            otp=otp,
            expires_at=now_ist() + timedelta(minutes=10),
        )
        self.db.add(reset_token)
        self.db.commit()

        from app.utils.email import send_otp_email
        send_otp_email(email, otp)

        return otp, None

    # ─── Forgot Password: Verify & Reset ──────────────────────────

    def reset_password(self, email: str, otp: str, new_password: str, tenant_slug: str) -> Tuple[bool, Optional[str]]:
        """Verify reset OTP and update password. Uses password_reset_tokens table."""
        tenant = self._get_active_tenant(tenant_slug)
        if not tenant:
            return False, "Restaurant not found"

        from app.models.password_reset_token import PasswordResetToken
        from app.models.base import now_ist
        reset_record = (
            self.db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.tenant_id == tenant.id,
                PasswordResetToken.email == email,
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at > now_ist(),
            )
            .order_by(PasswordResetToken.created_at.desc())
            .first()
        )

        if not reset_record:
            return False, "Reset OTP expired or not found"
        if reset_record.otp != otp:
            reset_record.attempts += 1
            self.db.commit()
            if reset_record.attempts >= 3:
                reset_record.is_used = True
                self.db.commit()
                return False, "Too many attempts. Request a new OTP."
            return False, "Invalid OTP"

        reset_record.is_used = True

        user = self.db.query(User).filter(User.id == reset_record.user_id).first()
        if not user:
            return False, "User not found"

        user.password_hash = hash_password(new_password)
        self.db.commit()
        return True, None

    # ─── Update Profile ───────────────────────────────────────────

    def update_user_profile(self, user_id: int, name: str = None, phone: str = None, password: str = None) -> Tuple[Optional[User], Optional[str]]:
        """Update user's name, phone, or password."""
        user = self.db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        if not user:
            return None, "User not found"

        if name:
            user.name = name
        if phone:
            user.phone = phone
        if password:
            user.password_hash = hash_password(password)

        self.db.commit()
        self.db.refresh(user)
        return user, None

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


# OTP is now stored in database (otp_tokens table)
