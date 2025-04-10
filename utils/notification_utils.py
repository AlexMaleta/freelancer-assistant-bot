import smtplib
from email.mime.text import MIMEText

from aiogram import Bot
from config import config
from models.users import UserInDB

bot = Bot(token=config.token)

async def send_deadline_notification(user: UserInDB, message: str, type: str = "telegram", subject: str = "Deadline Reminder"):
    if type == "telegram":
        if user.notify_telegram:
            try:
                await bot.send_message(chat_id=user.telegram_id, text=message, parse_mode="HTML")
                print(f"✅ Notification sent to Telegram to user {user.id}")
            except Exception as e:
                print(f"❌ Error sending to Telegram: {e}")
    elif type == "email":
        if user.notify_email and user.email:
            try:
                send_email(user.email, message, subject)
                print(f"📧 Email sent to {user.email}")
            except Exception as e:
                print(f"❌ Error sending email: {e}")

def send_email(to_address: str, message: str, subject: str = "Deadline Reminder"):
    from_address = config.EMAIL_FROM
    password = config.EMAIL_PASSWORD
    smtp_server = config.SMTP_SERVER
    smtp_port = config.SMTP_PORT

    msg = MIMEText(message, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = from_address
    msg["To"] = to_address

    server = smtplib.SMTP_SSL(smtp_server, smtp_port)
    server.login(from_address, password)
    server.sendmail(from_address, to_address, msg.as_string())
    server.quit()

