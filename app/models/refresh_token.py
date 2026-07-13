"""
Refresh Token model — stores hashed refresh tokens in the database.

Why store refresh tokens:
  - Allows server-side revocation (logout everywhere)
  - Can track active sessions
  - Can enforce single-device or multi-device policies
  - Audit trail of login sessions

Never store raw tokens — only SHA-256 hashes.
"""
import hashlib
import secrets
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from app.models.base import BaseModel


class RefreshToken(BaseModel):
    """
    One record per active refresh token.
    When user refreshes, old token is revoked and new one issued.
    """
    __tablename__ = "refresh_tokens"

    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tenant_id    = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    token_hash   = Column(String(64), nullable=False, unique=True, index=True)
    expires_at   = Column(DateTime, nullable=False)
    revoked      = Column(Boolean, default=False, nullable=False)
    revoked_at   = Column(DateTime, nullable=True)
    user_agent   = Column(String(500), nullable=True)  # Browser/device info
    ip_address   = Column(String(45), nullable=True)   # IPv4 or IPv6

    @staticmethod
    def hash_token(raw_token: str) -> str:
        """SHA-256 hash of the raw token. Never store raw tokens."""
        return hashlib.sha256(raw_token.encode()).hexdigest()

    @staticmethod
    def generate() -> str:
        """Generate a cryptographically secure random token."""
        return secrets.token_urlsafe(64)

    def __repr__(self):
        return f"<RefreshToken user_id={self.user_id} revoked={self.revoked}>"
