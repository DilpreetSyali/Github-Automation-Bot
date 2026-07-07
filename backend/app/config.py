import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # GitHub OAuth App
    GITHUB_CLIENT_ID: str = os.environ.get("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.environ.get("GITHUB_CLIENT_SECRET", "")
    GITHUB_OAUTH_REDIRECT_URL: str = os.environ.get("GITHUB_OAUTH_REDIRECT_URL", "")

    # Webhook secret shared by all repos this app manages (set this same value
    # when creating the webhook on GitHub, per repo)
    GITHUB_WEBHOOK_SECRET: str = os.environ.get("GITHUB_WEBHOOK_SECRET", "")

    # Slack Incoming Webhook URL (free, no card, per Slack workspace)
    SLACK_WEBHOOK_URL: str = os.environ.get("SLACK_WEBHOOK_URL", "")
    SLACK_CLIENT_ID: str = os.environ.get("SLACK_CLIENT_ID", "")
    SLACK_CLIENT_SECRET: str = os.environ.get("SLACK_CLIENT_SECRET", "")
    SLACK_OAUTH_REDIRECT_URL: str = os.environ.get("SLACK_OAUTH_REDIRECT_URL", "")

    # Postgres (Neon/Supabase) connection string
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./dev.db")

    # Session/JWT signing secret
    SESSION_SECRET: str = os.environ.get("SESSION_SECRET", "change-me-in-prod")

    # Frontend origin, for CORS + OAuth redirect back
    FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "http://localhost:3000")

    # Optional: Google Gemini key for the AI triage stretch goal
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")

    ENV: str = os.environ.get("ENV", "development")


settings = Settings()
