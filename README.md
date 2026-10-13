# INSDC Provenance Country-Level DSI Counts for the Cali Fund

Country-level annual counts of non-human digital sequence information (DSI) records with geographic provenance, constructed from the INSDC/ENA sample database to assess whether INSDC provenance data could support a country-level allocation methodology for the CBD Cali Fund.

## Repository structure

```
ahteg_allocation/
├── pipeline/                    End-to-end pipeline (current)
│   ├── README.md                Pipeline documentation
│   ├── query_annual_counts.py   Step 1: Query ENA /count for annual per-country counts
│   ├── aggregate_countries.py   Step 2: Aggregate onto canonical sovereign countries
│   ├── analyze_disparities.py   Step 3: Analyze global disparities and write report
│   ├── api_evaluation.md        Subagent evaluation of ENA API approach
│   ├── annual_evaluation.md     Subagent evaluation of annual query methodology
│   ├── data/                    Input reference data
│   └── output/                  All pipeline outputs
│       ├── annual_counts.csv              Raw per-country-field-value annual counts
│       ├── annual_counts_methodology.md   Full methodology (15 sections)
│       ├── country_annual_counts.csv      Per-sovereign-country counts + classifications
│       └── analysis_report.md             Disparity analysis report
├── archive_v1/                  Archived v1 pipeline (download-based, superseded)
└── archive_v2/ (in pipeline/)   Archived v2 pipeline (period buckets, superseded)
```

## Quick start

```bash
cd pipeline/
python3 query_annual_counts.py    # ~15 min, queries ENA /count API
python3 aggregate_countries.py    # < 1 sec, aggregates and classifies
python3 analyze_disparities.py    # < 1 sec, generates analysis report
```

See `pipeline/README.md` for full documentation.

## Key findings

- **30.3 million** non-human DSI records (excl. microbiome + synthetic constructs) in ENA
- **19.0 million** (62.7%) attributable to sovereign countries; 37.3% are oceans, placeholders, unattributed, or historical
- **Developed countries hold 70.4%** of country-attributed records; developing countries 29.6%
- **LDCs account for 2.8%**, SIDS 1.2%, LLDCs 1.2% — 47 LDCs combined have fewer records than Canada alone
- **The developed-country share declined from 74.2% (2018) to 50.9% (2026)**, driven by China and other upper-middle-income countries
- **Europe dominates** with 40.9% of records, led by the UK (COVID-19 Genomics UK consortium)
- **Africa has only 3.6%** despite having 58 classified countries
- **38.3% of records cannot be attributed to any country**, limiting utility for allocation methodology

## Methodology highlights

- **ENA `/count` endpoint** — exact counts without downloading records
- **Non-human filter:** `NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)`
- **20 collision exclusions** — prevent false country matches from token matching (e.g., "USA: New Mexico" not counted for Mexico, "South Georgia" not counted for Georgia)
- **82 non-vocab values included** — alternative names, locality names, oceans/seas, placeholders
- **9 year columns (2018–2026)** — 2026 is partial (Jan–Oct); plus pre-2018, undated, and all-time
- **21.5% of records undated** — reported separately, not silently dropped
- **Reconciliation within -1.5%** of true total (genuine multi-country overcount, including ocean/country name overlaps)

See `pipeline/output/annual_counts_methodology.md` for the complete methodology.

## License

Data is queried from public databases (ENA). Analysis code is provided for reproducibility.
