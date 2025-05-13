from io import StringIO
from logging import Logger
from fastapi import HTTPException, status
import pandas as pd

from transcriptomics_data_service.db import DatabaseDependency
from transcriptomics_data_service.models import (
    CountTypesEnum,
    GeneExpression,
    GeneExpressionMapper,
)


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

    def __init__(self, experiment_result_id: str, db: DatabaseDependency, logger: Logger):
        self.experiment_result_id = experiment_result_id
        self.db = db
        self.logger = logger

    def load_dataframe(self, data: bytes):
        """
        Reads the file data and loads it inside a dataframe in the 'df' attribute.
        """
        raise NotImplementedError()

    def dataframe_to_expressions(self, count_type: CountTypesEnum) -> list[GeneExpression]:
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

        # Parse expressions
        expressions = self.dataframe_to_expressions(count_type)
        async with self.db.transaction_connection() as conn:
            await self.db.create_or_update_gene_expressions(expressions, conn)

    def _check_index_duplicates(self, index: pd.Index):
        duplicated = index.duplicated()
        if duplicated.any():
            dupes = index[duplicated]
            err_msg = f"Found duplicated {index.name}: {dupes.values}"
            self.logger.debug(err_msg)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)


class RCMIngestionHandler(BaseIngestionHandler):
    """
    For Raw-Count-Matrix (RCM) ingestion, where each column belongs to a sample,
    and each row to a feature (gene ID, gene name, Ensembl ID, ...).

    Cells are the raw count for the sample/feature pair:
        (gene_A, sample_B) => 789

    CSV ingestion can be used for multi and single sample RCMs.
    """

    def load_dataframe(self, data: bytes):
        """
        Reads the bytes of a CSV file into a dataframe.
        """
        buffer = StringIO(data.decode("utf-8"))
        buffer.seek(0)
        try:
            # sep=None to infer separator (handle CSV and TSV)
            df = pd.read_csv(buffer, index_col=0, header=0, sep=None)

            # Validating for unique Gene and Sample IDs
            self._check_index_duplicates(df.index)  # Gene IDs
            self._check_index_duplicates(df.columns)  # Sample IDs

            # Ensuring raw count values are integers
            df = df.applymap(lambda x: int(x) if pd.notna(x) else None)
            self.df = df

        except pd.errors.ParserError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error parsing data: {e}",
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Value error in data: {e}",
            )

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


class SampleIngestionHandler(BaseIngestionHandler):
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

    sample_id: str
    mapper: GeneExpressionMapper

    def __init__(
        self,
        experiment_result_id: str,
        sample_id: str,
        db: DatabaseDependency,
        logger: Logger,
    ):
        self.sample_id = sample_id
        super().__init__(experiment_result_id, db, logger)

    def _validate_mapper_field(self, df: pd.DataFrame, mapping: str | None) -> bool:
        """
        Returns True if the mapping is not present in the file's headers
        """
        return mapping and mapping not in df

    def load_dataframe(self, data: bytes, mapper: GeneExpressionMapper | None):
        buffer = StringIO(data.decode("utf-8"))
        buffer.seek(0)
        try:
            # sep=None to infer separator (handle CSV and TSV)
            df = pd.read_csv(
                buffer,
                header=0,
                sep=None,
                engine="python",  # C engine cannot infer if data is CSV or TSV
            )

            # Validating for unique feature IDs
            self._check_index_duplicates(df.index)

            invalid_mappings: list[str] = []
            for col_map in [
                mapper.feature_col,
                mapper.raw_count_col,
                mapper.tpm_count_col,
                mapper.tmm_count_col,
                mapper.getmm_count_col,
                mapper.fpkm_count_col,
            ]:
                if self._validate_mapper_field(df, col_map):
                    invalid_mappings.append(col_map)

            if invalid_mappings:
                err_msg = f"The following provided column mappings are not in the data: {", ".join(invalid_mappings)}"
                self.logger.warning(err_msg)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

            # validate mapping fields exist in the file's headers
            self._validate_mapper_field(df, mapper.raw_count_col)
            self._validate_mapper_field(df, mapper.tpm_count_col)
            self._validate_mapper_field(df, mapper.tmm_count_col)
            self._validate_mapper_field(df, mapper.getmm_count_col)
            self._validate_mapper_field(df, mapper.fpkm_count_col)

            self.df = df
            self.mapper = mapper

        except pd.errors.ParserError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error parsing data: {e}",
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Value error in data: {e}",
            )

    def dataframe_to_expressions(self, count_type: CountTypesEnum):
        # gene_id           abundance       counts      length      countsFromAbundance
        # ENSG00000000003   0.0447787       29.6875     3616.22     no
        expressions = []
        for _, row in self.df.iterrows():
            expr = GeneExpression(
                # required colums
                experiment_result_id=self.experiment_result_id,
                sample_id=self.sample_id,
                gene_code=row.loc[self.mapper.feature_col],
                # optional normalized data columns
                raw_count=(row.loc[self.mapper.raw_count_col] if self.mapper.raw_count_col else None),
                tpm_count=(row.loc[self.mapper.tpm_count_col] if self.mapper.tpm_count_col else None),
                tmm_count=(row.loc[self.mapper.tmm_count_col] if self.mapper.tmm_count_col else None),
                getmm_count=(row.loc[self.mapper.getmm_count_col] if self.mapper.getmm_count_col else None),
                fpkm_count=(row.loc[self.mapper.fpkm_count_col] if self.mapper.fpkm_count_col else None),
            )
            expressions.append(expr)
        return expressions

    def _read_sample_data_df(self, data: bytes) -> pd.DataFrame:
        buffer = StringIO(data.decode("utf-8"))
        buffer.seek(0)
        try:
            # sep=None to infer separator (handle CSV and TSV)
            df = pd.read_csv(buffer, header=0, sep=None)

            # Validating for unique feature IDs
            self._check_index_duplicates(df.index)

            return df

        except pd.errors.ParserError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error parsing data: {e}",
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Value error in data: {e}",
            )
