from enum import Enum
from pydantic import BaseModel

__all__ = [
    "ExperimentResult",
    "GeneExpression",
    "NormalizationAlgos"
]


class ExperimentResult(BaseModel):
    experiment_result_id: str
    assembly_id: str | None = None
    assembly_name: str | None = None


class GeneExpression(BaseModel):
    gene_code: str
    sample_id: str
    experiment_result_id: str
    raw_count: int
    tpm_count: float | None = None
    tmm_count: float | None = None
    getmm_count: float | None = None


class NormalizationAlgos(str, Enum):
    # Constants for normalization methods
    TPM = "tpm"
    TMM = "tmm"
    GETMM = "getmm"
