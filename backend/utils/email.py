from aiosmtplib import send
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from ..core.config import get_settings

settings = get_settings()

async def send_verification_email(email_to: str, verification_url: str):
    env = Environment(loader=FileSystemLoader('backend/template'))
    template = env.get_template("verify_email.html")
    html_content = template.render(verification_url=verification_url)

    msg = MIMEMultipart()
    msg["From"] = settings.EMAILS_FROM_EMAIL
    msg["To"] = email_to
    msg["Subject"] = "Verify your email"

    msg.attach(MIMEText(html_content, "html"))

    await send(
        msg,  
        hostname=settings.SMTP_SERVER,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        use_tls=False,  
        start_tls=True  
    )

async def send_password_reset_email(email_to: str, reset_url: str):
    env = Environment(loader=FileSystemLoader('backend/template'))
    template = env.get_template("password_reset.html")
    html_content = template.render(reset_url=reset_url)
    
    msg = MIMEMultipart()
    msg["From"] = settings.EMAILS_FROM_EMAIL
    msg["To"] = email_to
    msg["Subject"] = "Password Reset Request"
    msg.attach(MIMEText(html_content, "html"))

    await send(
        msg,
        hostname=settings.SMTP_SERVER,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        use_tls=False,
        start_tls=True
    )
    
async def send_exchange_confirmation_email(email_to: str, user_name: str, requested_item: str, offered_item: str):
    env = Environment(loader=FileSystemLoader('backend/template'))
    template = env.get_template("exchange_confirmation.html")
    html_content = template.render(user_name=user_name, requested_item=requested_item, offered_item=offered_item)
    
    msg = MIMEMultipart()
    msg["From"] = settings.EMAILS_FROM_EMAIL
    msg["To"] = email_to
    msg["Subject"] = "Exchange Confirmation"
    msg.attach(MIMEText(html_content, "html"))

    await send(
        msg,
        hostname=settings.SMTP_SERVER,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        use_tls=False,
        start_tls=True
    )