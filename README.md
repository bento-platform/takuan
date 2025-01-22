# transcriptomics_data_service

![Test Status](https://github.com/bento-platform/transcriptomics_data_service/actions/workflows/test.yml/badge.svg)
[![codecov](https://codecov.io/gh/bento-platform/transcriptomics_data_service/graph/badge.svg)](https://codecov.io/gh/bento-platform/transcriptomics_data_service)
![Lint Status](https://github.com/bento-platform/transcriptomics_data_service/actions/workflows/lint.yml/badge.svg)
![Docker Build](https://github.com/bento-platform/transcriptomics_data_service/actions/workflows/build.yml/badge.svg)

**Disclaimer: work in progress.**

The Transcriptomics Data Service (TDS) is intended to ingest, organize and query data from transcriptomics experiments through an API.

## Starting a standalone TDS

Start the TDS server with a local PostgreSQL database for testing by running the following command.
```bash
# start
docker compose up --build -d

# stop
docker compose down
```
The `--build` argument forces the image to be rebuilt. Be sure to use it if you want code changes to be present.

You can now interact with the API by querying `localhost:5000/{endpoint}`

For the OpenAPI browser interface, go to `localhost:5000/docs`.

## Local dev

For local development, you can use the [docker-compose.dev.yaml](./docker-compose.dev.yaml) file to start a TDS 
[development container](https://code.visualstudio.com/docs/devcontainers/containers) that mounts the local directory.
The server starts in reload mode to quickly reflect local changes, and debugpy is listening on the container's internal port `9511`.

```bash
# Set UID for directory permissions in the container
export UID=$(id -u)

# start
docker compose -f ./docker-compose.dev.yaml up --build -d

# stop
docker compose -f ./docker-compose.dev.yaml down
```

You can then attach VS Code to the `tds` container, and use the preconfigured `Python Debugger (TDS)` for interactive debugging.

## Using Docker Secrets for the PostgreSQL credential

The TDS [`Config`](./transcriptomics_data_service/config.py) object has its values populated from environment variables and secrets at startup.

The `Config.db_password` value is populated by either:
- `DB_PASSWORD=<a secure password>` if using an environment variable
  - As seen in [docker-compose.dev.yaml](./docker-compose.dev.yaml)
- `DB_PASSWORD_FILE=/run/secrets/db_password` if using a Docker secret (recommended)
  - As seen in [docker-compose.secrets.dev.yaml](./docker-compose.secrets.dev.yaml)

Using a Docker secret is recommended for security, as environment variables are more prone to be leaked.

`DB_PASSWORD` should only be considered for local development, or if the database is secured and isolated from public access in a private network.

## Authorization plugin

The Transcriptomics Data Service is meant to be a reusable microservice that can be integrated in existing 
stacks. Since authorization schemes vary across projects, TDS allows adopters to code their own authorization plugin, 
enabling adopters to leverage their existing access control code, tools and policies.

See the [authorization docs](./docs/authz.md) for more information on how to create and use the authz plugin with TDS.

## Endpoints

TODO: replace this with Swagger UI docs generated from CI workflows.

* `/service-info`
  * GA4GH service info
* `/ingest`
* `/normalize`
* `/expressions`
* `/experiment`
* `/search` (WIP)

## Docker images

The Transcriptomics Data Service is packaged and released as a Docker image using GitHub Actions.

Images are published in GitHub's container registry, [here](https://github.com/bento-platform/transcriptomics_data_service/pkgs/container/transcriptomics_data_service).

Images are built and published using the following tags:
- `<version>`: Build for a tagged release
- `latest`: Build for the latest tagged release
- `edge`: The top of the `main` branch
- `pr-<number>`: Build for a pull request that targets `main`

Note: Images with the `-dev` suffix (e.g. `edge-dev`) are for local development.


To pull an image, or reference it in a compose file, use this pattern:

```shell
docker pull ghcr.io/bento-platform/transcriptomics_data_service:<TAG>
```
