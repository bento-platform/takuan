from logging import Logger
from typing import Any, Awaitable, Callable, Coroutine
from fastapi import Depends, FastAPI, Request, Response
from starlette.responses import Response

from transcriptomics_data_service.authz.middleware_base import BaseAuthzMiddleware
from transcriptomics_data_service.config import Config, get_config
from transcriptomics_data_service.logger import get_logger

config = get_config()
logger = get_logger(config)


class ApiKeyAuthzMiddleware(BaseAuthzMiddleware):
    """
    Concrete implementation of BaseAuthzMiddleware to authorize requests based on the provided API key.
    """

    def __init__(self, config: Config, logger: Logger) -> None:
        super().__init__()
        self.enabled = config.bento_authz_enabled
        self.logger = logger

    def attach(self, app: FastAPI):
        app.middleware("http")(self.dispatch)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Coroutine[Any, Any, Response]:
        if not self.enabled:
            return await call_next(request)

    def dep_authz_ingest(self):
        # TODO authorize with propper permissions and resources
        pass

    def dep_authz_normalize(self):
        # TODO authorize with propper permissions and resources
        pass

    

authz_middleware = ApiKeyAuthzMiddleware()
