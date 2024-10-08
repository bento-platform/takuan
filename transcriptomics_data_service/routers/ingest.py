from fastapi import APIRouter, File, UploadFile, status
import csv
import json
from io import StringIO

from transcriptomics_data_service.db import DatabaseDependency

__all__ = [""]

ingest_router = APIRouter()

GENE_ID_KEY = "GeneID"


@ingest_router.post(
    "/ingest/{experiment_result_id}/genome/{genome_id}/ensembl/{ensembl_id}", status_code=status.HTTP_200_OK
)
async def ingest(
    db: DatabaseDependency, experiment_result_id: str, genome_id: str, ensembl_id: str, rcm_file: UploadFile = File(...)
):
    # Read and process rcm file
    file_bytes = rcm_file.file.read()
    buffer = StringIO(file_bytes.decode("utf-8"))

    # Read each row as a dict
    # Store rows by gene id
    rcm = {}
    for row in csv.DictReader(buffer):
        print(row)
        rcm[row[GENE_ID_KEY]] = row

    # rcm["WASH6P"]  would return something like:
    # {'GeneID': 'WASH6P', '<BIOSAMPLE_ID_1>': '63', '<BIOSAMPLE_ID_2>: '0', ...}
    # TODO read counts as integers

    # TODO perform the ingestion in a transaction
    # For each matrix: create one row in ExperimentResult
    # For each cell in the matrix: create one row in GeneExpression

    return


@ingest_router.post("/normalize/{experiment_result_id}")
async def normalize(
    db: DatabaseDependency,
    experiment_result_id: str,
    features_lengths_file: UploadFile = File(...),
    status_code=status.HTTP_200_OK,
):
    features_lengths = json.load(features_lengths_file.file)
    # TODO validate shape
    # TODO validate experiment_result_id exists
    # TODO algorithm selection argument?
    # TODO perform the normalization in a transaction
    return
