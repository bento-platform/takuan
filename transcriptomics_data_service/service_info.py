import json
import os
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from transcriptomics_data_service import __version__

__all__ = ["ServiceInfoDependency"]

SERVICE_INFO_OVERRIDE_PATH = "/tds/lib/service-info.json"


def read_service_info(path: str):
    with open(path, "r") as f:
        service_info = json.load(f)
    return service_info


@lru_cache
def get_service_info():
    if os.path.isfile(SERVICE_INFO_OVERRIDE_PATH):
        # Return the custom service-info if provided
        return read_service_info(SERVICE_INFO_OVERRIDE_PATH)

    # Otherwise return the default service-info.
    return {
        "id": "ca.c3g.bento:tds",
        "name": "Transcriptomics Data Service",
        "type": {"group": "ca.c3g.bento", "artifact": "tds", "version": __version__},
        "organization": {"name": "C3G", "url": "https://www.computationalgenomics.ca"},
        "version": __version__,
    }


ServiceInfoDependency = Annotated[dict, Depends(get_service_info)]
