from logging import Logger
import pandas as pd

from transcriptomics_data_service.routers.experiment_results import _load_csv

class BaseIngestionHandler:
    df: pd.DataFrame | None
    logger: Logger

    def __init__(self, experiment_result_id: str, logger: Logger):
        self.experiment_result_id = experiment_result_id
        self.logger = logger

    def load_dataframe(data: bytes):
        # Reads the bytes into a Pandas DF from CSV/TSV
        pass

    async def ingest():
        # Writes dataframe contents to the DB
        # TODO: arg for pre-normalized ingestions
        pass

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
        self.df = _load_csv(data, self.logger)

    async def ingest():
        # Writes dataframe contents to the DB
        pass

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

    def load_dataframe(self, data: bytes):
        # gene_id           abundance       counts      length      countsFromAbundance
        # ENSG00000000003   0.0447787       29.6875     3616.22     no
        # self.df = _load_csv(data, self.logger)
        pass

    async def ingest():
        
        pass
