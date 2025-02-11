import os
import json

os.environ["CORS_ORIGINS"] = "*"
os.environ["AUTHZ_ENABLED"] = "False"
os.environ["DB_PASSWORD"] = ""

from transcriptomics_data_service.main import app

with open('openapi.json', 'w') as f:
    json.dump(app.openapi(), f)
