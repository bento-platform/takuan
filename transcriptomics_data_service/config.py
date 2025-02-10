from fastapi import Depends
from functools import lru_cache
from typing import Annotated, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
from bento_lib.config.pydantic import CorsOriginsParsingEnvSettingsSource

from .constants import SERVICE_GROUP, SERVICE_ARTIFACT

__all__ = [
    "Config",
    "get_config",
    "ConfigDependency",
]

LogLevelLiteral = Literal["debug", "info", "warning", "error"]


class Config(BaseSettings):
    # Service Info
    service_id: str = f"{SERVICE_GROUP}:{SERVICE_ARTIFACT}"
    service_name: str = "Transcriptomics Data Service"
    service_description: str = "Transcriptomics data service for the Bento platform."
    service_url_base_path: str = "http://127.0.0.1:5000"  # Base path to construct URIs from
    service_docs_path: str = "/docs"
    service_openapi_path: str = "/openapi.json"

    # Postgre DB settings
    db_host: str = "tds-db"
    db_port: int = 5432
    db_user: str = "tds_user"
    db_name: str = "tds"
    db_password: str  # Populated from secrets OR env variable

    log_level: LogLevelLiteral = "info"

    cors_origins: tuple[str, ...] = ()

    # Enable/disable your authorization plugin
    authz_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file="./lib/.env",  # authz plugin extra configs
        secrets_dir="/run/secrets/",  # Docker secrets directory
        extra="allow",
        frozen=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            CorsOriginsParsingEnvSettingsSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )


@lru_cache()
def get_config():
    return Config()


ConfigDependency = Annotated[Config, Depends(get_config)]
