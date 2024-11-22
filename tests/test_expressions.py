from fastapi import status
from fastapi.testclient import TestClient
from transcriptomics_data_service.config import get_config
from transcriptomics_data_service.logger import get_logger


config = get_config()
logger = get_logger(config)

api_key = config.model_extra.get("api_key")

def test_expressions_unauthorized(test_client: TestClient):
    response = test_client.get("/expressions")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_expressions_authorized(test_client: TestClient, authz_headers):
    response = test_client.get("/expressions", headers=authz_headers)
    assert response.status_code == status.HTTP_200_OK
