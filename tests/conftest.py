from typing import AsyncGenerator
import asyncpg
from fastapi.testclient import TestClient
import pytest
import os
import pytest_asyncio
from httpx._types import HeaderTypes

from tests.test_db import TEST_EXPERIMENT_RESULT
from transcriptomics_data_service.db import Database, get_db
from transcriptomics_data_service.logger import get_logger
from transcriptomics_data_service.models import GeneExpression

os.environ["CORS_ORIGINS"] = "*"
os.environ["AUTHZ_ENABLED"] = "True"

from transcriptomics_data_service.config import Config, get_config
from transcriptomics_data_service.main import app


@pytest.fixture
def config() -> Config:
    return get_config()


async def get_test_db() -> AsyncGenerator[Database, None]:
    config = get_config()
    db = Database(config, get_logger(config))
    await db.initialize(pool_size=1)
    yield db


db_fixture = pytest_asyncio.fixture(get_test_db, name="db")


@pytest_asyncio.fixture
async def db_cleanup(db: Database):
    yield
    conn: asyncpg.Connection
    async with db.connect() as conn:
        await conn.execute(
            """
            DROP TABLE IF EXISTS gene_expressions;
            DROP TABLE IF EXISTS experiment_results;
            
            DROP INDEX IF EXISTS idx_gene_code;
            DROP INDEX IF EXISTS idx_sample_id;
            DROP INDEX IF EXISTS idx_experiment_result_id;
            """
        )
    await db.close()


@pytest_asyncio.fixture
async def db_truncate_expressions(db: Database):
    # Cleans gene_expressions table
    async with db.connect() as conn:
        await conn.execute("TRUNCATE gene_expressions;")


@pytest_asyncio.fixture
async def db_with_experiment(db: Database):
    await db.create_experiment_result(TEST_EXPERIMENT_RESULT)
    return TEST_EXPERIMENT_RESULT


@pytest_asyncio.fixture
async def db_with_raw_expression(db: Database, db_truncate_expressions, db_with_experiment) -> GeneExpression:
    RAW_ONLY_SAMPLE_ID = "SAMPLE_RAW"
    raw_expression = GeneExpression(
        experiment_result_id=TEST_EXPERIMENT_RESULT.experiment_result_id,
        sample_id=RAW_ONLY_SAMPLE_ID,
        gene_code="ENSG00000000005",
        raw_count=25,
    )
    async with db.connect() as conn:
        await db.create_or_update_gene_expressions([raw_expression], conn)
    return raw_expression


@pytest_asyncio.fixture
async def db_with_tpm_expression(db: Database, db_truncate_expressions, db_with_experiment) -> GeneExpression:
    TPM_ONLY_SAMPLE_ID = "SAMPLE_RAW_TPM"
    tpm_expression = GeneExpression(
        experiment_result_id=TEST_EXPERIMENT_RESULT.experiment_result_id,
        sample_id=TPM_ONLY_SAMPLE_ID,
        gene_code="ENSG00000000005",
        tpm_count=0.032,
    )
    async with db.connect() as conn:
        await db.create_or_update_gene_expressions([tpm_expression], conn)
    return tpm_expression


@pytest_asyncio.fixture
async def db_with_full_expression(db: Database, db_truncate_expressions, db_with_experiment) -> GeneExpression:
    ALL_COUNTS_SAMPLE_ID = "SAMPLE_ALL"
    all_counts_expression = GeneExpression(
        experiment_result_id=TEST_EXPERIMENT_RESULT.experiment_result_id,
        gene_code="ENSG00000000005",
        sample_id=ALL_COUNTS_SAMPLE_ID,
        raw_count=59,
        tpm_count=12135.2151,
        tmm_count=0.2851,
        getmm_count=23.0007,
        fpkm_count=0.3333458,
    )
    async with db.connect() as conn:
        await db.create_or_update_gene_expressions([all_counts_expression], conn)
    return all_counts_expression


@pytest.fixture
def test_client(db: Database):
    with TestClient(app) as client:
        app.dependency_overrides[get_db] = get_test_db
        yield client


@pytest.fixture
def authz_headers(config) -> HeaderTypes:
    # Valid authz header from the config
    api_key = config.model_extra.get("api_key", "")
    return {"x-api-key": api_key}


@pytest.fixture
def authz_headers_bad() -> HeaderTypes:
    # Invalid authz header: 403 wrong API key
    return {"x-api-key": "bad key"}


@pytest.fixture
def authz_headers_empty() -> HeaderTypes:
    # Invalid authz header: 400 missing header value
    return {"x-api-key": ""}
