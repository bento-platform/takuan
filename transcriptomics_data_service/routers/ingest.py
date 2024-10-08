from fastapi import APIRouter, File, UploadFile, status
import csv
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

    # rcm["WASH6P"]
    # {'GeneID': 'WASH6P', '<BIOSAMPLE_ID>': '63', }

    return
