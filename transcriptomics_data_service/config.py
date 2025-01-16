from bento_lib.config.pydantic import BentoFastAPIBaseConfig
from fastapi import Depends
from functools import lru_cache
from typing import Annotated

from pydantic_settings import SettingsConfigDict

from .constants import SERVICE_GROUP, SERVICE_ARTIFACT

__all__ = [
    "Config",
    "get_config",
    "ConfigDependency",
]


class Config(BentoFastAPIBaseConfig):
    service_id: str = f"{SERVICE_GROUP}:{SERVICE_ARTIFACT}"
    service_name: str = "Transcriptomics Data Service"
    service_description: str = "Transcriptomics data service for the Bento platform."
    service_url_base_path: str = "http://127.0.0.1:5000"  # Base path to construct URIs from

    db_host: str = "tds-db"
    db_port: int = 5432
    db_user: str = "tds_user"
    db_password: str    # Populated from secrets OR env variable

    # Allow extra configs from /tds/lib/.env for custom authz configuration
    model_config = SettingsConfigDict(env_file="./lib/.env", secrets_dir="/run/secrets/" , extra="allow")


@lru_cache()
def get_config():
    return Config()


ConfigDependency = Annotated[Config, Depends(get_config)]
