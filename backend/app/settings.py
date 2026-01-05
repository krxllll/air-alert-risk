import os

class Settings:
    alerts_base_url: str = os.getenv(
        "ALERTS_API_BASE_URL",
        "https://api.alerts.in.ua"
    )
    alerts_token: str | None = os.getenv("ALERTS_API_TOKEN")

settings = Settings()
