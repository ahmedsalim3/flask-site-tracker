import secrets
from pathlib import Path

PROJ_ROOT = Path(__file__).resolve().parents[1]

class Config:
    SECRET_KEY = secrets.token_hex()
    DATABASE = PROJ_ROOT / 'database/database.db'
    SCHEMA = PROJ_ROOT / 'database/schema.sql'
