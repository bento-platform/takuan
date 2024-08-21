from pydantic import BaseModel

__all__ = [
    "ExperimentResult",
    "GeneExpression",
]

class ExperimentResult(BaseModel):
    experiment_result_id: str
    assembly_id: str | None = None
    assembly_name: str | None = None
