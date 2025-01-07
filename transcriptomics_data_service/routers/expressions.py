from fastapi import APIRouter, HTTPException, status, Query

from transcriptomics_data_service.db import DatabaseDependency
from transcriptomics_data_service.logger import LoggerDependency
from transcriptomics_data_service.models import (
    GeneExpressionData,
    GeneExpressionResponse,
    MethodEnum,
    ExpressionQueryBody,
)

expressions_router = APIRouter(prefix="/expressions")


async def get_expressions_handler(
    query_body: ExpressionQueryBody,
    db: DatabaseDependency,
    logger: LoggerDependency,
):
    """
    Handler for fetching and returning gene expression data.
    """
    logger.info(f"Received query parameters: {query_body}")

    expressions, total_records = await db.fetch_gene_expressions(
        genes=query_body.genes,
        experiments=query_body.experiments,
        sample_ids=query_body.sample_ids,
        method=query_body.method.value,
        page=query_body.page,
        page_size=query_body.page_size,
    )

    if not expressions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No gene expression data found for the given parameters.",
        )

    method = query_body.method.value
    method_count_field = f"{method}_count"
    response_data = [
        GeneExpressionData(
            gene_code=expr.gene_code,
            sample_id=expr.sample_id,
            experiment_result_id=expr.experiment_result_id,
            count=getattr(expr, method_count_field),
        )
        for expr in expressions
    ]

    total_pages = (total_records + query_body.page_size - 1) // query_body.page_size

    return GeneExpressionResponse(
        # pagination
        page=query_body.page,
        page_size=query_body.page_size,
        total_records=total_records,
        total_pages=total_pages,
        # data
        expressions=response_data,
        query=query_body
    )


@expressions_router.post(
    "",
    status_code=status.HTTP_200_OK,
    response_model=GeneExpressionResponse,
)
async def get_expressions_post(
    params: ExpressionQueryBody,
    db: DatabaseDependency,
    logger: LoggerDependency,
):
    """
    Retrieve gene expression data via POST request.
    Using POST instead of GET in order to add a body of type ExpressionQueryBody

    Example JSON body:
    {
        "genes": ["gene1", "gene2"],
        "experiments": ["exp1"],
        "sample_ids": ["sample1"],
        "method": "tmm",
        "page": 1,
        "page_size": 100
    }
    """
    return await get_expressions_handler(params, db, logger)
