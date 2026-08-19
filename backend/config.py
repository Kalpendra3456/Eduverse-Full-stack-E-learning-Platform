import os
from dataclasses import dataclass


@dataclass
class Config:
    SQLALCHEMY_DATABASE_URI: str = ""
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    JWT_SECRET_KEY: str = ""
    ENV: str = "development"
    DEBUG: bool = True
    UPLOAD_FOLDER: str = "uploads"


def load_config() -> Config:
    from dotenv import load_dotenv

    load_dotenv()

    db_type = os.getenv("DB_TYPE", "sqlite")
    if db_type == "mysql":
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "3306")
        db_name = os.getenv("DB_NAME", "eduverse")
        db_user = os.getenv("DB_USER", "root")
        db_password = os.getenv("DB_PASSWORD", "")
        uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    else:
        # Default to SQLite to avoid MySQL connection errors
        base_dir = os.path.abspath(os.path.dirname(__file__))
        uri = f"sqlite:///{os.path.join(base_dir, '..', 'eduverse.db')}"

    return Config(
        SQLALCHEMY_DATABASE_URI=uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "change_this_jwt_secret"),
        ENV=os.getenv("FLASK_ENV", "development"),
        DEBUG=os.getenv("FLASK_DEBUG", "1") == "1",
        UPLOAD_FOLDER=os.getenv("UPLOAD_FOLDER", "uploads"),
    )


