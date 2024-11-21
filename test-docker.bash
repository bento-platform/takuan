#!/usr/bin/env bash
export UID=$(id -u)

docker compose -f docker-compose.test.yaml down
docker compose -f docker-compose.test.yaml up  -d --build --wait

docker exec tds /bin/bash -c "
    cd /tds &&
    /poetry_user_install_dev.bash &&
    pytest -svv --cov=transcriptomics_data_service --cov-branch &&
    coverage html
    "

docker compose -f docker-compose.test.yaml down

docker rmi transcriptomics_data_service-tds:latest
