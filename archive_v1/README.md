# Archive v1: Initial INSDC Provenance Analysis

This folder contains the first iteration of the INSDC provenance analysis, archived on 12 October 2026.

## Why archived

The v1 analysis used NCBI BioSample's `country="X"[all]` query syntax, which does exact text matching and misses records with sub-national detail (e.g., "USA: California" doesn't match `country="USA"[all]`). This resulted in NCBI per-country sums being only 39% of the NCBI total. The v2 analysis uses the `[country]` field tag, which provides broader matching.

The v1 analysis also included an environmental DNA focus (Map 3) that has been dropped from v2 per the user's request.

## Contents

- `INSDC_Provenance_Cali_Fund_Assessment.md` — Full assessment document (v1)
- `insdc_provenance_country_maps.csv` — Main country-level table
- `ena_per_country_counts.csv` — Raw ENA per-country counts
- `ena_period_counts.csv` — ENA per-country 3-year period counts
- `ena_period_by_income.csv` — Period counts by WB income group
- `ena_period_by_vulnerability.csv` — Period counts by LDC/SIDS/LLDC
- `insdc_counts_*.csv` — NCBI BioSample per-country counts (3 files)
- `insdc_provenance_final_analysis.json` — Full analysis JSON
- `*.py` — Analysis and mapping scripts
- `*.html` — Interactive choropleth maps
