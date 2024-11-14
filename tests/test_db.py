import pytest
from transcriptomics_data_service.db import Database
from transcriptomics_data_service.models import ExperimentResult

@pytest.mark.asyncio
async def test_create_experiment_result(db: Database, db_cleanup):
    exp_id = "exp_test"
    exp_result = ExperimentResult(
        experiment_result_id=exp_id,
        assembly_id="assembly_test_id",
        assembly_name="assembly_test_name",
    )
    await db.create_experiment_result(exp_result)
    db_exp_result = await db.read_experiment_result(exp_id)
    assert exp_result == db_exp_result
