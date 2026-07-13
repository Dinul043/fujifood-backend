"""
OTP Token model — stores OTPs in the database (not in-memory).

Each OTP has an expiry time. Old OTPs are cleaned up periodically.
Scoped to tenant (a customer's OTP is per-restaurant).
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from app.models.base import BaseModel


class OTPToken(BaseModel):
    """
    Stores OTPs for verification.
    Purpose: 'login' (customer login) or 'password_reset' (forgot password)
    One active OTP per identifier+tenant+purpose combination.
    """
    __tablename__ = "otp_tokens"

    tenant_id    = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    phone        = Column(String(255), nullable=False, index=True)  # email or phone as identifier
    otp          = Column(String(6), nullable=False)
    purpose      = Column(String(20), nullable=False, default="login")  # 'login' or 'password_reset'
    expires_at   = Column(DateTime, nullable=False)
    is_used      = Column(Boolean, default=False, nullable=False)
    attempts     = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<OTPToken phone={self.phone} tenant_id={self.tenant_id}>"
