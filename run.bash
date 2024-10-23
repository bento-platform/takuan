#!/bin/bash

export ASGI_APP="transcriptomics_data_service.main:app"

# Set default internal port to 5000
: "${INTERNAL_PORT:=5000}"

if ! [ -f /tds/lib/requirements.txt ]; then
  echo "Installing authz plugin dependencies"
  pip3 install -r /tds/lib/requirements.txt
fi

uvicorn \
  --workers 1 \
  --loop uvloop \
  --host 0.0.0.0 \
  --port "${INTERNAL_PORT}" \
  "${ASGI_APP}"
