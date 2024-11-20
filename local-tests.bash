#!/usr/bin/env bash
export UID=$(id -u)

docker compose -f docker-compose.test.yaml down
docker compose -f docker-compose.test.yaml run --rm tds
docker compose -f docker-compose.test.yaml down

docker rmi
