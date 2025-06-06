from typing import Annotated, Literal
from asyncpg import UniqueViolationError
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status, Path

from transcriptomics_data_service.authz.plugin import authz_plugin
from transcriptomics_data_service.db import DatabaseDependency
from transcriptomics_data_service.ingestion import (
    RCMIngestionHandler,
    SampleIngestionHandler,
)
from transcriptomics_data_service.logger import LoggerDependency
from transcriptomics_data_service.models import (
    CountTypesEnum,
    ExperimentResult,
    GeneExpressionMapper,
    PaginatedRequest,
    SamplesResponse,
    FeaturesResponse,
)

__all__ = ["experiment_router"]

experiment_router = APIRouter(prefix="/experiment", dependencies=authz_plugin.dep_experiment_result_router())

DEFAULT_PAGINATION = PaginatedRequest(page=1, page_size=100)


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
        logger.error(err_msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
    db: DatabaseDependency,
    logger: LoggerDependency,
    params: PaginatedRequest = DEFAULT_PAGINATION,
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
    db: DatabaseDependency,
    logger: LoggerDependency,
    params: PaginatedRequest = DEFAULT_PAGINATION,
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
    # description="Ingest detailed counts for a single sample TSV or CSV file.",
    summary="Ingest detailed counts for a single sample TSV or CSV file.",
    description="Use this endpoint to ingest raw counts and/or pre-normalized gene expressions at the same time.",
)
async def ingest_single(
    db: DatabaseDependency,
    logger: LoggerDependency,
    experiment_result_id: Annotated[str, Path(description="ID of an existing `ExperimentResult` to ingest into")],
    data: Annotated[bytes, File(description="TSV/CSV file bytes")],
    sample_id: Annotated[str, Form(description="Sample unique identifier")],
    file_type: Annotated[
        Literal["csv", "tsv"],
        Form(description="Specify file format for parsing, 'tsv' by default if not specified"),
    ] = "tsv",
    feature_col: Annotated[str, Form(description="Feature column mapper, defaults to 'gene_id'")] = "gene_id",
    raw_count_col: Annotated[str | None, Form(description="Raw count column mapper")] = "",
    tpm_count_col: Annotated[str | None, Form(description="TPM count column mapper")] = "",
    tmm_count_col: Annotated[str | None, Form(description="TMM count column mapper")] = "",
    getmm_count_col: Annotated[str | None, Form(description="GETMM count column mapper")] = "",
    fpkm_count_col: Annotated[str | None, Form(description="FPKM count column mapper")] = "",
):
    """
    Ingests data for a single sample in an ExperimentResult.
    The sample_id must be provided in the request.
    """
    # Reading and converting uploaded RCM file to DataFrame
    handler = SampleIngestionHandler(experiment_result_id, sample_id, db, logger)

    # Cannot use this Pydantic model as a Form parameter with multipart
    # https://fastapi.tiangolo.com/tutorial/request-forms-and-files/#define-file-and-form-parameters
    data_mapper = GeneExpressionMapper(
        feature_col=feature_col,
        raw_count_col=raw_count_col,
        tpm_count_col=tpm_count_col,
        tmm_count_col=tmm_count_col,
        getmm_count_col=getmm_count_col,
        fpkm_count_col=fpkm_count_col,
    )
    handler.load_dataframe(data, file_type, data_mapper)
    n_created = await handler.ingest()
    if not n_created:
        return {"message": "Completed with no errors but no new GeneExpression could be created, inspect input data."}
    return {"message": f"Ingested {n_created} GeneExpressions successfully"}


@experiment_router.post(
    "/{experiment_result_id}/ingest",
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
    handler = RCMIngestionHandler(experiment_result_id, db, logger)
    handler.load_dataframe(file_bytes)
    await handler.ingest(count_type)

    return {"message": "Ingestion completed successfully"}
