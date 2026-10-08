# INSDC Provenance Country Maps for the Cali Fund

Country-level maps of non-human digital sequence information (DSI) records with geographic provenance, constructed from the INSDC/ENA sample database to assess whether INSDC provenance data could support a country-level allocation methodology for the Cali Fund.

## Contents

- `INSDC_Provenance_Cali_Fund_Assessment.md` — Full written assessment with analysis tables
- `insdc_provenance_country_maps.csv` — Main table: 244 countries with ENA + NCBI counts and UN classifications
- `ena_per_country_counts.csv` — Raw ENA per-country counts (all, post-2023, environmental)
- `insdc_counts_all_legacy.csv` — NCBI BioSample per-country counts (all records)
- `insdc_counts_post2023.csv` — NCBI BioSample per-country counts (post-2023)
- `insdc_counts_environmental.csv` — NCBI BioSample per-country counts (environmental)
- `insdc_provenance_final_analysis.json` — Full analysis in JSON format

### Maps (interactive HTML, open in any browser)

- `map1_all_legacy_records.html` — All 26.7M non-human DSI records with country provenance (blue-white-red)
- `map2_post2023_records.html` — 6.8M post-2023 records
- `map3_environmental_records.html` — 125K environmentally sourced records
- `map4_post2023_growth_rate.html` — Post-2023 growth rate by country
- `insdc_provenance_combined_maps.html` — All three maps in one figure

### Scripts

- `query_insdc_provenance.py` — NCBI ESearch per-country count queries
- `final_analysis.py` — Combined ENA + NCBI analysis with UN classification mapping
- `make_maps.py` — Generate all choropleth maps
- `make_map1_bwr.py` — Regenerate map 1 with blue-white-red diverging scale

## Methodology

Data was queried from the ENA portal API (primary) and NCBI BioSample ESearch (cross-reference) on 8 October 2026. Non-human records were filtered using `NOT tax_tree(9606)`. Country provenance uses the INSDC controlled vocabulary for `geo_loc_name` (296 valid values). Post-2023 is defined as `first_public >= 2024-01-01`. Environmental samples use the `environmental_sample=true` boolean field.

For countries exceeding ENA's 500k-per-query cap (USA, China, UK, Germany, Denmark, Canada, Australia), counts were obtained by subdividing by year and quarter.

All country names were mapped to UN M.49 classifications for aggregation by region, sub-region, and development status.

## Key findings

- 26.7 million non-human ENA samples have country provenance across 244 countries
- Developed countries hold 71.1% of all records; the USA alone holds 29.3%
- All 47 LDCs combined hold fewer records (760K) than Denmark alone (716K)
- Post-2023 developing-country share rose to 40.7%, but this is driven almost entirely by China
- Environmental sample flags are severely under-populated (0.5% of records)
- INSDC provenance data should not be used as a direct Cali Fund allocation criterion

## License

Data is queried from public databases (ENA, NCBI). Analysis code is provided for reproducibility.
