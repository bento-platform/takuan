# transcriptomics_data_service

WORK IN PROGRESS.

The Transcriptomics Data Service (TDS) is intended to ingest, organize and query data from transcriptomics experiments through an API.

## Starting a standalone TDS

Start the TDS server with a database for testing by running the following command.
```bash
docker compose up --build
```
The `--build` argument forces the image to be rebuilt. Be sure to use it if you want code changes to be present.

You can now interact with the API by querying `localhost:5000/{endpoint}`

## Endpoints

* /service-info
  * GA4GH service info
* /ingest (TODO)
