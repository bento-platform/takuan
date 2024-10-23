#!/bin/bash

export ASGI_APP="transcriptomics_data_service.main:app"

# Set default internal port to 5000
: "${INTERNAL_PORT:=5000}"

# Extra dependencies installation for authz plugin
if ! [ -f /tds/lib/requirements.txt ]; then
  pip install -r /tds/lib/requirements.txt
fi

uvicorn \
  --workers 1 \
  --loop uvloop \
  --host 0.0.0.0 \
  --port "${INTERNAL_PORT}" \
  "${ASGI_APP}"
