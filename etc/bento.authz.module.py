from bento_lib.auth.middleware.fastapi import FastApiAuthMiddleware
from bento_lib.auth.permissions import P_INGEST_DATA, P_DELETE_DATA, P_QUERY_DATA, Permission
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

    def _dep_perm_data_everything(self, permission: Permission):
        return self.dep_require_permissions_on_resource(
            permissions=frozenset({permission}),
            resource=RESOURCE_EVERYTHING,
            require_token=False,
        )

    # INGESTION router paths

    def dep_authz_ingest(self):
        # TODO authorize with propper permissions and resources
        return self._dep_perm_data_everything(P_INGEST_DATA)

    def dep_authz_normalize(self):
        # TODO authorize with propper permissions and resources
        return self._dep_perm_data_everything(P_INGEST_DATA)

    # EXPERIMENT RESULT router paths

    def dep_authz_get_experiment_result(self):
        return self._dep_perm_data_everything(P_QUERY_DATA)

    def dep_authz_delete_experiment_result(self):
        return self._dep_perm_data_everything(P_DELETE_DATA)

    # EXPRESSIONS router paths

    def dep_authz_expressions_list(self):
        return self._dep_perm_data_everything(P_QUERY_DATA)


authz_middleware = CustomAuthzMiddleware.build_from_fastapi_pydantic_config(config, logger)
