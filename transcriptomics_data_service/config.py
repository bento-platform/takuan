from bento_lib.config.pydantic import BentoBaseConfig
from fastapi import Depends
from functools import lru_cache
from typing import Annotated

from .constants import SERVICE_GROUP, SERVICE_ARTIFACT

__all__ = [
    "Config",
    "get_config",
    "ConfigDependency",
]

class Config(BentoBaseConfig):
    service_id: str = f"{SERVICE_GROUP}:{SERVICE_ARTIFACT}"
    service_name: str = "Transcriptomics Data Service"
    service_description: str = "Transcriptomics data service for the Bento platform."
    service_url_base_path: str = "http://127.0.0.1:5000"  # Base path to construct URIs from

    service_docs_path: str = "/docs"
    service_openapi_path: str = "/openapi.json"

    database_uri: str = "postgres://localhost:5432"

@lru_cache()
def get_config():
    return Config()


ConfigDependency = Annotated[Config, Depends(get_config)]
