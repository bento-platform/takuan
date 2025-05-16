from fastapi import APIRouter, HTTPException, status

from transcriptomics_data_service.authz.plugin import authz_plugin
from transcriptomics_data_service.db import DatabaseDependency
from transcriptomics_data_service.logger import LoggerDependency
from transcriptomics_data_service.models import (
    CountTypesEnum,
    GeneExpression,
    GeneExpressionData,
    GeneExpressionResponse,
    ExpressionQueryBody,
)

expressions_router = APIRouter(prefix="/expressions", dependencies=authz_plugin.dep_expression_router())

DEFAULT_EXPRESSIONS_QUERY = ExpressionQueryBody(
    page=1, page_size=100, method="raw", experiments=[], sample_ids=[], genes=[]
)


async def get_expressions_handler(
    query_body: ExpressionQueryBody,
    db: DatabaseDependency,
    logger: LoggerDependency,
    mapping: GeneExpression | GeneExpressionData,
):
    """
    Handler for fetching and returning gene expression data.
    """
    logger.info(f"Received query parameters: {query_body}")

    expressions, total_records = await db.fetch_gene_expressions(
        genes=query_body.genes,
        experiments=query_body.experiments,
        sample_ids=query_body.sample_ids,
        method=query_body.method,
        pagination=query_body,  # ExpressionQueryBody extends the PaginatedRequest model
        mapping=mapping,
    )

    if not expressions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No gene expression data found for the given parameters.",
        )

    total_pages = (total_records + query_body.page_size - 1) // query_body.page_size

    return GeneExpressionResponse(
        # pagination
        page=query_body.page,
        page_size=query_body.page_size,
        total_records=total_records,
        total_pages=total_pages,
        # data
        expressions=expressions,
        query=query_body,
    )


@expressions_router.post(
    "",
    status_code=status.HTTP_200_OK,
    response_model=GeneExpressionResponse,
    dependencies=authz_plugin.dep_authz_expressions_list(),
)
async def get_expressions_post(
    db: DatabaseDependency,
    logger: LoggerDependency,
    params: ExpressionQueryBody = DEFAULT_EXPRESSIONS_QUERY,
    full: bool = False,
):
    """
    Retrieve gene expression data via POST request.\n
    Filter the items by genes, experiments, samples and count methods with a body of type `ExpressionQueryBody`.\n
    The `ExpressionQueryBody.method` helps filtering results by count method: \n
    - If NOT provided, returns all expressions for the query
    - If provided, only returns expressions for which this count is NOT NULL.\n
    To include all counts in the response, use the `full` query parameter.\n
    If `full` is false or unset and no `ExpressionQueryBody.method` is provided, `raw` counts will be used by default.\n
    """
    if full:
        mapping = GeneExpression
    else:
        mapping = GeneExpressionData
        if not params.method:
            logger.warning("Using count type 'raw'")
            params.method = CountTypesEnum.raw
    return await get_expressions_handler(params, db, logger, mapping)
