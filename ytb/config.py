from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    ytb_env: str = "development"
    ytb_secret_key: str = "change-me"
    ytb_admin_email: str = "admin@example.com"
    ytb_admin_password: str = "change-me"

    ytb_host: str = "0.0.0.0"
    ytb_port: int = 8000
    ytb_database_url: str = f"sqlite:///{(BASE_DIR / 'data' / 'ytb.db').as_posix()}"
    ytb_storage_dir: str = "workspace"

    ai_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    ffmpeg_bin: str = "ffmpeg"
    ffprobe_bin: str = "ffprobe"

    require_human_approval: bool = True
    block_on_missing_rights_evidence: bool = True

    cors_origins: str = "*"
    max_upload_bytes: int = 4 * 1024 ** 3

    @model_validator(mode="after")
    def resolve_paths(self) -> "Settings":
        db_url = self.ytb_database_url
        if db_url.startswith("sqlite:///"):
            db_path = Path(db_url[len("sqlite:///"):].strip()).expanduser()
            if not db_path.is_absolute():
                db_path = BASE_DIR / db_path
            self.ytb_database_url = f"sqlite:///{db_path.as_posix()}"
        storage = Path(self.ytb_storage_dir).expanduser()
        if not storage.is_absolute():
            storage = BASE_DIR / storage
        self.ytb_storage_dir = str(storage)
        return self

    @property
    def allowed_origins(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return origins if origins else ["*"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()