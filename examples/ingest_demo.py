import json
import requests

# Example values, adapt to your needs
MY_EXPERIMENT_ID = "EXP_12345"
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

##### Load data to send in ingestion requests

# Bytes can be read from a file
file_data: bytes = b""
with open("examples/my-sample-example.tsv", "rb") as data_file:
    # TSV HEADERS: gene_id	abundance	counts	length	countsFromAbundance
    file_data = data_file.read()

# Ingests file data with 'abundance' column as TPM normalized
file_sample = "SAMPLE_12345"
r_file_data = requests.post(
    f"{TAKUAN_ENDPOINT}/experiment/{MY_EXPERIMENT_ID}/ingest/single",
    files={"data": file_data},
    data={
        "sample_id": file_sample,
        # column mappings
        "raw_count_col": "counts",
        "tpm_count_col": "abundance",
    },
)
print(f"Ingest status code (TSV file bytes): {r_file_data.status_code}")

# Or they can be converted from a string
tsv_string_data = """gene_id	abundance	counts	length	countsFromAbundance
ENSG00000000938	5.168539	727.0001	1814.54375737582	no
ENSG00000000971	5.33253621	826.86235	3328.23573203574	no
ENSG00000001036	5.298295	6524.4007	2383.15248504693	no
ENSG00000001084	4.3898788	15743.07438	2625.59540961572	no
"""
string_data = bytes(tsv_string_data, "utf-8")

# Ingests string data with 'abundance' column as TMM normalized
r_string_data = requests.post(
    f"{TAKUAN_ENDPOINT}/experiment/{MY_EXPERIMENT_ID}/ingest/single",
    files={"data": string_data},
    data={
        "sample_id": "SAMPLE_54321",
        # column mappings
        "raw_count_col": "counts",
        "tmm_count_col": "abundance",
    },
)
print(f"Ingest status code (encoded TSV string): {r_string_data.status_code}")

### /ingestion/single also handles CSV
csv_sample_id = "SAMPLE_CSV_9876"
csv_file_data: bytes = b""
with open("tests/data/single_sample_detailed.csv", "rb") as file:
    # CSV headers: feature,count,tpm,tmm,getmm,fpkm
    csv_file_data = file.read()

# Will fail, default feature_col and raw_count_col mappers are not in the CSV file
r_csv_data = requests.post(
    f"{TAKUAN_ENDPOINT}/experiment/{MY_EXPERIMENT_ID}/ingest/single",
    files={"data": csv_file_data},
    data={
        "sample_id": csv_sample_id,
        # mapper defaults
        # "feature_col": "gene_id",
        # "raw_count_col": "counts"
    },
)
print(f"Ingest status code, needs map (CSV file bytes): {r_csv_data.status_code}")
print(f"    {r_csv_data.json()['detail']}")

r_csv_data = requests.post(
    f"{TAKUAN_ENDPOINT}/experiment/{MY_EXPERIMENT_ID}/ingest/single",
    files={"data": csv_file_data},
    data={
        "sample_id": csv_sample_id,
        # column mappings
        "feature_col": "feature",
        "raw_count_col": "count",
    },
)
print(f"Ingest status code, correct mappings (CSV file bytes): {r_csv_data.status_code}")

########## Ingest multiple normalized values at once
# CSV with TPM, FPKM and GETMM normalized data
multi_norm_data_csv = """gene_id, tpm, fpkm, getmm
ENSG00000000938, 5.168539, 727.0001, 1814.54375737582
ENSG00000000971, 5.33253621, 826.86235, 3328.23573203574
ENSG00000001036, 5.298295, 6524.4007, 2383.15248504693
ENSG00000001084, 4.3898788, 15743.07438, 2625.59540961572
"""
multi_norm_data = bytes(multi_norm_data_csv, "utf-8")

MULTI_NORM_SAMPLE_ID = "MULTI_NORM_1234"
r_multi_norm = requests.post(
    f"{TAKUAN_ENDPOINT}/experiment/{MY_EXPERIMENT_ID}/ingest/single",
    files={"data": multi_norm_data},
    data={
        "sample_id": MULTI_NORM_SAMPLE_ID,
        # Column mappings
        "feature_col": "gene_id",
        "tpm_count_col": "tpm",
        "fpkm_count_col": "fpkm",
        "getmm_count_col": "getmm",
    },
)
print(f"Status for multiple normalised values ingestion: {r_multi_norm.status_code}")

r_query = requests.post(f"{TAKUAN_ENDPOINT}/expressions", json={"sample_ids": [MULTI_NORM_SAMPLE_ID], "method": "fpkm"})
print("Get expressions values from the /expressions endpoint")
print(json.dumps(r_query.json(), indent=2))
