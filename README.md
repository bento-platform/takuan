# transcriptomics_data_service

WORK IN PROGRESS.

The Transcriptomics Data Service (TDS) is intended to ingest, organize and query data from transcriptomics experiments through an API.

## Starting a standalone TDS

Start the TDS server with a database for testing by running the following command.
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
# start
docker compose -f ./docker-compose.dev.yaml up --build -d

# stop
docker compose -f ./docker-compose.dev.yaml down
```

You can then attach VS Code to the `tds` container, and use the preconfigured `Python Debugger (TDS)` for interactive debugging.

## Authorization plugin

Although TDS is part of the Bento platform, it is meant to be reusable in other software stacks.
Since authorization requirements and technology vary wildy across different projects, 
TDS allows adopters to write their own authorization logic in python.

For Bento, we rely on API calls to a custom authorization service, 
see [etc/bento.authz.module.py](./etc/bento.authz.module.py) for an example.

For different authorization requirements, you could choose to write a custom module that performs authorization checks based on:
* An API key in the request header or in a cookie
* A JWT bearer token, for example you could:
  * Allow/Deny simply based on the token's validity (decode + TTL)
  * Allow/Deny based on the presence of a scope in the token
  * Allow/Deny based on the presence of a group membership claim
* The results of API calls to an authorization service
* Policy engine evaluations, like OPA or Casbin

TODO: add more details as this takes shape

## Endpoints

* /service-info
  * GA4GH service info
* /ingest (TODO)
