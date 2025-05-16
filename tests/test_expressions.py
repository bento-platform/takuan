from fastapi import status
from fastapi.testclient import TestClient
from transcriptomics_data_service.config import get_config
from transcriptomics_data_service.logger import get_logger
from transcriptomics_data_service.models import GeneExpression


config = get_config()
logger = get_logger(config)

api_key = config.model_extra.get("api_key")


def test_expressions_unauthorized(test_client: TestClient, authz_headers_bad):
    # missing API key
    response = test_client.post("/expressions", headers=authz_headers_bad)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_expressions_authorized(test_client: TestClient, authz_headers):
    # no expressions in DB
    response = test_client.post("/expressions", headers=authz_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_expressions_query_raw(
    test_client: TestClient, authz_headers, db_cleanup, db_with_raw_expression: GeneExpression
):
    # default query returns expressions with 'raw' counts present
    base_q = {
        "genes": [db_with_raw_expression.gene_code],
        "experiments": [db_with_raw_expression.experiment_result_id],
        "sample_ids": [db_with_raw_expression.sample_id],
    }
    response = test_client.post("/expressions", headers=authz_headers, json=base_q)
    assert response.status_code == status.HTTP_200_OK

    # Should be 404 because there is no tpm rows stored
    response = test_client.post("/expressions", headers=authz_headers, json={"method": "tpm", **base_q})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_expressions_query_tpm(
    test_client: TestClient, authz_headers, db_cleanup, db_with_tpm_expression: GeneExpression
):
    # Should be 404 because there is no 'raw' rows stored
    base_q = {
        "genes": [db_with_tpm_expression.gene_code],
        "experiments": [db_with_tpm_expression.experiment_result_id],
        "sample_ids": [db_with_tpm_expression.sample_id],
    }
    response = test_client.post("/expressions", headers=authz_headers, json=base_q)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Should return 200 because we have a TPM expression present
    response = test_client.post("/expressions", headers=authz_headers, json={"method": "tpm", **base_q})
    assert response.status_code == status.HTTP_200_OK


def _expressions_query_all(
    test_client: TestClient,
    authz_headers,
    expect_code: int = status.HTTP_200_OK,
    extra_query: dict = {},
):
    response = test_client.post("/expressions", headers=authz_headers, json=extra_query)
    assert response.status_code == expect_code

    response = test_client.post("/expressions", headers=authz_headers, json={"method": "tpm", **extra_query})
    assert response.status_code == expect_code

    response = test_client.post("/expressions", headers=authz_headers, json={"method": "tmm", **extra_query})
    assert response.status_code == expect_code

    response = test_client.post("/expressions", headers=authz_headers, json={"method": "getmm", **extra_query})
    assert response.status_code == expect_code

    response = test_client.post("/expressions", headers=authz_headers, json={"method": "fpkm", **extra_query})
    assert response.status_code == expect_code


def test_expressions_query_all(test_client: TestClient, authz_headers, db_cleanup, db_with_full_expression):
    # Test accross all counts
    _expressions_query_all(test_client, authz_headers)


def test_expressions_query_exp(
    test_client: TestClient, authz_headers, db_cleanup, db_with_full_expression: GeneExpression
):
    # Test accross all Experiments / Samples
    _expressions_query_all(test_client, authz_headers, status.HTTP_404_NOT_FOUND, {"experiments": ["I-DONT-EXIST"]})
    _expressions_query_all(
        test_client, authz_headers, status.HTTP_200_OK, {"experiments": [db_with_full_expression.experiment_result_id]}
    )


def test_expressions_query_sample(
    test_client: TestClient, authz_headers, db_cleanup, db_with_full_expression: GeneExpression
):
    # Test accross all Experiments / Samples
    _expressions_query_all(test_client, authz_headers, status.HTTP_404_NOT_FOUND, {"sample_ids": ["I-DONT-EXIST"]})
    _expressions_query_all(
        test_client, authz_headers, status.HTTP_200_OK, {"sample_ids": [db_with_full_expression.sample_id]}
    )


def test_expressions_query_gene(
    test_client: TestClient, authz_headers, db_cleanup, db_with_full_expression: GeneExpression
):
    # Test accross all Experiments / Samples
    _expressions_query_all(test_client, authz_headers, status.HTTP_404_NOT_FOUND, {"genes": ["I-DONT-EXIST"]})
    _expressions_query_all(
        test_client, authz_headers, status.HTTP_200_OK, {"genes": [db_with_full_expression.gene_code]}
    )
