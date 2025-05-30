#!/bin/bash

# Update dependencies and install module locally
poetry export -f requirements.txt --with dev --output requirements.txt
pip install --no-cache-dir --user -r requirements.txt
rm requirements.txt
pip install -e .

# Extra dependencies installation for authz plugin
if [ -f /tds/lib/requirements.txt ]; then
  pip install -r /tds/lib/requirements.txt
fi

export ASGI_APP="transcriptomics_data_service.main:app"

# Set default internal port to 5000
: "${INTERNAL_PORT:=5000}"

python -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:9511 -m \
  uvicorn \
  --host 0.0.0.0 \
  --port "${INTERNAL_PORT}" \
  --reload \
  "${ASGI_APP}"
