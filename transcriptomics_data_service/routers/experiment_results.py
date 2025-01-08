from fastapi import APIRouter

from transcriptomics_data_service.db import DatabaseDependency

__all__ = ["experiment_router"]

experiment_router = APIRouter(prefix="/experiment")

@experiment_router.get("")
async def get_all_experiments(db: DatabaseDependency):
    experiments, _ = await db.fetch_experiment_results(paginate=False)
    return experiments


@experiment_router.get("/{experiment_result_id}")
async def get_experiment_result(db: DatabaseDependency, experiment_result_id: str):
    return await db.read_experiment_result(experiment_result_id)
