from io import StringIO
from logging import Logger
from typing import TypedDict
from fastapi import HTTPException, status
import pandas as pd

from transcriptomics_data_service.db import DatabaseDependency
from transcriptomics_data_service.models import CountTypesEnum, GeneExpression


class BaseIngestionHandler:
    """
    Base class for implementation of data format handling for transcriptomics data.

    Uses the template design pattern, an ingestion follows these steps:
        - Init handler
        - Read file data into a data frame (load_dataframe)
            - Must be implemented in children classes
        - Convert the data frame to a list of GeneExpression (dataframe_to_expressions)
            - Must be implemented in children classes
        - Ingest in the database
    """

    df: pd.DataFrame | None
    logger: Logger

    def __init__(
        self, experiment_result_id: str, db: DatabaseDependency, logger: Logger
    ):
        self.experiment_result_id = experiment_result_id
        self.db = db
        self.logger = logger

    def load_dataframe(self, data: bytes):
        """
        Reads the file data and loads it inside a dataframe.
        """
        raise NotImplementedError()

    def dataframe_to_expressions(
        self, count_type: CountTypesEnum
    ) -> list[GeneExpression]:
        """
        Parses the loaded data frame into a list of GeneExpression for ingestion.
        A count type can be specified in order to indicate if a count is pre-normalised.
        """
        raise NotImplementedError()

    async def ingest(self, count_type: CountTypesEnum = CountTypesEnum.raw.value):
        """
        Writes the GeneExpressions to the database.
        """

        # Check that the experiment exists
        experiment = await self.db.read_experiment_result(self.experiment_result_id)
        if experiment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No experiment result found for provided ID",
            )

        # Parse expressions, implementation dependent (CSV/TSV)
        expressions = self.dataframe_to_expressions(count_type)
        async with self.db.transaction_connection() as conn:
            await self.db.create_or_update_gene_expressions(expressions, conn)


class CSVIngestionHandler(BaseIngestionHandler):
    """
    CSV format is for Raw-Count-Matrix (RCM) ingestion, where each column belongs to a sample,
    and each row to a feature (gene ID, gene name, Ensembl ID, ...).

    Cells are the raw count for the sample/feature pair:
        (gene_A, sample_B) => 789

    CSV ingestion can be used for multi and single sample RCMs.
    """

    def load_dataframe(self, data: bytes):
        """
        Reads the bytes of a CSV file into a dataframe.
        """
        self.df = _parse_csv(data, self.logger)

    def dataframe_to_expressions(self, count_type: CountTypesEnum):
        return [
            GeneExpression(
                gene_code=gene_code,
                sample_id=sample_id,
                experiment_result_id=self.experiment_result_id,
                **{f"{count_type.value}_count": count},
            )
            for gene_code, row in self.df.iterrows()
            for sample_id, count in row.items()
        ]


class ColumnIndices(TypedDict):
    gene_id: int = 0
    abundance: int = 1
    counts: int = 2
    length: int = 3
    counts_from_abundance: 4


class TSVIngestionHandler(BaseIngestionHandler):
    """
    TSV format ingestion is for single sample files ONLY.

    Where each row belongs to a feature (gene ID, gene name, Ensembl ID, ...),
    and the columns contain observed quantities for the sample/feature pair.

    Expected columns are:
        1) gene_id: feature identifier (String)
        2) abundance: normalized transcriptions count (Number)
        3) counts: raw transcriptions count (Number)
        4) length: length of the feature (Number)
        5) countsFromAbundance: TODO is this needed?

    At the moment, any additional column is ignored.

    Since the sample identifier is not in the file's content, TSV ingestions will
    determine the sample identifier as follow:
        - From the sample_id path parameter, if provided
        - From the file name, if sample_id is not provided

    """

    columns: ColumnIndices
    sample_id: str

    def __init__(
        self,
        experiment_result_id: str,
        sample_id: str,
        db: DatabaseDependency,
        logger: Logger,
        columns: ColumnIndices = ColumnIndices(),
    ):
        self.sample_id = sample_id
        self.columns = columns
        super().__init__(experiment_result_id, db, logger)

    def load_dataframe(self, data: bytes):
        self.df = parse_tsv(data, self.logger)

    def dataframe_to_expressions(self, count_type: CountTypesEnum):
        # gene_id           abundance       counts      length      countsFromAbundance
        # ENSG00000000003   0.0447787       29.6875     3616.22     no
        expressions = []
        for _, row in self.df.iterrows():
            expressions.append(
                GeneExpression(
                    gene_code=row[0],
                    sample_id=self.sample_id,
                    experiment_result_id=self.experiment_result_id,
                    raw_count=row[2],
                    **{f"{count_type.value}_count": row[1]},
                )
            )
        return expressions


def parse_tsv(data: bytes, logger: Logger) -> pd.DataFrame:
    buffer = StringIO(data.decode("utf-8"))
    buffer.seek(0)
    try:
        df = pd.read_csv(buffer, header=0, sep="\t")

        # Validating for unique feature IDs
        _check_index_duplicates(df.index, logger)

        return df

    except pd.errors.ParserError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error parsing CSV: {e}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Value error in CSV data: {e}",
        )


def _parse_csv(file_bytes: bytes, logger: Logger) -> pd.DataFrame:
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error parsing CSV: {e}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Value error in CSV data: {e}",
        )


def _check_index_duplicates(index: pd.Index, logger: Logger):
    duplicated = index.duplicated()
    if duplicated.any():
        dupes = index[duplicated]
        err_msg = f"Found duplicated {index.name}: {dupes.values}"
        logger.debug(err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
