from fastapi import status
from fastapi.testclient import TestClient
from transcriptomics_data_service.config import get_config
from transcriptomics_data_service.db import DEFAULT_PAGINATION
from transcriptomics_data_service.logger import get_logger


config = get_config()
logger = get_logger(config)

api_key = config.model_extra.get("api_key")


def test_expressions_unauthorized(test_client: TestClient):
    # missing API key
    response = test_client.post("/expressions", data=DEFAULT_PAGINATION)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_expressions_authorized(test_client: TestClient, authz_headers):
    # no expressions in DB
    response = test_client.post("/expressions", data=DEFAULT_PAGINATION.model_dump_json(), headers=authz_headers)
    print(response)
    assert response.status_code == status.HTTP_404_NOT_FOUND
