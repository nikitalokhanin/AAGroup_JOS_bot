from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    tz: str = os.getenv("TZ", "Europe/Moscow")
    admin_ids: list[int] = None
    rate_limit_seconds: int = int(os.getenv("RATE_LIMIT_SECONDS", "5"))
    data_dir: str = os.getenv("DATA_DIR", "./data")

    def __post_init__(self):
        admins = os.getenv("ADMIN_IDS", "").strip()
        self.admin_ids = [int(x) for x in admins.split(",") if x.strip().isdigit()]

settings = Settings()