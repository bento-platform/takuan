from typing import AsyncGenerator
import asyncpg
from fastapi.testclient import TestClient
import pytest
import os

import pytest_asyncio

from transcriptomics_data_service.db import Database, get_db
from transcriptomics_data_service.logger import get_logger

os.environ["BENTO_DEBUG"] = "true"
os.environ["BENTO_VALIDATE_SSL"] = "false"
os.environ["CORS_ORIGINS"] = "*"
os.environ["BENTO_AUTHZ_SERVICE_URL"] = "https://authz.local"

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
            DROP TABLE IF EXISTS experiment_results;
            DROP TABLE IF EXISTS gene_expressions;
            
            DROP INDEX IF EXISTS idx_gene_code;
            DROP INDEX IF EXISTS idx_sample_id;
            DROP INDEX IF EXISTS idx_experiment_result_id;
            """
        )
    await db.close()


@pytest.fixture
def test_client(db: Database):
    with TestClient(app) as client:
        app.dependency_overrides[get_db] = get_test_db
        yield client
