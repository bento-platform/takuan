import os
from pathlib import Path
from fastapi import status
from fastapi.testclient import TestClient

from tests.conftest import TEST_EXPERIMENT_RESULT
from transcriptomics_data_service.config import get_config
from httpx._types import HeaderTypes

from transcriptomics_data_service.logger import get_logger
from transcriptomics_data_service.models import ExpressionQueryBody, NormalizationMethodEnum


config = get_config()
logger = get_logger(config)

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "data")
RCM_FILE_PATH = f"{TEST_FILES_DIR}/rcm_file.csv"
SINGLE_SAMPLE_FILE_PATH = f"{TEST_FILES_DIR}/single_sample_detailed.csv"


def _ingest_file(
    client: TestClient,
    file_path: Path,
    headers: HeaderTypes | None = None,
    is_single_sample: bool = False,
    form_data: dict | None = None,
):
    url = f"/experiment/{TEST_EXPERIMENT_RESULT.experiment_result_id}/ingest"
    if is_single_sample:
        url = f"{url}/single"
        file_key = "data"
    else:
        file_key = "rcm_file"

    with open(file_path, "rb") as file:
        res = client.post(
            url=url,
            files=[(file_key, file)],
            headers=headers,
            data=form_data,
        )
    return res


def test_ingest_unauthorized(test_client, authz_headers_bad, db_cleanup, db_with_experiment):
    response = _ingest_file(
        test_client,
        file_path=RCM_FILE_PATH,
        headers=authz_headers_bad,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_ingest_authorized(test_client, authz_headers, db_cleanup, db_with_experiment):
    response = _ingest_file(
        test_client,
        file_path=RCM_FILE_PATH,
        headers=authz_headers,
    )
    assert response.status_code == status.HTTP_200_OK


def test_ingest_authorized_duplicate(test_client, authz_headers, db_cleanup, db_with_experiment):
    response = _ingest_file(
        test_client,
        file_path=f"{TEST_FILES_DIR}/rcm_file_duplicates.csv",
        headers=authz_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_ingest_404(test_client, authz_headers, db_cleanup):
    # db_with_experiment fixture not included, targeted experiment doesn't exist
    response = _ingest_file(
        test_client,
        file_path=RCM_FILE_PATH,
        headers=authz_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_ingest_parser_error(test_client, authz_headers, db_cleanup, db_with_experiment):
    response = _ingest_file(
        test_client,
        file_path=f"{TEST_FILES_DIR}/rcm_file_bad_values.csv",
        headers=authz_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_ingest_invalid_csv(test_client, authz_headers, db_cleanup, db_with_experiment):
    response = _ingest_file(
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
    response = _ingest_file(
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

            if method is NormalizationMethodEnum.fpkm:
                # TODO: expect 200 once implemented
                assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
            else:
                assert response.status_code == status.HTTP_200_OK


def test_ingest_single_sample(test_client: TestClient, authz_headers, db_cleanup, db_with_experiment):
    response = _ingest_file(
        test_client,
        file_path=SINGLE_SAMPLE_FILE_PATH,
        headers=authz_headers,
        is_single_sample=True,
        form_data=dict(
            sample_id="my-sample-id",
            feature_col="feature",
            raw_count_col="count",
            tpm_count_col="tpm",
            tmm_count_col="tmm",
            getmm_count_col="getmm",
            fpkm_count_col="fpkm",
        ),
    )
    assert response.status_code == status.HTTP_200_OK


def test_ingest_single_sample_bad_mapping(test_client: TestClient, authz_headers, db_cleanup, db_with_experiment):
    response = _ingest_file(
        test_client,
        file_path=SINGLE_SAMPLE_FILE_PATH,
        headers=authz_headers,
        is_single_sample=True,
        form_data={
            "sample_id": "my-sample-id",
            "feature_col": "feature",
            "raw_count_col": "bad_count_MISSING",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def _assert_expression_count(
    test_client: TestClient,
    authz_headers,
    query: ExpressionQueryBody,
    expected_count: int | None = None,
    expected_status: status = status.HTTP_200_OK,
):
    r = test_client.post("/expressions", headers=authz_headers, json=query.model_dump())
    assert r.status_code == expected_status
    if expected_status == status.HTTP_200_OK and expected_count:
        # Data is available, check counts
        data = r.json()
        assert data["total_records"] == expected_count


def test_ingest_mixed_samples(test_client: TestClient, authz_headers, db_cleanup, db_with_experiment):
    # Ingest a file with TPM and FPKM columns
    r1 = _ingest_file(
        test_client,
        file_path=f"{TEST_FILES_DIR}/single_sample_tpm.tsv",
        headers=authz_headers,
        is_single_sample=True,
        form_data={
            "sample_id": "my-sample-id",
            "raw_count_col": "counts",
            "tpm_count_col": "abundance",
        },
    )
    assert r1.status_code == status.HTTP_200_OK
    _assert_expression_count(test_client, authz_headers, query=ExpressionQueryBody(method="tpm"), expected_count=2)
    _assert_expression_count(test_client, authz_headers, query=ExpressionQueryBody(method="raw"), expected_count=2)
    _assert_expression_count(
        test_client, authz_headers, query=ExpressionQueryBody(method="fpkm"), expected_status=status.HTTP_404_NOT_FOUND
    )

    # Same gene_id, sample and experiment, should only add FPKM counts and update TPM
    r2 = _ingest_file(
        test_client,
        file_path=f"{TEST_FILES_DIR}/single_sample_tpm_fpkm.tsv",
        headers=authz_headers,
        is_single_sample=True,
        form_data={
            "sample_id": "my-sample-id",
            "raw_count_col": "expected_count",
            "tpm_count_col": "TPM",
            "fpkm_count_col": "FPKM",
        },
    )
    assert r2.status_code == status.HTTP_200_OK
    # Same sample_id and experiment so TPM and RAW counts should not have changed
    _assert_expression_count(test_client, authz_headers, query=ExpressionQueryBody(method="tpm"), expected_count=2)
    _assert_expression_count(test_client, authz_headers, query=ExpressionQueryBody(method="raw"), expected_count=2)
    # We should now have 2 expressions with FPKM
    _assert_expression_count(test_client, authz_headers, query=ExpressionQueryBody(method="fpkm"), expected_count=2)

    # USING A DIFFERENT SAMPLE_ID
    OTHER_SAMPLE_ID = "my-other-sample-id"
    r3 = _ingest_file(
        test_client,
        file_path=f"{TEST_FILES_DIR}/single_sample_tpm_fpkm.tsv",
        headers=authz_headers,
        is_single_sample=True,
        form_data={
            "sample_id": OTHER_SAMPLE_ID,
            "raw_count_col": "expected_count",
            "tpm_count_col": "TPM",
            "fpkm_count_col": "FPKM",
        },
    )
    assert r3.status_code == status.HTTP_200_OK
    # Counts accross all samples should now be double since we ingested in another sample
    _assert_expression_count(test_client, authz_headers, query=ExpressionQueryBody(method="tpm"), expected_count=4)
    _assert_expression_count(test_client, authz_headers, query=ExpressionQueryBody(method="raw"), expected_count=4)
    _assert_expression_count(test_client, authz_headers, query=ExpressionQueryBody(method="fpkm"), expected_count=4)

    # Counts specific to my-other-sample-id should be 2
    _assert_expression_count(
        test_client,
        authz_headers,
        query=ExpressionQueryBody(method="tpm", sample_ids=[OTHER_SAMPLE_ID]),
        expected_count=2,
    )
    _assert_expression_count(
        test_client,
        authz_headers,
        query=ExpressionQueryBody(method="raw", sample_ids=[OTHER_SAMPLE_ID]),
        expected_count=2,
    )
    _assert_expression_count(
        test_client,
        authz_headers,
        query=ExpressionQueryBody(method="fpkm", sample_ids=[OTHER_SAMPLE_ID]),
        expected_count=2,
    )
