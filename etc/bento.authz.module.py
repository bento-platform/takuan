from typing import Any, Awaitable, Callable, Coroutine
from fastapi import Depends, FastAPI, Request, Response
from bento_lib.auth.middleware.fastapi import FastApiAuthMiddleware
from bento_lib.auth.permissions import P_INGEST_DATA
from bento_lib.auth.resources import RESOURCE_EVERYTHING, build_resource
from starlette.responses import Response

from transcriptomics_data_service.config import get_config
from transcriptomics_data_service.logger import get_logger
from transcriptomics_data_service.authz.middleware_mixin import BaseAuthzMiddleware

config = get_config()
logger = get_logger(config)


class CustomAuthzMiddleware(BaseAuthzMiddleware):
    """
    Concrete implementation of BaseAuthzMiddleware to authorize with Bento's authorization service/model.
    Essentialy a TDS wrapper for the bento_lib FastApiAuthMiddleware.
    """

    def __init__(self, config, logger, enabled: bool = True) -> None:
        self.bento_authz = FastApiAuthMiddleware.build_from_pydantic_config(config, logger)
        self.enabled = enabled

    def attach(self, app: FastAPI):
        app.middleware("http")(self.bento_authz.dispatch)
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Coroutine[Any, Any, Response]:
        # Use the bento_lib authz middleware's dispatch
        return await self.bento_authz.dispatch(request, call_next)

    def dep_public_endpoint(self):
        return self.bento_authz.dep_public_endpoint()

    # INGEST router authz dependency functions

    def dep_authorize_ingest(self):
        # TODO authorize with propper permissions and resources
        return self.bento_authz.dep_require_permissions_on_resource(
            permissions=frozenset({P_INGEST_DATA}), resource=RESOURCE_EVERYTHING
        )

    def dep_authorize_normalize(self):
        # TODO authorize with propper permissions and resources
        return self.bento_authz.dep_require_permissions_on_resource(
            permissions=frozenset({P_INGEST_DATA}), resource=RESOURCE_EVERYTHING
        )

    def mark_authz_done(self, request: Request):
        self.bento_authz.mark_authz_done(request)

authz_middleware = CustomAuthzMiddleware(config, logger)
