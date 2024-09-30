from fastapi import APIRouter, status

from transcriptomics_data_service.db import DatabaseDependency

__all__ = ["expression_router"]

expression_router = APIRouter(prefix="/expressions")


@expression_router.get("", status_code=status.HTTP_200_OK)
async def expressions_list(db: DatabaseDependency):
    return await db.fetch_expressions()
