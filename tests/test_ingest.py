import os
from pathlib import Path
from fastapi import status
from fastapi.testclient import TestClient

from transcriptomics_data_service.config import get_config
from httpx._types import HeaderTypes

from transcriptomics_data_service.logger import get_logger


config = get_config()
logger = get_logger(config)

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "data")
RCM_FILE_PATH = f"{TEST_FILES_DIR}/rcm_file.csv"
INGEST_ARGS = dict(
    exp_id="exp-12345",
    assembly_name="GRCh38",
    assembly_id="GCF_000001405.26",
)


def _ingest_rcm_file(
    client: TestClient,
    exp_id: str,
    assembly_name: str,
    assembly_id: str,
    file_path: Path,
    headers: HeaderTypes | None = None,
):
    with open(file_path, "rb") as file:
        res = client.post(
            url=f"/ingest/{exp_id}/assembly-name/{assembly_name}/assembly-id/{assembly_id}",
            files=[("rcm_file", file)],
            headers=headers,
        )
    logger.debug(res.json())
    return res


def test_ingest_missing_api_key(test_client: TestClient, db_cleanup):
    # No API key
    response = _ingest_rcm_file(test_client, file_path=RCM_FILE_PATH, **INGEST_ARGS)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_ingest_unauthorized(test_client, authz_headers_bad, db_cleanup):
    response = _ingest_rcm_file(
        test_client,
        file_path=RCM_FILE_PATH,
        headers=authz_headers_bad,
        **INGEST_ARGS,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_ingest_authorized(test_client, authz_headers, db_cleanup):
    response = _ingest_rcm_file(
        test_client,
        file_path=RCM_FILE_PATH,
        headers=authz_headers,
        **INGEST_ARGS,
    )
    assert response.status_code == status.HTTP_200_OK


def test_ingest_authorized_duplicate(test_client, authz_headers, db_cleanup):
    response = _ingest_rcm_file(
        test_client,
        file_path=f"{TEST_FILES_DIR}/rcm_file_duplicates.csv",
        headers=authz_headers,
        **INGEST_ARGS,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_ingest_parser_error(test_client, authz_headers, db_cleanup):
    response = _ingest_rcm_file(
        test_client,
        file_path=f"{TEST_FILES_DIR}/rcm_file_bad_values.csv",
        headers=authz_headers,
        **INGEST_ARGS,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_ingest_invalid_csv(test_client, authz_headers, db_cleanup):
    response = _ingest_rcm_file(
        test_client,
        file_path=f"{TEST_FILES_DIR}/rcm_file_bad_column.csv",
        headers=authz_headers,
        **INGEST_ARGS,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_normalize_400(test_client: TestClient, db_cleanup):
    response = test_client.post("/normalize/some-id")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_normalize_403(test_client: TestClient, authz_headers_bad, db_cleanup):
    response = test_client.post("/normalize/some-id", headers=authz_headers_bad)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_normalize_200(test_client: TestClient, authz_headers, db_cleanup):
    # TODO real tests in normalization PR
    with open(f"{TEST_FILES_DIR}/gene_lengths.csv", "rb") as file:
        response = test_client.post(
            url="/normalize/some-id",
            files=[("features_lengths_file", file)],
            headers=authz_headers,
        )
    assert response.status_code == status.HTTP_200_OK
