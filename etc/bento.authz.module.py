from bento_lib.auth.middleware.fastapi import FastApiAuthMiddleware
from bento_lib.auth.permissions import P_INGEST_DATA, P_DELETE_DATA, P_QUERY_DATA, Permission
from bento_lib.auth.resources import RESOURCE_EVERYTHING

from transcriptomics_data_service.config import get_config
from transcriptomics_data_service.logger import get_logger
from transcriptomics_data_service.authz.middleware_base import BaseAuthzMiddleware

config = get_config()
logger = get_logger(config)

# TODO add Bento specific project/dataset ownership pattern to experiment_result_id

class BentoAuthzMiddleware(FastApiAuthMiddleware, BaseAuthzMiddleware):
    """
    Concrete implementation of BaseAuthzMiddleware to authorize with Bento's authorization service/model.
    Extends the bento-lib FastApiAuthMiddleware, which includes all the middleware lifecycle and authorization logic.

    Notes:
        - This middleware plugin will only work with a Bento authorization-service.
        - TDS should be able to perform HTTP requests on the authz service url: `config.bento_authz_service_url`
    """

    def _dep_perm_data_everything(self, permission: Permission):
        return self.dep_require_permissions_on_resource(
            permissions=frozenset({permission}),
            resource=RESOURCE_EVERYTHING,
        )

    # INGESTION router paths

    def dep_authz_ingest(self):
        return self._dep_perm_data_everything(P_INGEST_DATA)

    def dep_authz_normalize(self):
        return self._dep_perm_data_everything(P_INGEST_DATA)

    # EXPERIMENT RESULT router paths

    def dep_authz_get_experiment_result(self):
        return self._dep_perm_data_everything(P_QUERY_DATA)

    def dep_authz_delete_experiment_result(self):
        return self._dep_perm_data_everything(P_DELETE_DATA)

    # EXPRESSIONS router paths

    def dep_authz_expressions_list(self):
        return self._dep_perm_data_everything(P_QUERY_DATA)


authz_middleware = BentoAuthzMiddleware.build_from_fastapi_pydantic_config(config, logger)
