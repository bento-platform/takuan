from fastapi import Request
from bento_lib.auth.middleware.fastapi import FastApiAuthMiddleware

from transcriptomics_data_service.config import get_config
from transcriptomics_data_service.logger import get_logger

config = get_config()
logger = get_logger(config)

bento_authz = FastApiAuthMiddleware.build_from_pydantic_config(config, logger)

async def get_current_user_authorization(req: Request):
    # TODO use as a propper middleware, or simply as an injectable with method calls?
    print("************ This middleware performs authz checks for Bento")
    return True
