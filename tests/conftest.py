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
async def db_with_experiment(db: Database):
    await db.create_experiment_result(TEST_EXPERIMENT_RESULT)


@pytest.fixture
def test_client(db: Database):
    with TestClient(app) as client:
        app.dependency_overrides[get_db] = get_test_db
        yield client


@pytest.fixture
def authz_headers(config) -> HeaderTypes:
    api_key = config.model_extra.get("api_key")
    return {"x-api-key": api_key}


@pytest.fixture
def authz_headers_bad() -> HeaderTypes:
    return {"x-api-key": "bad key"}
