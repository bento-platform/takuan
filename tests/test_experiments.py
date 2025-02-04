from fastapi import status
import pytest

from tests.test_db import TEST_EXPERIMENT_RESULT
from transcriptomics_data_service.config import get_config
from transcriptomics_data_service.logger import get_logger
from transcriptomics_data_service.models import ExperimentResult

config = get_config()
logger = get_logger(config)

TEST_EXPERIMENT_RESULT_NO_EXTRA = ExperimentResult(
    experiment_result_id="12345",
    assembly_id="assembly_test_id",
    assembly_name="assembly_test_name",
)


@pytest.mark.parametrize("exp", [TEST_EXPERIMENT_RESULT, TEST_EXPERIMENT_RESULT_NO_EXTRA])
def test_create_experiment(exp, test_client, authz_headers, db_cleanup):
    response = test_client.post(
        "/experiment",
        headers=authz_headers,
        data=exp.model_dump_json(),
    )
    assert response.status_code == status.HTTP_200_OK


def test_create_experiment_400(test_client, authz_headers, db_cleanup):
    response = test_client.post(
        "/experiment",
        headers=authz_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_experiment_403(test_client, authz_headers_bad, db_cleanup):
    response = test_client.post(
        "/experiment",
        headers=authz_headers_bad,
        data=TEST_EXPERIMENT_RESULT.model_dump_json(),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_experiment(test_client, authz_headers, db_with_experiment, db_cleanup):
    # TEST_EXPERIMENT_RESULT_ID
    response = test_client.get(
        f"/experiment/{TEST_EXPERIMENT_RESULT.experiment_result_id}",
        headers=authz_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert TEST_EXPERIMENT_RESULT == ExperimentResult(**data)


# EMPTY DB
def test_get_experiment_400(test_client):
    # Missing api-key
    response = test_client.get("/experiment/non-existant")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_experiment_200_empty(test_client, authz_headers):
    # Missing api-key
    response = test_client.get("/experiment/non-existant", headers=authz_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() is None


def test_delete_experiment_400(test_client):
    # Missing api-key
    response = test_client.delete("/experiment/non-existant")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_delete_experiment_403(test_client, authz_headers_bad):
    # Missing api-key
    response = test_client.delete("/experiment/non-existant", headers=authz_headers_bad)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_experiment_200(test_client, authz_headers):
    # Missing api-key
    response = test_client.delete("/experiment/non-existant", headers=authz_headers)
    assert response.status_code == status.HTTP_200_OK
