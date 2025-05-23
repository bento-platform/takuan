import os
from pathlib import Path
from fastapi import status
from fastapi.testclient import TestClient

from tests.conftest import TEST_EXPERIMENT_RESULT
from transcriptomics_data_service.config import get_config
from httpx._types import HeaderTypes

from transcriptomics_data_service.logger import get_logger
from transcriptomics_data_service.models import ExperimentResult, ExpressionQueryBody, NormalizationMethodEnum


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


# Temp commented to speed local tests
def test_normalize(test_client: TestClient, authz_headers, db_cleanup, db_with_experiment):
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
            file_type="csv",
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
            "file_type": "csv",
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
    SAMPLE_ID_1 = "SAMPLE_ID_1"
    r1 = _ingest_file(
        test_client,
        file_path=f"{TEST_FILES_DIR}/single_sample_tpm_fpkm.tsv",
        headers=authz_headers,
        is_single_sample=True,
        form_data={
            "sample_id": SAMPLE_ID_1,
            "feature_col": "gene_id",
            "raw_count_col": "expected_count",
            "tpm_count_col": "TPM",
            "fpkm_count_col": "FPKM",
            "file_type": "tsv",
        },
    )
    assert r1.status_code == status.HTTP_200_OK
    # Ingested 2 new expressions for a new sample, we expect 2 for each count
    _assert_expression_count(test_client, authz_headers, query=ExpressionQueryBody(method="tpm"), expected_count=2)
    _assert_expression_count(test_client, authz_headers, query=ExpressionQueryBody(method="raw"), expected_count=2)
    _assert_expression_count(test_client, authz_headers, query=ExpressionQueryBody(method="fpkm"), expected_count=2)

    # Same gene_id, sample and experiment, should only add FPKM counts and update TPM
    SAMPLE_ID_2 = "SAMPLE_ID_2"
    r2 = _ingest_file(
        test_client,
        file_path=f"{TEST_FILES_DIR}/single_sample_tpm.tsv",
        headers=authz_headers,
        is_single_sample=True,
        form_data={
            "sample_id": SAMPLE_ID_2,
            "feature_col": "gene_id",
            "raw_count_col": "counts",
            "tpm_count_col": "abundance",
        },
    )
    assert r2.status_code == status.HTTP_200_OK
    # Ingested 2 new expressions for a new sample, we expect 4 for each count
    _assert_expression_count(test_client, authz_headers, query=ExpressionQueryBody(method="tpm"), expected_count=4)
    _assert_expression_count(test_client, authz_headers, query=ExpressionQueryBody(method="raw"), expected_count=4)
    # We should now have 2 expressions with FPKM
    _assert_expression_count(test_client, authz_headers, query=ExpressionQueryBody(method="fpkm"), expected_count=2)

    # Upsert FPKM values into SAMPLE_ID_1
    r3 = _ingest_file(
        test_client,
        file_path=f"{TEST_FILES_DIR}/single_sample_tpm_fpkm_2.tsv",
        headers=authz_headers,
        is_single_sample=True,
        form_data={
            "sample_id": SAMPLE_ID_1,
            "raw_count_col": "expected_count",
            "tpm_count_col": "TPM",
            "fpkm_count_col": "FPKM",
        },
    )
    assert r3.status_code == status.HTTP_200_OK
    # Counts accross all samples should now have been incremented by 2
    _assert_expression_count(test_client, authz_headers, query=ExpressionQueryBody(method="tpm"), expected_count=6)
    _assert_expression_count(test_client, authz_headers, query=ExpressionQueryBody(method="raw"), expected_count=6)
    _assert_expression_count(test_client, authz_headers, query=ExpressionQueryBody(method="fpkm"), expected_count=4)

    # Counts specific to SAMPLE_ID_1 should all be 4 now
    _assert_expression_count(
        test_client,
        authz_headers,
        query=ExpressionQueryBody(method="tpm", sample_ids=[SAMPLE_ID_1]),
        expected_count=4,
    )
    _assert_expression_count(
        test_client,
        authz_headers,
        query=ExpressionQueryBody(method="raw", sample_ids=[SAMPLE_ID_1]),
        expected_count=4,
    )
    _assert_expression_count(
        test_client,
        authz_headers,
        query=ExpressionQueryBody(method="fpkm", sample_ids=[SAMPLE_ID_1]),
        expected_count=4,
    )


