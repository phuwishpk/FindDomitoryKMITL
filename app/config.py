import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    WTF_CSRF_ENABLED = True

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(INSTANCE_DIR / 'app.db').as_posix()}"
    ).replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", (BASE_DIR / 'uploads').as_posix()) 
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    BABEL_DEFAULT_LOCALE = "th"
    BABEL_DEFAULT_TIMEZONE = "Asia/Bangkok"

    MAIL_SERVER = 'localhost'
    MAIL_PORT = 8025
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = ('FindDorm KMITL', 'noreply@finddorm-kmitl.com')

    # --- vvv เพิ่ม 3 บรรทัดนี้เข้าไป vvv ---
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")