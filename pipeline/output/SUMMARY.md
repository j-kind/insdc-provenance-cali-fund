# INSDC Provenance Country-Level Maps for the Cali Fund — v2

**Run timestamp:** 2026-10-12T11:03:14Z
**Data source:** ENA portal API `/count` endpoint (primary); NCBI ESearch `[country]` (cross-check)
**Filter:** `NOT tax_tree(9606) AND NOT host_tax_id=9606` (excludes human organism and human-associated microbiome)
**Temporal anchor:** `first_public` (date record was made public in the archive)
**INSDC vocabulary:** 296 entries from controlled vocabulary for `geo_loc_name`

---

## Grand totals

| Metric | Count | % of total |
|--------|-------|------------|
| Total non-human samples (excl. human microbiome) | 30,400,131 | 100% |
| With country provenance | 22,641,119 | 74.5% |
| Unattributed (no country) | 7,759,012 | 25.5% |
| Post-2023 with country | 5,854,571 | |
| Countries with >= 1 record | 247 | |

## By development status

| Status | Countries | All records | % share | Post-2023 | 2018-2020 | 2021-2023 | 2024+ |
|--------|-----------|-------------|---------|-----------|-----------|-----------|-------|
| Developed | 63 | 13,248,159 | 58.5% | 2,559,210 | 1,710,489 | 5,932,295 | 2,559,179 |
| Developing | 175 | 5,734,991 | 25.3% | 2,196,496 | 703,547 | 1,705,805 | 2,196,496 |
| Unmapped | 9 | 636,235 | 2.8% | 167,248 | 72,955 | 194,618 | 167,248 |

## By World Bank income group

| Income group | Countries | All records | % share | Post-2023 | 2018-2020 | 2021-2023 | 2024+ |
|--------------|-----------|-------------|---------|-----------|-----------|-----------|-------|
| High income | 82 | 13,724,933 | 60.6% | 2,740,607 | 1,771,491 | 6,072,917 | 2,740,607 |
| Upper middle income | 53 | 4,210,114 | 18.6% | 1,808,321 | 544,800 | 1,262,457 | 1,808,321 |
| Lower middle income | 50 | 715,119 | 3.2% | 144,738 | 66,527 | 227,164 | 144,738 |
| Low income | 26 | 260,808 | 1.2% | 38,470 | 19,580 | 54,507 | 38,470 |
| Unknown | 36 | 708,411 | 3.1% | 190,818 | 84,593 | 215,673 | 190,787 |

## By vulnerable country group

| Group | Countries | All records | % share | Post-2023 | 2018-2020 | 2021-2023 | 2024+ |
|-------|-----------|-------------|---------|-----------|-----------|-----------|-------|
| LDC | 47 | 548,895 | 2.4% | 68,909 | 34,470 | 178,475 | 68,909 |
| SIDS | 52 | 226,752 | 1.0% | 64,147 | 29,976 | 76,571 | 64,147 |
| LLDC | 32 | 267,354 | 1.2% | 60,072 | 25,675 | 68,632 | 60,072 |

## Growth rates (annualized, period vs previous period)

| Group | 2018-2020/yr | 2021-2023/yr | Growth | 2024+/yr | Growth |
|-------|-------------|-------------|--------|---------|--------|
| Developed | 570,163 | 1,977,432 | +247% | 920,568 | -53% |
| Developing | 234,516 | 568,602 | +142% | 790,106 | +39% |
| Unmapped | 24,318 | 64,873 | +167% | 60,161 | -7% |
| High income | 590,497 | 2,024,306 | +243% | 985,830 | -51% |
| Upper middle income | 181,600 | 420,819 | +132% | 650,475 | +55% |
| Lower middle income | 22,176 | 75,721 | +241% | 52,064 | -31% |
| Low income | 6,527 | 18,169 | +178% | 13,838 | -24% |
| Unknown | 28,198 | 71,891 | +155% | 68,628 | -5% |
| LDC | 11,490 | 59,492 | +418% | 24,787 | -58% |
| SIDS | 9,992 | 25,524 | +155% | 23,074 | -10% |
| LLDC | 8,558 | 22,877 | +167% | 21,609 | -6% |

## Top 20 countries by all records

