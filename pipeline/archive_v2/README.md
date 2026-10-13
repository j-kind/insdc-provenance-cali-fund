# Archived v2 Pipeline (Period Buckets)

This directory contains the v2 pipeline (`run_pipeline.py`) that was superseded by the current 3-script pipeline (`query_annual_counts.py` → `aggregate_countries.py` → `analyze_disparities.py`).

## Why it was archived

The v2 pipeline used 3-year period buckets (2018-2020, 2021-2023, 2024+) instead of annual counts. It also lacked:

1. **Sub-national collision exclusions** — `country="Mexico"` matched "USA: New Mexico", `country="Georgia"` matched "USA: Georgia" (US state), `country="Mongolia"` matched "China: Inner Mongolia", etc. The current pipeline applies 17 collision exclusions.
2. **Non-vocab country values** — alternative names (United States, UK, England), locality names (Japanese/Chinese sites), and placeholders (NULL, na, None) were not included. The current pipeline includes 32 non-vocab values.
3. **Synthetic construct exclusion** — the v2 filter was `NOT tax_tree(9606) AND NOT host_tax_id=9606`; the current pipeline adds `AND NOT tax_tree(32630)` to exclude synthetic constructs.
4. **Annual granularity** — period buckets cannot be decomposed into individual years. The current pipeline queries per-year counts directly.
5. **Undated bucket** — the v2 pipeline did not separately report records with no `first_public` date (21.5% of records). The current pipeline includes an explicit "undated" column.

## Files

| File | Description |
|------|-------------|
| `run_pipeline.py` | The v2 pipeline script (6 stages) |
| `ena_counts.csv` | ENA counts by period bucket (with collision contamination) |
| `ncbi_crosscheck.csv` | NCBI ESearch cross-check counts |
| `country_master.csv` | Country mapping table |
| `country_provenance_counts.csv` | Per-country counts with classifications (contaminated) |
| `analysis_results.json` | Full analysis in JSON |
| `map_all_records.html` | Choropleth map |
| `SUMMARY.md` | v2 summary assessment |
| `non_vocab_counts.csv` | Intermediate file from building annual counts |

The v2 pipeline was replaced on 2026-10-12. See `pipeline/output/annual_counts_methodology.md` for the current methodology.
