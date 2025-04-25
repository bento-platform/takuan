from asyncpg import UniqueViolationError
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from transcriptomics_data_service.authz.plugin import authz_plugin
from transcriptomics_data_service.db import DatabaseDependency
from transcriptomics_data_service.ingestion import CSVIngestionHandler, TSVIngestionHandler
from transcriptomics_data_service.logger import LoggerDependency
from transcriptomics_data_service.models import (
    CountTypesEnum,
    ExperimentResult,
    NormalizationMethodEnum,
    PaginatedRequest,
    SamplesResponse,
    FeaturesResponse,
)

__all__ = ["experiment_router"]

experiment_router = APIRouter(prefix="/experiment", dependencies=authz_plugin.dep_experiment_result_router())


async def get_experiment_samples_handler(
    experiment_result_id: str,
    params: PaginatedRequest,
    db: DatabaseDependency,
    logger: LoggerDependency,
) -> SamplesResponse:
    """
    Handler for fetching and returning samples for a experiment_result_id.
    """
    logger.info(f"Received query parameters for samples: {params}")

    samples, total_records = await db.fetch_experiment_samples(
        experiment_result_id=experiment_result_id, pagination=params
    )

    if not samples:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No samples found for experiment '{experiment_result_id}'.",
        )

    total_pages = (total_records + params.page_size - 1) // params.page_size

    return SamplesResponse(
        page=params.page,
        page_size=params.page_size,
        total_records=total_records,
        total_pages=total_pages,
        samples=samples,
    )


async def get_experiment_features_handler(
    experiment_result_id: str,
    params: PaginatedRequest,
    db: DatabaseDependency,
    logger: LoggerDependency,
) -> FeaturesResponse:
    """
    Handler for fetching and returning features for a experiment_result_id.
    """
    logger.info(f"Received query parameters for features: {params}")

    features, total_records = await db.fetch_experiment_features(
        experiment_result_id=experiment_result_id, pagination=params
    )

    if not features:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No features found for experiment '{experiment_result_id}'.",
        )

    total_pages = (total_records + params.page_size - 1) // params.page_size

    return FeaturesResponse(
        page=params.page,
        page_size=params.page_size,
        total_records=total_records,
        total_pages=total_pages,
        features=features,
    )


@experiment_router.post(
    "",
    status_code=status.HTTP_200_OK,
    dependencies=authz_plugin.dep_authz_create_experiment_result(),
)
async def create_experiment(db: DatabaseDependency, logger: LoggerDependency, exp: ExperimentResult):
    try:
        await db.create_experiment_result(exp)
    except UniqueViolationError:
        err_msg = f"Duplicate key error: experiment_result_id={exp.experiment_result_id} already exists."
        logger.warning(err_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=err_msg,
        )
    logger.info(f"Created experiment row with ID: {exp.experiment_result_id}")


@experiment_router.get("", dependencies=authz_plugin.dep_authz_list_experiment_results())
async def get_all_experiments(db: DatabaseDependency):
    experiments, _ = await db.fetch_experiment_results(pagination=None)
    return experiments


@experiment_router.get(
    "/{experiment_result_id}",
    dependencies=authz_plugin.dep_authz_get_experiment_result(),
)
async def get_experiment_result(db: DatabaseDependency, experiment_result_id: str):
    return await db.read_experiment_result(experiment_result_id)


@experiment_router.post(
    "/{experiment_result_id}/samples",
    status_code=status.HTTP_200_OK,
    response_model=SamplesResponse,
    dependencies=authz_plugin.dep_authz_get_experiment_result(),
)
async def post_experiment_samples(
    experiment_result_id: str,
    params: PaginatedRequest,
    db: DatabaseDependency,
    logger: LoggerDependency,
):
    return await get_experiment_samples_handler(experiment_result_id, params, db, logger)


@experiment_router.post(
    "/{experiment_result_id}/features",
    status_code=status.HTTP_200_OK,
    response_model=FeaturesResponse,
    dependencies=authz_plugin.dep_authz_get_experiment_result(),
)
async def post_experiment_features(
    experiment_result_id: str,
    params: PaginatedRequest,
    db: DatabaseDependency,
    logger: LoggerDependency,
):
    return await get_experiment_features_handler(experiment_result_id, params, db, logger)


@experiment_router.delete(
    "/{experiment_result_id}",
    dependencies=authz_plugin.dep_authz_delete_experiment_result(),
)
async def delete_experiment_result(db: DatabaseDependency, experiment_result_id: str):
    await db.delete_experiment_result(experiment_result_id)


@experiment_router.post(
    "/{experiment_result_id}/ingest/single",
    status_code=status.HTTP_200_OK,
    # Injects the plugin authz middleware dep_authorize_ingest function
    dependencies=authz_plugin.dep_authz_ingest(),
    description="Ingest detailed counts for a single sample TSV file",
)
async def ingest_tsv(
    db: DatabaseDependency,
    logger: LoggerDependency,
    experiment_result_id: str,
    sample_file: UploadFile = File(...),
    sample_id: str = None,
    norm_type: NormalizationMethodEnum = None,
):
    # Use sample ID param if provided, otherwise use the uploded file name
    if sample_id is None:
        sample_id = sample_file.filename

    # Reading and converting uploaded RCM file to DataFrame
    handler = TSVIngestionHandler(experiment_result_id, sample_id, db, logger)
    file_bytes = sample_file.file.read()
    handler.load_dataframe(file_bytes)
    await handler.ingest(norm_type)

    return {"message": "Ingestion completed successfully"}


@experiment_router.post(
    "/{experiment_result_id}/ingest/matrix",
    status_code=status.HTTP_200_OK,
    # Injects the plugin authz middleware dep_authorize_ingest function
    dependencies=authz_plugin.dep_authz_ingest(),
    description="Ingest a raw counts matrix RCM into an existing experiment",
)
async def ingest(
    db: DatabaseDependency,
    logger: LoggerDependency,
    experiment_result_id: str,
    rcm_file: UploadFile = File(...),
    count_type: CountTypesEnum | None = None,
):
    if count_type is None:
        count_type = CountTypesEnum.raw

    # Reading and converting uploaded RCM file to DataFrame
    file_bytes = rcm_file.file.read()
    handler = CSVIngestionHandler(experiment_result_id, db, logger)
    handler.load_dataframe(file_bytes)
    await handler.ingest(count_type)

    return {"message": "Ingestion completed successfully"}
