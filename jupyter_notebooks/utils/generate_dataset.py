import numpy as np
import pandas as pd
from scipy.stats import ttest_ind
from statsmodels.stats.multitest import multipletests

def simulate_counts(genes, de_down, de_up, n_control, n_treatment,
                    dropout_rate_nonDE, dropout_rate_DE, outlier_rate, outlier_factors, seed=None):
    """
    Simulates a raw count matrix with built-in dropouts and outlier events.
    Returns:
      - df_counts: DataFrame of simulated counts (genes as rows, samples as columns)
      - gene_events: Dictionary with an informative summary of events per gene
    """
    if seed is not None:
        np.random.seed(seed)

    baseline = {gene: np.random.randint(100, 300) for gene in genes}
    data = {}
    gene_events = {}

    for gene in genes:
        mu = baseline[gene]
        # Generate control and treatment counts (Poisson distributed)
        control_counts = np.random.poisson(lam=mu, size=n_control)
        if gene in de_down:
            treatment_mu = mu * 0.5  # ~50% reduction
        elif gene in de_up:
            treatment_mu = mu * 2.0  # ~2-fold increase
        else:
            treatment_mu = mu
        treatment_counts = np.random.poisson(lam=treatment_mu, size=n_treatment)
        counts = np.concatenate([control_counts, treatment_counts])

        # Select dropout rate based on DE status
        gene_dropout_rate = dropout_rate_DE if gene in (de_down + de_up) else dropout_rate_nonDE

        new_counts = []
        # Counters for informative event summary
        control_dropout = treatment_dropout = 0
        control_outlier = treatment_outlier = 0

        # Process each replicate
        for idx, count in enumerate(counts):
            group = "Control" if idx < n_control else "Treatment"
            if np.random.random() < gene_dropout_rate:
                new_counts.append(0)
                if group == "Control":
                    control_dropout += 1
                else:
                    treatment_dropout += 1
            else:
                modified_count = count
                if np.random.random() < outlier_rate:
                    factor = np.random.choice(outlier_factors)
                    modified_count *= factor
                    if group == "Control":
                        control_outlier += 1
                    else:
                        treatment_outlier += 1
                new_counts.append(modified_count)

        data[gene] = new_counts

        events = []
        if control_dropout:
            events.append(f"{control_dropout} Control dropout(s)")
        if treatment_dropout:
            events.append(f"{treatment_dropout} Treatment dropout(s)")
        if control_outlier:
            events.append(f"{control_outlier} Control outlier(s)")
        if treatment_outlier:
            events.append(f"{treatment_outlier} Treatment outlier(s)")
        gene_events[gene] = "; ".join(events) if events else "None"

    sample_names = [f'Control_{i+1}' for i in range(n_control)] + [f'Treatment_{i+1}' for i in range(n_treatment)]
    df_counts = pd.DataFrame(data, index=sample_names).T
    return df_counts, data, gene_events

def perform_de_analysis(data, gene_events, n_control, n_treatment):
    """
    Performs a simple differential expression analysis (using a t-test) and returns a DataFrame
    with log2 fold changes, p-values, FDR-adjusted p-values, regulation direction, observed events, and rank.
    """
    genes_list, log2fc_list, pval_list = [], [], []
    regulation_list, observed_events_list = [], []

    for gene, counts in data.items():
        control = counts[:n_control]
        treatment = counts[n_control:]
        # Adding 1 to avoid division by zero
        mean_control = np.mean(control) + 1
        mean_treatment = np.mean(treatment) + 1
        log2fc = np.log2(mean_treatment / mean_control)

        # General T-test for demonstration purposes (method not specializad for RNA-seq)
        stat, pval = ttest_ind(treatment, control, equal_var=False)
        if np.isnan(pval):
            pval = 1.0

        if log2fc > 0:
            regulation = "Upregulated"
        elif log2fc < 0:
            regulation = "Downregulated"
        else:
            regulation = "No change"

        genes_list.append(gene)
        log2fc_list.append(round(log2fc, 2))
        pval_list.append(pval)
        regulation_list.append(regulation)
        observed_events_list.append(gene_events.get(gene, "None"))

    # FDR correction using Benjamini-Hochberg
    _, adj_pvals, _, _ = multipletests(pval_list, method="fdr_bh")

    df_de = pd.DataFrame({
        "Gene": genes_list,
        "Log2 Fold Change": log2fc_list,
        "p-value": pval_list,
        "Adjusted p-value (FDR)": adj_pvals,
        "Regulation": regulation_list,
        "Observed Events": observed_events_list
    })
    # Rank based on absolute log2 fold change (largest difference gets Rank 1)
    df_de["Rank"] = df_de["Log2 Fold Change"].abs().rank(method="min", ascending=False).astype(int)
    df_de.sort_values("Rank", inplace=True)
    return df_de

