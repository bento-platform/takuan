import importlib.util
from types import ModuleType

from transcriptomics_data_service.authz.middleware_base import BaseAuthzMiddleware
from transcriptomics_data_service.config import get_config
from transcriptomics_data_service.logger import get_logger

__all__ = ["authz_plugin"]

config = get_config()


def import_module_from_path(path) -> None | ModuleType:
    if config.bento_authz_enabled:
        spec = importlib.util.spec_from_file_location("authz_plugin", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.authz_middleware
    else:
        return None


# Get the concrete authz middleware from the provided plugin module
authz_plugin = import_module_from_path("/tds/lib/authz.module.py")
