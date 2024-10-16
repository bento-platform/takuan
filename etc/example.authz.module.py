from logging import Logger
from typing import Annotated, Any, Awaitable, Callable, Coroutine
from fastapi import Depends, FastAPI, HTTPException, Header, Request, Response
from fastapi.responses import JSONResponse
from starlette.responses import Response

from transcriptomics_data_service.authz.middleware_base import BaseAuthzMiddleware
from transcriptomics_data_service.config import Config, get_config
from transcriptomics_data_service.logger import get_logger

config = get_config()
logger = get_logger(config)

# The valid api key for authorization
API_KEY = "fake-super-secret-api-key"


class ApiKeyAuthzMiddleware(BaseAuthzMiddleware):
    """
    Concrete implementation of BaseAuthzMiddleware to authorize requests based on the provided API key.
    """

    def __init__(self, config: Config, logger: Logger) -> None:
        super().__init__()
        self.enabled = config.bento_authz_enabled
        self.logger = logger

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

    # API KEY authorization
    def dep_app(self):
        """
        API-level dependency injection
        Injects a required header for the API key authz: x_api_key
        OpenAPI automatically includes it on all paths.
        """

        async def _inner(x_api_key: Annotated[str, Header()]):
            return x_api_key

        return [Depends(_inner)]

    def _dep_check_api_key(self):
        """
        Dependency injection for the API key authorization.
        The inner function checks the x_api_key header to validate the API key.
        Raises an exception that should be caught and handled in the dispatch func.
        """

        async def _inner(x_api_key: Annotated[str, Header()]):
            if x_api_key != API_KEY:
                raise HTTPException(status_code=403, detail="Unauthorized: invalid API key")

        return Depends(_inner)

    # Authz logic: only check for valid API key

    def dep_authz_ingest(self):
        return self._dep_check_api_key()

    def dep_authz_normalize(self):
        return self._dep_check_api_key()

    def dep_authz_delete_experiment_result(self):
        return self._dep_check_api_key()

    def dep_authz_expressions_list(self):
        return self._dep_check_api_key()

    def dep_authz_get_experiment_result(self):
        return self._dep_check_api_key()


authz_middleware = ApiKeyAuthzMiddleware(config, logger)
