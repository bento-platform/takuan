from fastapi import APIRouter, HTTPException, status

from transcriptomics_data_service.authz.plugin import authz_plugin
from transcriptomics_data_service.db import DatabaseDependency
from transcriptomics_data_service.logger import LoggerDependency
from transcriptomics_data_service.models import (
    ExperimentResult,
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
    await db.create_experiment_result(exp)
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
