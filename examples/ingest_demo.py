import requests

# Example values, adapt to your needs
MY_EXPERIMENT_ID = "HELPING-DAISIE"
MY_ASSEMBLY_ID = "GCF_000001405.40"
MY_ASSEMBLY_NAME = "GRCh38.p14"

# Local endpoint, change if using a remote endpoint
TAKUAN_ENDPOINT = "http://localhost:5000"

##### Create an experiment with POST /experiment
r = requests.post(
    f"{TAKUAN_ENDPOINT}/experiment",
    json={
        "experiment_result_id": MY_EXPERIMENT_ID,
        "assembly_id": MY_ASSEMBLY_ID,
        "assembly_name": MY_ASSEMBLY_NAME,
        "extra_properties": {
            # arbitrary extra properties
            "something": "something else"
        },
    },
)

##### Load data to send in ingestion request

# Bytes can be read from a file
file_data: bytes = b""
with open("examples/my-sample-example.tsv", "rb") as data_file:
    file_data = data_file.read()

# Or they can be converted from a string
tsv_string_data = """gene_id	abundance	counts	length	countsFromAbundance
ENSG00000000938	5.168539	727.0001	1814.54375737582	no
ENSG00000000971	5.33253621	826.86235	3328.23573203574	no
ENSG00000001036	5.298295	6524.4007	2383.15248504693	no
ENSG00000001084	4.3898788	15743.07438	2625.59540961572	no
"""
string_data = bytes(tsv_string_data, "utf-8")

##### Ingest the data (TSV)!

# Ingests file data with abundance column as TPM normalized
file_sample = "SAMPLE_12345"
r_file_data = requests.post(
    f"{TAKUAN_ENDPOINT}/experiment/{MY_EXPERIMENT_ID}/ingest/single?sample_id={file_sample}&norm_type=tpm",
    data=dict(data=file_data),
)
print(f"Ingest status code (file bytes): {r_file_data.status_code}")

# Ingests string data with abundance column as TMM normalized
string_sample = "SAMPLE_54321"
r_string_data = requests.post(
    f"{TAKUAN_ENDPOINT}/experiment/{MY_EXPERIMENT_ID}/ingest/single?sample_id={string_sample}&norm_type=tmm",
    data=dict(data=string_data),
)
print(f"Ingest status code (encoded string): {r_string_data.status_code}")
