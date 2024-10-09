from fastapi import APIRouter

from transcriptomics_data_service.db import DatabaseDependency

__all__ = ["experiment_router"]

experiment_router = APIRouter(prefix="/experiment")


@experiment_router.delete("/{experiment_result_id}")
async def delete_experiment_result(db: DatabaseDependency, experiment_result_id: str):
    await db.delete_experiment_result(experiment_result_id)


@experiment_router.get("/{experiment_result_id}")
async def get_experiment_result(db: DatabaseDependency, experiment_result_id: str):
    return await db.read_experiment_result(experiment_result_id)
