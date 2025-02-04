from logging import Logger
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from io import StringIO
import pandas as pd

from transcriptomics_data_service.db import DatabaseDependency
from transcriptomics_data_service.logger import LoggerDependency
from transcriptomics_data_service.models import GeneExpression
from transcriptomics_data_service.authz.plugin import authz_plugin

__all__ = ["ingest_router"]

ingest_router = APIRouter(dependencies=authz_plugin.dep_ingest_router())

# TODO make configurable? an argument?
GENE_ID_KEY = "GeneID"


@ingest_router.post(
    # "/ingest/{experiment_result_id}",
    "/experiment/{experiment_result_id}/ingest/",
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
