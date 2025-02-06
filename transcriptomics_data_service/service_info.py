import json
import os
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

__all__ = ["ServiceInfoDependency"]

SERVICE_INFO_OVERRIDE_PATH = "/tds/lib/service-info.json"


def read_service_info():
    with open(SERVICE_INFO_OVERRIDE_PATH, "r") as f:
        service_info = json.load(f)
    return service_info


@lru_cache
def get_service_info():
    if os.path.isfile(SERVICE_INFO_OVERRIDE_PATH):
        # Return the custom service-info if provided
        return read_service_info()
    # TODO: default service-info def
    # Otherwise return the default service-info.
    return {"id": "default"}


ServiceInfoDependency = Annotated[dict, Depends(get_service_info)]