| # | Country | ISO3 | Status | Income | All | Post-2023 | % share |
|---|---------|------|--------|--------|-----|-----------|---------|
| 1 | United Kingdom of Great Britain and Northern Ireland | GBR | Developed | High income | 4,099,520 | 102,793 | 18.1% |
| 2 | United States of America | USA | Developed | High income | 3,965,097 | 1,227,846 | 17.5% |
| 3 | China | CHN | Developing | Upper middle income | 3,331,953 | 1,517,658 | 14.7% |
| 4 | Canada | CAN | Developed | High income | 536,918 | 186,138 | 2.4% |
| 5 | Germany | DEU | Developed | High income | 509,371 | 95,030 | 2.2% |
| 6 | __OCEANS_SEAS__ | --- | ? | Unknown | 456,637 | 98,847 | 2.0% |
| 7 | Australia | AUS | Developed | High income | 424,486 | 111,446 | 1.9% |
| 8 | Denmark | DNK | Developed | High income | 403,790 | 51,107 | 1.8% |
| 9 | France | FRA | Developed | High income | 388,177 | 71,715 | 1.7% |
| 10 | Japan | JPN | Developed | High income | 364,752 | 148,825 | 1.6% |
| 11 | Spain | ESP | Developed | High income | 326,735 | 62,175 | 1.4% |
| 12 | Finland | FIN | Developed | High income | 244,247 | 20,876 | 1.1% |
| 13 | Republic of Korea | KOR | Developing | High income | 232,164 | 106,451 | 1.0% |
| 14 | Italy | ITA | Developed | High income | 216,400 | 51,645 | 1.0% |
| 15 | Sweden | SWE | Developed | High income | 213,811 | 36,582 | 0.9% |
| 16 | Netherlands | NLD | Developed | High income | 201,107 | 32,009 | 0.9% |
| 17 | Switzerland | CHE | Developed | High income | 184,423 | 45,530 | 0.8% |
| 18 | India | IND | Developing | Lower middle income | 139,863 | 50,228 | 0.6% |
| 19 | Brazil | BRA | Developing | Upper middle income | 138,824 | 45,963 | 0.6% |
| 20 | United Republic of Tanzania | TZA | Developing | Lower middle income | 121,972 | 6,069 | 0.5% |

*2024+ annualized based on ~2.78 years (Jan 2024 to present). 2018-2020 and 2021-2023 are exactly 3 years each.*

---

## Methodology

- **Primary source:** ENA portal API `/count` endpoint — returns exact counts without downloading records
- **Cross-check:** NCBI ESearch with `[country]` field tag (token-indexed, absorbs sub-national values like "USA: California")
- **Non-human filter:** `NOT tax_tree(9606) AND NOT host_tax_id=9606` — excludes both human organism records and human-associated microbiome (gut/skin/oral metagenomes with host_tax_id=9606)
- **Country matching:** ENA `country="X"` (exact base-country match, includes sub-national variants); NCBI `X[country]` (token match)
- **Temporal anchor:** `first_public` (archive deposition date, reliably populated for all records)
- **Historical country names:** Single-successor names mapped to current state (e.g., Zaire→DRC); multi-successor names (USSR, Yugoslavia) assigned to `__HISTORICAL__` bucket
- **Unattributed records:** Reported separately; not included in country-level percentages
- **ENA and NCBI are overlapping mirrors of INSDC** — counts are never summed; NCBI serves as coverage cross-check only

## Key improvements over v1

1. Uses ENA `/count` endpoint (eliminates 500k download cap and quarterly/monthly subdivision)
2. Uses NCBI `[country]` field tag (absorbs sub-national records, vs `[all]` exact match that missed 61%)
3. Excludes human-associated microbiome (`NOT host_tax_id=9606`) — v1 included gut/skin/oral metagenomes
4. Reports unattributed bucket separately (8M+ records with no country)
5. Historical country names with documented mapping policy
6. Reproducible: pinned queries, timestamps, vocabulary versions

## Output files

| File | Description |
|------|-------------|
| `country_master.csv` | Country mapping table (INSDC → UN → WB income) |
| `ena_counts.csv` | Raw ENA per-country counts by period |
| `ncbi_crosscheck.csv` | NCBI cross-check counts |
| `country_provenance_counts.csv` | Main table: per-country counts with classifications |
| `agg_by_region.csv` | Aggregation by UN region |
| `agg_by_dev_status.csv` | Aggregation by development status |
| `agg_by_income.csv` | Aggregation by World Bank income group |
| `agg_by_vulnerability.csv` | Aggregation by LDC/SIDS/LLDC |
| `analysis_results.json` | Full analysis in JSON |
| `map_all_records.html` | Choropleth map (blue-white-red) |
| `SUMMARY.md` | This summary |
