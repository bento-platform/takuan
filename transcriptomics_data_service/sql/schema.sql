CREATE TABLE IF NOT EXISTS experiment_results (
    experiment_result_id VARCHAR(31) NOT NULL PRIMARY KEY,
    assembly_id VARCHAR(63),
    assembly_name VARCHAR(63)
);