def main():
    # List of 100 genes
    genes = [
        'A1BG', 'A1BG-AS1', 'A1CF', 'A2M', 'A2M-AS1', 'A2ML1', 'A2MP1', 'A3GALT2', 
        'A4GALT', 'A4GNT', 'AA06', 'AAAS', 'AACS', 'AACSP1', 'AADAC', 'AADACL2', 
        'AADACL2-AS1', 'AADACL3', 'AADACL4', 'AADACP1', 'AADAT', 'AAGAB', 'AAK1', 
        'AAMDC', 'AAMP', 'AANAT', 'AAR2', 'AARD', 'AARS1', 'AARS2', 'AARSD1', 
        'AASDH', 'AASDHPPT', 'AASS', 'AATBC', 'AATF', 'AATK', 'ABALON', 'ABAT', 
        'ABCA1', 'ABCA10', 'ABCA11P', 'ABCA12', 'ABCA13', 'ABCA17P', 'ABCA2', 'ABCA3', 
        'ABCA4', 'ABCA5', 'ABCA6', 'ABCA7', 'ABCA8', 'ABCA9', 'ABCA9-AS1', 'ABCB1', 
        'ABCB10', 'ABCB11', 'ABCB4', 'ABCB5', 'ABCB6', 'ABCB7', 'ABCB8', 'ABCB9', 
        'ABCC1', 'ABCC10', 'ABCC11', 'ABCC12', 'ABCC13', 'ABCC2', 'ABCC3', 'ABCC4', 
        'ABCC5', 'ABCC5-AS1', 'ABCC6', 'ABCC6P1', 'ABCC6P2', 'ABCC8', 'ABCC9', 
        'ABCD1', 'ABCD2', 'ABCD3', 'ABCD4', 'ABCE1', 'ABCF1', 'ABCF1-DT', 'ABCF2', 
        'ABCF2-H2BK1', 'ABCF3', 'ABCG1', 'ABCG2', 'ABCG4', 'ABCG5', 'ABCG8', 
        'ABHD1', 'ABHD10', 'ABHD11', 'ABHD11-AS1', 'ABHD12', 'ABHD12B', 'ABHD13'
    ]

    de_down = genes[:10]   # Genes 1-10: downregulated (~50% reduction)
    de_up   = genes[10:20]  # Genes 11-20: upregulated (~2-fold increase)
    
    # Simulation parameters
    n_control = 5
    n_treatment = 5
    dropout_rate_nonDE = 0.10
    dropout_rate_DE = 0.05
    outlier_rate = 0.03
    outlier_factors = [5, 10]
    seed = 42
    
    # Simulate counts
    df_counts, data, gene_events = simulate_counts(
        genes, de_down, de_up, n_control, n_treatment,
        dropout_rate_nonDE, dropout_rate_DE, outlier_rate, outlier_factors, seed
    )
    df_counts.to_csv("simulated_raw_counts.csv", index=True)
    print("Simulated raw count matrix saved to 'simulated_raw_counts.csv'.")
    
    # Perform differential expression analysis inspection - only for overview purposes
    df_de = perform_de_analysis(data, gene_events, n_control, n_treatment)
    df_de.to_csv("differential_expression_report.csv", index=False)
    print("Differential expression report saved to 'differential_expression_report.csv'.")

if __name__ == "__main__":
    main()
    