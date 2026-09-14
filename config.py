from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ytb_env: str = "development"
    ytb_secret_key: str = "change-me"
    ytb_admin_email: str = "admin@example.com"
    ytb_admin_password: str = "change-me"

    ytb_host: str = "0.0.0.0"
    ytb_port: int = 8000
    ytb_database_url: str = "sqlite:///./data/ytb.db"
    ytb_storage_dir: str = "./workspace"

    ai_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"

    ffmpeg_bin: str = "ffmpeg"
    ffprobe_bin: str = "ffprobe"

    require_human_approval: bool = True
    block_on_missing_rights_evidence: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
