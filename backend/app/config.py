from datetime import datetime
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / '.env',
        env_file_encoding='utf-8', extra='ignore', hide_input_in_errors=True,
    )
    db_host: str = 'localhost'
    db_port: int = Field(default=3306, ge=1, le=65535)
    db_name: str
    db_user: str
    db_password: SecretStr
    jwt_secret: SecretStr = Field(min_length=32)
    jwt_expire_minutes: int = Field(default=480, gt=0)
    app_timezone: str = 'America/Sao_Paulo'

    @field_validator('app_timezone')
    @classmethod
    def timezone_valido(cls, value):
        ZoneInfo(value)
        return value

    @property
    def database_url(self):
        return URL.create('mysql+pymysql', username=self.db_user,
                          password=self.db_password.get_secret_value(),
                          host=self.db_host, port=self.db_port,
                          database=self.db_name, query={'charset': 'utf8mb4'})


@lru_cache
def get_settings():
    return Settings()


def agora_local():
    # DATETIME do MySQL guarda o relógio local, sem informação de fuso.
    return datetime.now(ZoneInfo(get_settings().app_timezone)).replace(tzinfo=None, microsecond=0)
