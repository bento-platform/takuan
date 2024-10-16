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

### Using an authorization plugin

When starting the TDS container, the FastAPI server will attempt to dynamicaly load the authorization plugin 
middleware from `lib/authz.module.py`.

If authorization is enabled and there is no file at `lib/authz.module.py`, an exception will be thrown and the server
will not start.

Furthermore, the content of the file must follow some implementation guidelines:
from transcriptomics_data_service.authz.middleware_base import BaseAuthzMiddleware

- You MUST declare a concrete class that extends [BaseAuthzMiddleware](./transcriptomics_data_service/authz/middleware_base.py)
- In that class, you MUST implement the functions from BaseAuthzMiddleware with the expected signatures:
  - `attach`: used to attach the middleware to the FastAPI app
  - `dipatch`: called for every request made to the API
  - `dep_authorize_<endpoint>`: endpoint-specific, authz evaluation functions that should return an injectable function

Looking at [bento.authz.module.py](./etc/bento.authz.module.py), we can see an implementation that is specific to 
Bento's authorization service and libraries.

Rather than directly implementing the `attach`, `dispatch` and other authorization logic, we rely on the `bento-lib` 
`FastApiAuthMiddleware`, which already provides a reusable authorization middleware for FastAPI.

The only thing left to do is to implement the endpoint-specific authorization functions.

## Endpoints

* /service-info
  * GA4GH service info
* /ingest (TODO)
