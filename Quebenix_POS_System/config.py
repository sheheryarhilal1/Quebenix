import os
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-before-production")
    DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()
    SQLITE_PATH = os.getenv("SQLITE_PATH", "quebenix_pos.db")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "quebenix_pos")
