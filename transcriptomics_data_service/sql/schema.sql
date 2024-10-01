CREATE TABLE IF NOT EXISTS experiment_results (
    experiment_result_id VARCHAR(31) NOT NULL PRIMARY KEY,
    assembly_id VARCHAR(63),
    assembly_name VARCHAR(63)
);

CREATE TABLE IF NOT EXISTS gene_expressions (
    gene_code VARCHAR(31) NOT NULL,
    sample_id VARCHAR(31) NOT NULL,
    experiment_result_id VARCHAR(31) NOT NULL REFERENCES experiment_results ON DELETE CASCADE,
    raw_count INTEGER NOT NULL,
    tpm_count FLOAT,
    tmm_count FLOAT,
    PRIMARY KEY (gene_code, sample_id, experiment_result_id)
);

CREATE INDEX idx_gene_code ON gene_expressions(gene_code);
CREATE INDEX idx_sample_id ON gene_expressions(sample_id);
CREATE INDEX idx_experiment_result_id ON gene_expressions(experiment_result_id);
