"""
Password Reset Token model — dedicated table for password reset flow.

Separate from login OTPs for clean separation of concerns.
Flow: User requests reset → OTP sent to email → User enters OTP + new password → Password updated.
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from app.models.base import BaseModel


class PasswordResetToken(BaseModel):
    """
    Stores password reset OTPs.
    One active reset token per user at a time.
    Expires in 10 minutes. Max 3 attempts.
    """
    __tablename__ = "password_reset_tokens"

    tenant_id    = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    email        = Column(String(255), nullable=False, index=True)
    otp          = Column(String(6), nullable=False)
    expires_at   = Column(DateTime, nullable=False)
    is_used      = Column(Boolean, default=False, nullable=False)
    attempts     = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<PasswordResetToken email={self.email} user_id={self.user_id}>"
