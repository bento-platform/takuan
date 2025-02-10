import importlib.util
from types import ModuleType

from transcriptomics_data_service.authz.middleware_base import BaseAuthzMiddleware
from transcriptomics_data_service.config import Config, get_config

__all__ = ["authz_plugin"]


def import_module_from_path(path, config: Config) -> None | ModuleType:
    if config.authz_enabled:
        spec = importlib.util.spec_from_file_location("authz_plugin", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.authz_middleware
    else:
        # We return an authz middleware that does nothing if authz is disabled
        # This middleware is never attached and only serves dependency injection signatures
        return BaseAuthzMiddleware()


# Get the concrete authz middleware from the provided plugin module
authz_plugin: BaseAuthzMiddleware = import_module_from_path("./lib/authz.module.py", get_config())
