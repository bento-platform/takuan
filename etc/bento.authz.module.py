from bento_lib.auth.middleware.fastapi import FastApiAuthMiddleware
from bento_lib.auth.permissions import P_INGEST_DATA
from bento_lib.auth.resources import RESOURCE_EVERYTHING

from transcriptomics_data_service.config import get_config
from transcriptomics_data_service.logger import get_logger
from transcriptomics_data_service.authz.middleware_base import BaseAuthzMiddleware

config = get_config()
logger = get_logger(config)


class CustomAuthzMiddleware(FastApiAuthMiddleware, BaseAuthzMiddleware):
    """
    Concrete implementation of BaseAuthzMiddleware to authorize with Bento's authorization service/model.
    Essentialy a TDS wrapper for the bento_lib FastApiAuthMiddleware.
    """

    def dep_authorize_ingest(self):
        # TODO authorize with propper permissions and resources
        return self.dep_require_permissions_on_resource(
            permissions=frozenset({P_INGEST_DATA}), resource=RESOURCE_EVERYTHING
        )

    def dep_authorize_normalize(self):
        # TODO authorize with propper permissions and resources
        return self.dep_require_permissions_on_resource(
            permissions=frozenset({P_INGEST_DATA}), resource=RESOURCE_EVERYTHING
        )


authz_middleware = CustomAuthzMiddleware.build_from_fastapi_pydantic_config(config, logger)
