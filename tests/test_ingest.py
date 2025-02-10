import os
from pathlib import Path
from fastapi import status
from fastapi.testclient import TestClient

from tests.conftest import TEST_EXPERIMENT_RESULT
from transcriptomics_data_service.config import get_config
from httpx._types import HeaderTypes

from transcriptomics_data_service.logger import get_logger
from transcriptomics_data_service.models import NormalizationMethodEnum


config = get_config()
logger = get_logger(config)

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "data")
RCM_FILE_PATH = f"{TEST_FILES_DIR}/rcm_file.csv"


def _ingest_rcm_file(
    client: TestClient,
    file_path: Path,
    headers: HeaderTypes | None = None,
):
    with open(file_path, "rb") as file:
        res = client.post(
            url=f"/experiment/{TEST_EXPERIMENT_RESULT.experiment_result_id}/ingest",
            files=[("rcm_file", file)],
            headers=headers,
        )
    return res


def test_ingest_unauthorized(test_client, authz_headers_bad, db_cleanup, db_with_experiment):
    response = _ingest_rcm_file(
        test_client,
        file_path=RCM_FILE_PATH,
        headers=authz_headers_bad,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_ingest_authorized(test_client, authz_headers, db_cleanup, db_with_experiment):
    response = _ingest_rcm_file(
        test_client,
        file_path=RCM_FILE_PATH,
        headers=authz_headers,
    )
    assert response.status_code == status.HTTP_200_OK


def test_ingest_authorized_duplicate(test_client, authz_headers, db_cleanup, db_with_experiment):
    response = _ingest_rcm_file(
        test_client,
        file_path=f"{TEST_FILES_DIR}/rcm_file_duplicates.csv",
        headers=authz_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_ingest_404(test_client, authz_headers, db_cleanup):
    # db_with_experiment fixture not included, targeted experiment doesn't exist
    response = _ingest_rcm_file(
        test_client,
        file_path=RCM_FILE_PATH,
        headers=authz_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_ingest_parser_error(test_client, authz_headers, db_cleanup, db_with_experiment):
    response = _ingest_rcm_file(
        test_client,
        file_path=f"{TEST_FILES_DIR}/rcm_file_bad_values.csv",
        headers=authz_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_ingest_invalid_csv(test_client, authz_headers, db_cleanup, db_with_experiment):
    response = _ingest_rcm_file(
        test_client,
        file_path=f"{TEST_FILES_DIR}/rcm_file_bad_column.csv",
        headers=authz_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_normalize_403(test_client: TestClient, authz_headers_bad, db_cleanup, db_with_experiment):
    exp_id_missing = "bad-id"
    method = NormalizationMethodEnum.tpm.value
    response = test_client.post(f"/normalize/{exp_id_missing}/{method}", headers=authz_headers_bad)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_normalize_tpm(test_client: TestClient, authz_headers, db_cleanup, db_with_experiment):
    response = _ingest_rcm_file(
        test_client,
        file_path=RCM_FILE_PATH,
        headers=authz_headers,
    )
    with open(f"{TEST_FILES_DIR}/gene_lengths.csv", "rb") as file:
        for method in NormalizationMethodEnum:
            response = test_client.post(
                url=f"/normalize/{TEST_EXPERIMENT_RESULT.experiment_result_id}/{method.value}",
                files=[("gene_lengths_file", file)],
                headers=authz_headers,
            )
            assert response.status_code == status.HTTP_200_OK
