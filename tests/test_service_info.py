from fastapi import status
from fastapi.testclient import TestClient

from transcriptomics_data_service.service_info import read_service_info


def test_read_service_info():
    read_service_info("./tests/data/service-info.json")


def test_service_info_endpoint(test_client: TestClient):
    res = test_client.get("/service-info")
    assert res.status_code == status.HTTP_200_OK
