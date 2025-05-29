-- Change gene_expressions.raw_count from INTEGER to FLOAT and allow NULL
ALTER TABLE gene_expressions ALTER COLUMN raw_count DROP NOT NULL;
ALTER TABLE gene_expressions ALTER COLUMN raw_count TYPE FLOAT;

-- Add fpkm_count COLUMN to GENE_EXPRESSION
ALTER TABLE gene_expressions ADD COLUMN IF NOT EXISTS fpkm_count FLOAT;

