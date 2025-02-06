from logging import Logger
from typing import Annotated, Any, Awaitable, Callable, Coroutine, Sequence
from fastapi import Depends, HTTPException, Header, Request, Response
from fastapi.responses import JSONResponse

from transcriptomics_data_service.authz.middleware_base import BaseAuthzMiddleware
from transcriptomics_data_service.config import Config, get_config
from transcriptomics_data_service.logger import get_logger

config = get_config()
logger = get_logger(config)


"""
CUSTOM PLUGIN CONFIGURATION
Extra configurations can be added to the config object by adding
a '.env' file in the plugin mount directory.
Variables placed there will be loaded as lowercase properties

This variable's value can be accessed with: config.api_key
API_KEY="fake-super-secret-api-key"
"""


class ApiKeyAuthzMiddleware(BaseAuthzMiddleware):
    """
    Concrete implementation of BaseAuthzMiddleware to authorize requests based on the provided API key.
    """

    def __init__(self, config: Config, logger: Logger) -> None:
        super().__init__()
        self.enabled = config.authz_enabled
        self.logger = logger

        # Load the api_key from the config's extras
        self.api_key = config.model_extra.get("api_key")
        if self.api_key is None:
            # prevents the server from starting if misconfigured
            raise ValueError("Expected variable 'API_KEY' is not set in the plugin's .env")

    # Middleware lifecycle

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Coroutine[Any, Any, Response]:
        if not self.enabled:
            return await call_next(request)

        # Request was not checked for authz yet
        try:
            res = await call_next(request)
        except HTTPException as e:
            # Catch exceptions raised by authz functions
            self.logger.error(e)
            return JSONResponse(status_code=e.status_code, content=e.detail)

        return res

    # API KEY authorization

    def _dep_check_api_key(self):
        """
        Dependency injection for the API key authorization.
        The inner function checks the x_api_key header to validate the API key.
        Raises an exception that should be caught and handled in the dispatch func.
        """

        async def _inner(x_api_key: Annotated[str, Header()]):
            if x_api_key is None:
                raise HTTPException(status_code=401, detail="Unauthorized: missing API key")
            if x_api_key != self.api_key:
                raise HTTPException(status_code=403, detail="Unauthorized: invalid API key")

        return Depends(_inner)

    def dep_expression_router(self) -> Sequence[Depends]:
        # Require API key check on the expressions router
        return [self._dep_check_api_key()]

    def dep_experiment_result_router(self) -> Sequence[Depends]:
        # Require API key check on the experiment_result router
        return [self._dep_check_api_key()]

    def dep_authz_normalize(self) -> Sequence[Depends]:
        return [self._dep_check_api_key()]

    # NOTE: With an all-or-nothing authz mechanism like an API key,
    # we can place the authz checks at the router level to have a more concise module.


authz_middleware = ApiKeyAuthzMiddleware(config, logger)
