from logging import Logger
from typing import Any, Awaitable, Callable, Coroutine
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from opa_client.opa import OpaClient  # CUSTOM PLUGIN DEPENDENCY

from transcriptomics_data_service.authz.middleware_base import BaseAuthzMiddleware
from transcriptomics_data_service.config import Config, get_config
from transcriptomics_data_service.logger import get_logger

config = get_config()
logger = get_logger(config)

"""
CUSTOM PLUGIN DEPENDENCY
Extra dependencies can be added if the authz plugin requires them.
In this example, the authz module imports the OPA client.
Since OPA does not ship with TDS, a requirements.txt file must be placed under 'lib'.
"""


class OPAAuthzMiddleware(BaseAuthzMiddleware):
    """
    Concrete implementation of BaseAuthzMiddleware to authorize requests with OPA.
    """

    def __init__(self, config: Config, logger: Logger) -> None:
        super().__init__()
        self.enabled = config.authz_enabled
        self.logger = logger

        # Get custom OPA configs from lib/.env
        opa_host = config.model_extra.get("opa_host")
        opa_port = int(config.model_extra.get("opa_host_port"))

        # Init the OPA client with the server
        self.opa_client = OpaClient(host=opa_host, port=opa_port)

        # This is not pointing to a real OPA server.
        # Will raise an exception if connection is invalid.
        self.logger.info(self.opa_client.check_connection())

    # Middleware lifecycle

    def attach(self, app: FastAPI):
        app.middleware("http")(self.dispatch)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Coroutine[Any, Any, Response]:
        if not self.enabled:
            return await call_next(request)

        try:
            res = await call_next(request)
        except HTTPException as e:
            # Catch exceptions raised by authz functions
            self.logger.error(e)
            return JSONResponse(status_code=e.status_code, content=e.detail)

        return res

    # OPA authorization function
    def _dep_check_opa(self):
        async def inner(request: Request):
            # Check the permission using the OPA client.
            # We assume true for the sake of the demonstration
            # authz_result = await self.opa_client.check_permission()
            authz_result = True
            if not authz_result:
                raise HTTPException(status_code=403, detail="Unauthorized: policy evaluation failed")

        return Depends(inner)

    # Authz logic: OPA check injected at endpoint levels

    def dep_authz_ingest(self):
        return [self._dep_check_opa()]

    def dep_authz_normalize(self):
        return [self._dep_check_opa()]

    def dep_authz_delete_experiment_result(self):
        return [self._dep_check_opa()]

    def dep_authz_expressions_list(self):
        return [self._dep_check_opa()]

    def dep_authz_get_experiment_result(self):
        return [self._dep_check_opa()]


authz_middleware = OPAAuthzMiddleware(config, logger)
