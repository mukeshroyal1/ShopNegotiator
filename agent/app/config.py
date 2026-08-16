from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    django_api_url: str = "http://127.0.0.1:8000/api"
    agent_service_secret: str = "dev-agent-secret-change-me"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    # Local fair-price FastAPI (ml/): http://127.0.0.1:8090
    ml_service_url: str = ""


settings = Settings()