def test_ingest_mixed_samples_strings(
    test_client: TestClient, authz_headers, db_cleanup, db_with_experiment: ExperimentResult
):
    exp_id = db_with_experiment.experiment_result_id

    def _assert_counts(exp_count: int):
        exp_status = status.HTTP_200_OK
        if exp_count == 0:
            exp_count = None
            exp_status = status.HTTP_404_NOT_FOUND
        for method in ["raw", "tpm", "fpkm"]:
            _assert_expression_count(
                test_client,
                authz_headers,
                query=ExpressionQueryBody(method=method),
                expected_count=exp_count,
                expected_status=exp_status,
            )

    _assert_counts(0)

    # Sample 1 malformed: \\t and \\n instead of \t and \n
    s1_id = "SAMPLE_1"
    s1_malformed_string = "gene_id\\tcounts\\tlength\\ttpm\\tfpkm\\nENSG00000000003.14\\t150.00\\t2000.22\\t6.24\\t7.32\\t\\nENSG00000000005\\t250.00\\t2020.22\\t2.24\\t2.32"
    s1_malformed_data = bytes(
        s1_malformed_string,
        "utf-8",
    )
    s1_body = {
        "sample_id": s1_id,
        "feature_col": "gene_id",
        "raw_count_col": "counts",
        "tpm_count_col": "tpm",
        "fpkm_count_col": "fpkm",
    }
    r_s1_ingest = test_client.post(
        f"/experiment/{exp_id}/ingest/single", headers=authz_headers, files={"data": s1_malformed_data}, data=s1_body
    )
    assert r_s1_ingest.status_code == status.HTTP_400_BAD_REQUEST
    _assert_counts(0)

    # Sample 1 corrected, but wrongly ingested as CSV
    s1_corrected_string = s1_malformed_string.replace("\\t", "\t").replace("\\n", "\n")
    s1_corrected_data = bytes(s1_corrected_string, "utf-8")
    s1_body_wrong_type = {"file_type": "csv", **s1_body}
    r_s1_ingest = test_client.post(
        f"/experiment/{exp_id}/ingest/single",
        headers=authz_headers,
        files={"data": s1_corrected_data},
        data=s1_body_wrong_type,
    )
    assert r_s1_ingest.status_code == status.HTTP_400_BAD_REQUEST

    # Sample 1 corrected, but ingested as TSV (default)
    r_s1_ingest = test_client.post(
        f"/experiment/{exp_id}/ingest/single", headers=authz_headers, files={"data": s1_corrected_data}, data=s1_body
    )
    assert r_s1_ingest.status_code == status.HTTP_200_OK
    _assert_counts(2)

    # Sample 2 correct and ingest right away
    s2_id = "SAMPLE_2"
    s2_malformed_string = "gene_id\\tcounts\\tlength\\ttpm\\tfpkm\\nENSG00000000003.14\\t150.00\\t2000.22\\t6.24\\t7.32\\t\\nENSG00000000005\\t250.00\\t2020.22\\t2.24\\t2.32"
    s2_string = s2_malformed_string.replace("\\t", "\t").replace("\\n", "\n")
    s2_data = bytes(
        s2_string,
        "utf-8",
    )
    s2_body = {
        "sample_id": s2_id,
        "feature_col": "gene_id",
        "raw_count_col": "counts",
        "tpm_count_col": "tpm",
        "fpkm_count_col": "fpkm",
        "file_type": "tsv",
    }
    r_s2_ingest = test_client.post(
        f"/experiment/{exp_id}/ingest/single", headers=authz_headers, files={"data": s2_data}, data=s2_body
    )
    assert r_s2_ingest.status_code == status.HTTP_200_OK
    _assert_counts(4)
