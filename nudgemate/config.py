import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()


class Settings:
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    ADMIN_CHAT_ID: int = int(os.getenv("ADMIN_CHAT_ID", "0"))

    # Dahl AI API
    DAHL_API_KEY: str = os.getenv("DAHL_API_KEY", "").strip()
    DAHL_BASE_URL: str = os.getenv("DAHL_BASE_URL", "https://inference.dahl.global/v1").strip()
    DAHL_MODEL: str = os.getenv("DAHL_MODEL", "MiniMaxAI/MiniMax-M2.7").strip()

    # Whisper Settings
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "base").strip()
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu").strip()
    WHISPER_COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8").strip()

    # Timezone & Localization
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Tehran").strip()

    # Nagging (Snooze reminders)
    NAG_INTERVAL_MINUTES: int = int(os.getenv("NAG_INTERVAL_MINUTES", "15"))
    MAX_NAG_COUNT: int = int(os.getenv("MAX_NAG_COUNT", "3"))

    # Daily Briefing
    DAILY_BRIEFING_ENABLED: bool = os.getenv("DAILY_BRIEFING_ENABLED", "true").lower() in ("true", "1", "yes")
    DAILY_BRIEFING_TIME: str = os.getenv("DAILY_BRIEFING_TIME", "08:30").strip()

    # Auto-Update
    CHECK_UPDATES: bool = os.getenv("CHECK_UPDATES", "true").lower() in ("true", "1", "yes")
    UPDATE_CHECK_INTERVAL_HOURS: int = int(os.getenv("UPDATE_CHECK_INTERVAL_HOURS", "2"))
    GITHUB_REPO: str = os.getenv("GITHUB_REPO", "roseshayan/NudgeMate").strip()

    # Storage Paths
    DATABASE_PATH: Path = BASE_DIR / os.getenv("DATABASE_PATH", "data/nudgemate.db")
    TEMP_AUDIO_DIR: Path = BASE_DIR / os.getenv("TEMP_AUDIO_DIR", "temp_audio")

    @classmethod
    def validate(cls):
        errors = []
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is missing in .env")
        if not cls.DAHL_API_KEY:
            errors.append("DAHL_API_KEY is missing in .env")
        return errors


settings = Settings()

# Ensure directories exist
settings.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
settings.TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
