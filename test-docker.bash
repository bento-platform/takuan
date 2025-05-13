#!/usr/bin/env bash
export UID=$(id -u)

# Take down old test containers
docker compose -f docker-compose.test.yaml down
# Build and run new test containers
docker compose -f docker-compose.test.yaml up  -d --build --wait

# Run tests
docker exec --user "${UID}" tds /bin/bash -c "
    cd /tds &&
    poetry export -f requirements.txt --with dev --output requirements.txt
    pip install --no-cache-dir --user -r requirements.txt
    rm requirements.txt
    pip install -e .
    pytest -svv --cov=transcriptomics_data_service --cov-branch &&
    coverage html
    "

# Remove containers and images
docker compose -f docker-compose.test.yaml down
docker system prune -f \
    --filter "label=takuan.image.kind=test"
