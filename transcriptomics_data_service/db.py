import logging
from typing import Annotated
import asyncpg
from bento_lib.db.pg_async import PgAsyncDatabase
from contextlib import asynccontextmanager
from fastapi import Depends
from functools import lru_cache
from pathlib import Path

from .config import Config, ConfigDependency
from .logger import LoggerDependency
from .models import GeneExpression


SCHEMA_PATH = Path(__file__).parent / "sql" / "schema.sql"


class Database(PgAsyncDatabase):
    def __init__(self, config: Config, logger: logging.Logger):
        self._config = config
        self.logger = logger
        super().__init__(config.database_uri, SCHEMA_PATH)

    async def insert_gene_expression(self, expression: GeneExpression):
        query = """
        INSERT INTO gene_expressions (gene_code, sample_id, experiment_result_id, raw_count, tpm_count, tmm_count)
        VALUES ($1, $2, $3, $4, $5, $6)
        """
        await self.execute(
            query,
            expression.gene_code,
            expression.sample_id,
            expression.experiment_result_id,
            expression.raw_count,
            expression.tpm_count,
            expression.tmm_count,
        )

    async def fetch_expressions(self):
        conn: asyncpg.Connection
        query = "SELECT * FROM gene_expressions"
        async with self.connect() as conn:
            res = await conn.fetch(query)
        return res


    @asynccontextmanager
    async def transaction(self):
        conn = await self.get_connection()
        trx = await conn.transaction()
        try:
            yield
            await trx.commit()
        except Exception as e:
            await trx.rollback()
            raise e


@lru_cache()
def get_db(config: ConfigDependency, logger: LoggerDependency) -> Database:
    return Database(config, logger)


DatabaseDependency = Annotated[Database, Depends(get_db)]
