from io import StringIO
from logging import Logger
from fastapi import APIRouter, File, HTTPException, UploadFile, status
import pandas as pd

from transcriptomics_data_service.authz.plugin import authz_plugin
from transcriptomics_data_service.db import DatabaseDependency
from transcriptomics_data_service.logger import LoggerDependency
from transcriptomics_data_service.models import (
    ExperimentResult,
    GeneExpression,
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


@experiment_router.post(
    "/{experiment_result_id}/ingest/tsv",
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
):
    if sample_file.content_type != "text/tsv":
        # raise something
        pass
        

@experiment_router.post(
    "/{experiment_result_id}/ingest/csv",
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
):
    if not (rcm_file.content_type == "text/csv"):
        # raise something
        pass
    
    # Reading and converting uploaded RCM file to DataFrame
    file_bytes = rcm_file.file.read()
    rcm_df = _load_csv(file_bytes, logger)

    experiment_result = await db.read_experiment_result(experiment_result_id)
    if experiment_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No experiment result found for provided ID",
        )

    # Handling ingestion as a transactional operation
    async with db.transaction_connection() as transaction_con:
        gene_expressions: list[GeneExpression] = [
            GeneExpression(
                gene_code=gene_code,
                sample_id=sample_id,
                experiment_result_id=experiment_result_id,
                raw_count=raw_count,
            )
            for gene_code, row in rcm_df.iterrows()
            for sample_id, raw_count in row.items()
        ]

        await db.create_gene_expressions(gene_expressions, transaction_con)

    return {"message": "Ingestion completed successfully"}


def _check_index_duplicates(index: pd.Index, logger: Logger):
    duplicated = index.duplicated()
    if duplicated.any():
        dupes = index[duplicated]
        err_msg = f"Found duplicated {index.name}: {dupes.values}"
        logger.debug(err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)


def _load_csv(file_bytes: bytes, logger: Logger) -> pd.DataFrame:
    buffer = StringIO(file_bytes.decode("utf-8"))
    buffer.seek(0)
    try:
        df = pd.read_csv(buffer, index_col=0, header=0)

        # Validating for unique Gene and Sample IDs
        _check_index_duplicates(df.index, logger)  # Gene IDs
        _check_index_duplicates(df.columns, logger)  # Sample IDs

        # Ensuring raw count values are integers
        df = df.applymap(lambda x: int(x) if pd.notna(x) else None)
        return df

    except pd.errors.ParserError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error parsing CSV: {e}")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Value error in CSV data: {e}",
        )
