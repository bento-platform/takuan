from asyncpg import Connection, UniqueViolationError
import pytest
from transcriptomics_data_service.db import Database
from transcriptomics_data_service.models import ExperimentResult, GeneExpression

TEST_EXPERIMENT_RESULT_ID = "test-experiment-id"
TEST_EXPERIMENT_RESULT = ExperimentResult(
    experiment_result_id=TEST_EXPERIMENT_RESULT_ID,
    assembly_id="assembly_test_id",
    assembly_name="assembly_test_name",
)
TEST_GENE_EXPRESSION = GeneExpression(
    experiment_result_id=TEST_EXPERIMENT_RESULT_ID,
    gene_code="test-gene-code",
    sample_id="test-sample-id",
    raw_count=90,
)

##########################
# CRUD: experiment_results
##########################


@pytest.mark.asyncio
async def test_create_read_experiment_result(db: Database, db_cleanup):
    await db.create_experiment_result(TEST_EXPERIMENT_RESULT)
    db_exp_result = await db.read_experiment_result(TEST_EXPERIMENT_RESULT_ID)
    assert TEST_EXPERIMENT_RESULT == db_exp_result


@pytest.mark.asyncio
async def test_update_experiment_result(db: Database, db_cleanup):
    await db.create_experiment_result(TEST_EXPERIMENT_RESULT)
    new_exp = TEST_EXPERIMENT_RESULT.model_copy()
    new_exp.assembly_name = "updated_assembly_name"
    await db.update_experiment_result(new_exp)
    db_exp_result = await db.read_experiment_result(new_exp.experiment_result_id)
    assert db_exp_result.assembly_name == new_exp.assembly_name


@pytest.mark.asyncio
async def test_delete_experiment_result(db: Database, db_cleanup):
    await db.create_experiment_result(TEST_EXPERIMENT_RESULT)
    await db.delete_experiment_result(TEST_EXPERIMENT_RESULT_ID)
    db_exp_result = await db.read_experiment_result(TEST_EXPERIMENT_RESULT_ID)
    assert db_exp_result == None


########################
# CRUD: gene_expressions
########################


@pytest.mark.asyncio
async def test_gene_expression(db: Database, db_cleanup):
    async with db.transaction_connection() as conn:
        await db.create_experiment_result(TEST_EXPERIMENT_RESULT, conn)
        await db.create_gene_expressions([TEST_GENE_EXPRESSION], conn)

    # read all
    db_expressions = await db.fetch_expressions()
    assert len(db_expressions) == 1
    assert db_expressions[0] == TEST_GENE_EXPRESSION

    # read by ExperimentResult ID
    db_expressions = await db.fetch_expressions(experiment_result_id=TEST_EXPERIMENT_RESULT_ID)
    assert db_expressions[0] == TEST_GENE_EXPRESSION


# TEST TRANSACTIONS
@pytest.mark.asyncio
async def test_transaction(db: Database, db_cleanup):
    async with db.transaction_connection() as conn:
        try:
            await db.create_experiment_result(TEST_EXPERIMENT_RESULT, conn)
            await db.create_gene_expressions([TEST_GENE_EXPRESSION, TEST_GENE_EXPRESSION], conn)
            assert False
        except:
            assert True
    db_exp = await db.read_experiment_result(TEST_EXPERIMENT_RESULT_ID)
    db_gene_expr = await db.fetch_expressions()
    assert db_exp == None
    assert len(db_gene_expr) == 0
