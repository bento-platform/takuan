# Ingestion

Data is ingested in Takuan via API requests, making it possible to write scripts that perform the ingestion for you.

This page presents simple Python examples that allow to programatically ingest data in Takuan's database.

## Prerequisites
- A running Takuan deployment
- Transcriptomic data files
  - Single-sample CSV/TSV files
  - OR multi-sample CSV file
- Python and a terminal

## Ingesting a single sample TSV file

[Here](ingest_demo.py) is an example Python script for single-sample TSV ingestions with the `requests` library.


