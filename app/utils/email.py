"""
Email utility — sends OTPs via SMTP (Mailtrap in dev, real SMTP in production).
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings


def send_otp_email(to_email: str, otp: str, restaurant_name: str = "A2B") -> bool:
    """
    Send OTP to customer's email address.
    Returns True on success, False on failure.
    """
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        # No email configured — return True (dev mode, OTP shown in response)
        return True

    subject = f"Your login OTP for {restaurant_name}"
    html_body = f"""
    <div style="font-family: 'Inter', sans-serif; max-width: 480px; margin: 0 auto; padding: 40px 32px; background: #FAF9F6;">
        <div style="text-align: center; margin-bottom: 32px;">
            <h1 style="font-size: 24px; font-weight: 700; color: #1A1A1A; margin: 0;">{restaurant_name}</h1>
            <p style="font-size: 10px; color: #C8964B; letter-spacing: 0.2em; margin-top: 4px;">VEG RESTAURANT</p>
        </div>
        <div style="background: white; border-radius: 16px; padding: 32px; border: 1px solid #E8E4DE;">
            <p style="font-size: 15px; color: #1A1A1A; margin: 0 0 16px;">Your verification code is:</p>
            <div style="text-align: center; margin: 24px 0;">
                <span style="font-size: 36px; font-weight: 700; color: #C8964B; letter-spacing: 0.3em;">{otp}</span>
            </div>
            <p style="font-size: 13px; color: #888; margin: 0;">This code expires in 5 minutes. Do not share it with anyone.</p>
        </div>
        <p style="font-size: 11px; color: #AAA; text-align: center; margin-top: 24px;">
            Powered by Fuji Sakura Tech
        </p>
    </div>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.FROM_EMAIL
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.FROM_EMAIL, to_email, msg.as_string())

        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False
