import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from transcriptomics_data_service.authz.middleware_base import BaseAuthzMiddleware

middleware = BaseAuthzMiddleware()
app = FastAPI()
middleware.attach(app)
client = TestClient(app)


@app.get("/")
async def get_root():
    return {"message": "hello"}


def test_base_authz_middleware():
    try:
        client.get("/")
        assert False
    except NotImplementedError:
        assert True

    assert middleware.dep_ingest_router() is None
    assert middleware.dep_expression_router() is None
    assert middleware.dep_experiment_result_router() is None
