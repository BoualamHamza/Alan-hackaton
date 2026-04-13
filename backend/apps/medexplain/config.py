from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mistral_api_key: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    did_api_key: str = ""
    did_avatar_id: str = ""
    did_avatar_image_url: str = ""
    output_dir: str = "./output"
    image_source: str = "placeholder"
    unsplash_access_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Convenience alias — use this throughout the codebase.
# In tests, patch `config.settings` or call `get_settings.cache_clear()` after
# setting env vars.
settings = get_settings()
