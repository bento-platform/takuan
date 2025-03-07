#!/usr/bin/env bash
export UID=$(id -u)

docker compose -f docker-compose.test.yaml down
docker compose -f docker-compose.test.yaml up  -d --build --wait

docker exec --user "${UID}" tds /bin/bash -c "
    cd /tds &&
    poetry export -f requirements.txt --with dev --output requirements.txt
    pip install --no-cache-dir --user -r requirements.txt
    rm requirements.txt
    pip install -e .
    pytest -svv --cov=transcriptomics_data_service --cov-branch &&
    coverage html
    "

docker compose -f docker-compose.test.yaml down

docker rmi transcriptomics_data_service-tds:latest
