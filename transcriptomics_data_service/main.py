from contextlib import asynccontextmanager
from urllib.parse import urlparse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from transcriptomics_data_service.db import get_db
from transcriptomics_data_service.models import ServiceInfo
from transcriptomics_data_service.routers.experiment_results import experiment_router
from transcriptomics_data_service.routers.normalization import normalization_router
from transcriptomics_data_service.routers.expressions import expressions_router
from transcriptomics_data_service.authz.plugin import authz_plugin
from transcriptomics_data_service.service_info import ServiceInfoDependency

from . import __version__
from .config import get_config
from .constants import BENTO_SERVICE_KIND
from .logger import get_logger

# TODO should probably be mounted as a JSON for usage outside Bento
# could also be used to indicate if deployment is Bento specific of not
BENTO_SERVICE_INFO = {
    "serviceKind": BENTO_SERVICE_KIND,
    "dataService": False,  # temp off to quiet bento-web errors
    "workflowProvider": False,  # temp off to quiet bento-web errors
    "gitRepository": "https://github.com/bento-platform/transcriptomics_data_service",
}

config_for_setup = get_config()
logger_for_setup = get_logger(config_for_setup)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db = get_db(config_for_setup, logger_for_setup)
    await db.migrate()

    yield

    await db.close()


app = FastAPI(
    title=config_for_setup.service_name,
    root_path=urlparse(config_for_setup.service_url_base_path).path,
    docs_url=config_for_setup.service_docs_path,
    openapi_url=config_for_setup.service_openapi_path,
    version=__version__,
    lifespan=lifespan,
    dependencies=authz_plugin.dep_app(),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config_for_setup.cors_origins,
    allow_credentials=True,
    allow_headers=["Authorization", "Cache-Control"],
    allow_methods=["*"],
)

# Add authz middleware if AUTHZ_ENABLED
if config_for_setup.authz_enabled:
    authz_plugin.attach(app)

app.include_router(experiment_router)
app.include_router(normalization_router)
app.include_router(expressions_router)


@app.get("/service-info")
def get_service_info(service_info: ServiceInfoDependency) -> ServiceInfo:
    return service_info
