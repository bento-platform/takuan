from bento_lib.apps.fastapi import BentoFastAPI

from . import __version__
from .config import get_config
from .constants import BENTO_SERVICE_KIND, SERVICE_TYPE
from .logger import get_logger

BENTO_SERVICE_INFO = {
    "serviceKind": BENTO_SERVICE_KIND,
    "dataService": True,
    "workflowProvider": True,
    "gitRepository": "https://github.com/bento-platform/transcriptomics_data_service",
}

config_for_setup = get_config()
logger_for_setup = get_logger(config_for_setup)

app = BentoFastAPI(
    authz_middleware=None,
    config=config_for_setup,
    logger=logger_for_setup,
    bento_extra_service_info=BENTO_SERVICE_INFO,
    service_type=SERVICE_TYPE,
    version=__version__,
)
