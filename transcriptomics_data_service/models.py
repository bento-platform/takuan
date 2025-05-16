from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from enum import Enum
from bento_lib.service_info.types import GA4GHServiceOrganizationModel

__all__ = [
    "ExperimentResult",
    "GeneExpression",
    "GeneExpressionData",
    "GeneExpressionResponse",
    "NormalizationMethodEnum",
    "ExpressionQueryBody",
    "CountTypesEnum",
    "PaginatedRequest",
    "PaginatedResponse",
    "FeaturesResponse",
    "SamplesResponse",
]


TPM = "tpm"
TMM = "tmm"
GETMM = "getmm"
RAW = "raw"
FPKM = "fpkm"


class NormalizationMethodEnum(str, Enum):
    tpm = TPM
    tmm = TMM
    getmm = GETMM
    fpkm = FPKM


class CountTypesEnum(str, Enum):
    raw = RAW
    # normalized counts
    tpm = TPM
    tmm = TMM
    getmm = GETMM
    fpkm = FPKM


#####################################
# PAGINATION MODELS
#####################################
class PaginatedRequest(BaseModel):
    page: int = Field(1, ge=1, description="Current page number")
    page_size: int = Field(100, ge=1, le=1000, description="Number of records per page")


class PaginatedResponse(PaginatedRequest):
    total_records: int = Field(..., ge=0, description="Total number of records")
    total_pages: int = Field(..., ge=1, description="Total number of pages")


#####################################
# EXPERIMENTS
#####################################
class ExperimentResult(BaseModel):
    experiment_result_id: str = Field(..., min_length=1, max_length=255)
    assembly_id: str | None = Field(None, max_length=255)
    assembly_name: str | None = Field(None, max_length=255)
    extra_properties: dict | None = Field(None)


class SamplesResponse(PaginatedResponse):
    samples: List[str]


class FeaturesResponse(PaginatedResponse):
    features: List[str]


#####################################
# GENE EXPRESSIONS
#####################################
class GeneExpression(BaseModel):
    gene_code: str = Field(..., min_length=1, max_length=255, description="Feature identifier")
    sample_id: str = Field(..., min_length=1, max_length=255, description="Sample identifier")
    experiment_result_id: str = Field(..., min_length=1, max_length=255, description="ExperimentResult identifier")
    raw_count: float | None = Field(None, ge=0, description="The raw count for the given feature")
    tpm_count: float | None = Field(None, ge=0, description="TPM normalized count")
    tmm_count: float | None = Field(None, ge=0, description="TMM normalized count")
    getmm_count: float | None = Field(None, ge=0, description="GETMM normalized count")
    fpkm_count: float | None = Field(None, ge=0, description="FPKM normalized count")


class GeneExpressionData(BaseModel):
    gene_code: str = Field(..., min_length=1, max_length=255, description="Gene code")
    sample_id: str = Field(..., min_length=1, max_length=255, description="Sample ID")
    experiment_result_id: str = Field(..., min_length=1, max_length=255, description="Experiment result ID")
    count: float | None = Field(None, description="Expression count")


class ExpressionQueryBody(PaginatedRequest):
    genes: List[str] | None = Field(None, description="List of gene codes to retrieve")
    experiments: List[str] | None = Field(None, description="List of experiment result IDs to retrieve data from")
    sample_ids: List[str] | None = Field(None, description="List of sample IDs to retrieve data from")
    method: CountTypesEnum = Field(
        CountTypesEnum.raw,
        description=f"Data method to retrieve: {', '.join([c.value for c in CountTypesEnum])}",
    )


class GeneExpressionResponse(PaginatedResponse):
    query: ExpressionQueryBody = Field(..., description="The query that produced this response")
    expressions: List[GeneExpressionData] = Field(..., description="List of gene expressions")


class GeneExpressionMapper(BaseModel):
    """
    Mapping class for flexible handling of CSV/TSV files with different columns.
    """

    feature_col: str
    raw_count_col: str
    tpm_count_col: str
    tmm_count_col: str
    getmm_count_col: str
    fpkm_count_col: str


#####################################
# GA4GH Service Info
#####################################


class ServiceType(BaseModel):
    group: str
    artifact: str
    version: str


class ServiceInfo(BaseModel):
    # Required
    id: str
    name: str
    type: ServiceType
    organization: GA4GHServiceOrganizationModel
    version: str

    # Not required
    contactUrl: Optional[str] = None
    documentationUrl: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    environment: Optional[str] = None

    # Allow extra properties to extend the spec
    model_config = ConfigDict(extra="allow")
