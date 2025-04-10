import os

from dotenv import load_dotenv

load_dotenv()

token = os.getenv("BOT_TOKEN")
EMAIL_FROM= os.getenv("EMAIL_FROM")
EMAIL_PASSWORD= os.getenv("EMAIL_PASSWORD")
SMTP_SERVER= os.getenv("SMTP_SERVER")
SMTP_PORT= os.getenv("SMTP_PORT")
ADMIN_EMAIL= os.getenv("ADMIN_EMAIL")
db_path = "database.db"


