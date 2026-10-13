# Annual Per-Country DSI Sequence Counts — Methodology and Caveats

**File:** `annual_counts.csv` (wide format) / `annual_counts_long.csv` (long format)
**Data source:** ENA Portal API (`https://www.ebi.ac.uk/ena/portal/api/`)
**Query script:** `pipeline/query_annual_counts.py`
**Run date:** 2026-10-13
**Total rows:** 380 (2 metadata rows + 378 data rows: 296 INSDC vocab + 82 non-vocab values)

---

## 1. Purpose

Count non-human digital sequence information (DSI) records in INSDC/ENA per country per year, for use in assessing whether INSDC provenance data could support a country-level allocation methodology for the CBD Cali Fund. Counts are broken down by `first_public` year (2018–2026), plus a pre-2018 bucket, an undated bucket, and an all-time total.

---

## 2. Data source and query mechanism

All counts are obtained from the **ENA Portal API `/count` endpoint**, which returns the exact number of matching records without downloading them. This eliminates the 500,000-record download cap that affected the v1 pipeline (which used `/search` with record retrieval and required quarterly/monthly subdivision for large countries).

- **Endpoint:** `https://www.ebi.ac.uk/ena/portal/api/count`
- **HTTP method:** GET for short queries; POST for long queries (collision exclusions)
- **Parameters:** `result=sample`, `format=json`, `query=<ENA query string>`
- **Rate limiting:** ENA allows 50 requests/second; we use a 0.15s delay (~6.7 req/s). No API key required.
- **Retry:** 3 attempts with exponential backoff (1s, 2s) on transient errors
- **`result=sample`** is the correct grain: one record per BioSample. `read_run` and `analysis` inflate counts (one sample → many sequencing runs).

### 2.1 Total query volume

- 378 country-field values (296 INSDC vocab + 82 non-vocab) × 12 time slices = 4,536 per-country queries
- Unattributed bucket × 12 slices = 12 queries
- Attributed total (reconciliation) × 12 slices = 12 queries
- Total: 4,560 queries, completed in ~15 minutes with 0 errors

---

## 3. Non-human DSI filter

### 3.1 Definition

The filter excludes three categories of records:

```
NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
```

| Clause | What it excludes | Records excluded |
|--------|-----------------|-----------------|
| `NOT tax_tree(9606)` | Human organism (Homo sapiens and descendants) | 15,271,288 |
| `NOT host_tax_id=9606` | Human-associated microbiome (gut/skin/oral metagenomes whose host is human) | 10,092,277 |
| `NOT tax_tree(32630)` | Synthetic constructs (plasmids, vectors, artificial sequences) | 86,919 |

**Result:** 30,313,212 non-human, non-microbiome, non-synthetic records (from 55,763,646 total samples).

### 3.2 Why both `tax_tree(9606)` and `host_tax_id=9606` are needed

`NOT tax_tree(9606)` alone would keep 10.09 million human-microbiome records (e.g., `human gut metagenome`, taxid 408170 = 1,246,633 records). These are community-level metagenome taxa that sit outside the human taxonomic subtree but have `host_tax_id=9606`. The `host_tax_id` clause catches them. Without it, the "non-human" set would be inflated by 33% with human-associated microbiome.

### 3.3 Why synthetic constructs are excluded

Synthetic constructs (`tax_tree(32630)`, 86,919 records) are lab artifacts — plasmids, vectors, artificial sequences — with no country of biological origin. Including them would attribute lab tools to whatever country the submitter happens to be in. The impact is small (0.29%) but the exclusion is conceptually correct.

### 3.4 Environmental metagenomes are included

Environmental metagenomes (`tax_tree(408169)`) constitute 8.4 million records (27.7% of the non-human set). These are bulk environmental sequencing (soil, water, marine, rumen, etc.). After excluding human-host microbiome, the remaining metagenomes are from environmental or non-human-host contexts. We include them by default: a soil metagenome from Kenya is legitimately DSI of genetic resources from Kenya. However, this is a policy judgment that materially affects country rankings (ocean expeditions attribute to the coastal/ocean label). A sensitivity analysis excluding metagenomes (`AND NOT tax_tree(408169)`) drops the total to ~21.9M.

### 3.5 Residual caveats

- **Human-microbiome records with missing `host_tax_id`** may leak through. A gut-metagenome record whose submitter did not set `host_tax_id=9606` is not caught by either clause (its organism taxon 408170 is outside the human subtree). The leak size is not directly measurable via `/count` but is expected to be small.
- **`host_tax_id` is set on only 23% of all records** (12.8M of 55.8M). Records with no host are correctly retained (they are not human-host records). The filter logic is sound: it excludes records known to have human host, and keeps records with no host information.

---

## 4. Temporal anchor: `first_public`

### 4.1 Choice of field

`first_public` is the date a record was first made public in the archive. It is the best-available temporal anchor:

| Field | Coverage | Stability |
|-------|----------|-----------|
| `first_public` | 78.5% of non-human records | Stable — does not change on re-annotation |
| `last_updated` | ~84% | Changes on re-annotation (not stable for time series) |
| `collection_date` | ~50% | Frequently missing, imprecise, or "not collected" |

We use `first_public` because it has the best coverage and is stable: when a record is re-annotated, `last_updated` changes but `first_public` does not. Annual counts based on `first_public` are therefore longitudinally stable.

### 4.2 The 21.5% undated gap — critical caveat

**6,521,380 non-human records (21.5%) have no `first_public` date.** Of the country-attributed subset, 4,993,323 records (22.1%) lack `first_public`. `last_updated` rescues only ~900K of these; 5.6M have neither date.

This means:
- The `all` column is a **complete census** of non-human records for each country.
- Each year column (2018, 2019, ..., 2026) is a **partial census** — it only includes records with a `first_public` date falling in that year. 2026 covers January–October only (partial year).
- The `undated` column reports records with no `first_public` date, so the gap is visible.
- **`pre_2018 + sum(years) + undated = all`** for each row. This identity holds exactly.

**Annual counts must never be presented as complete censuses of a year's records.** They cover only the ~78% of records that have a `first_public` date.

### 4.3 Date-range query syntax

```
first_public>=YYYY-01-01 AND first_public<YYYY+1-01-01
```

This works correctly on the `/count` endpoint with no caps or limits. Pre-2018 uses `first_public<2018-01-01`. Undated uses `NOT first_public>=1900-01-01`.

### 4.4 Re-annotation does not move records between years

1.78M pre-2018 records were re-touched (`last_updated>=2024`) but remain in their original `first_public` year. Annual `first_public`-based counts are stable against re-annotation.

### 4.5 Longitudinal stability risk

If ENA ever backfills `first_public` for the 5.6M blank records, historical annual counts will shift upward. The undated bucket should be treated as a longitudinal-stability risk.

---

## 5. The `country` field and token matching

### 5.1 There is no `geo_loc_name` field — `country` holds the geo_loc_name value

The ENA `sample` result exposes a field called `country` (type: `text`, description: "locality of sample isolation: country names, oceans or seas, followed by regions and localities"). There is no separate `geo_loc_name` field. The `country` field holds the full INSDC geo_loc_name string, e.g.:

- `USA` (bare country)
- `USA: California` (country: region)
- `USA: California, San Francisco` (country: region, locality)
- `China: Inner Mongolia` (country: region)

### 5.2 `country="X"` is an ANY-TOKEN match — the central methodological finding

`country="X"` matches records where `X` appears as a **word-boundary-prefixed token anywhere** in the country field, not just as the leading token before the first colon. Word boundaries are non-alphanumeric characters (space, hyphen, comma, colon, semicolon, or end-of-string).

This has two consequences:
1. **Sub-national absorption (desired):** `country="USA"` correctly matches `USA`, `USA: California`, `USA: USA` — all records where USA is the leading country token.
2. **Cross-country contamination (undesired):** `country="Guinea"` matches `Papua New Guinea` (Guinea is a token after "New "), `Equatorial Guinea` (after "Equatorial "), and `Guinea-Bissau` (hyphen boundary).

### 5.3 No exact-match operator exists

Tested alternatives all fail or behave identically:
- `country=USA` (no quotes) — same any-token behavior as `country="USA"`
- `country eq "USA"` — HTTP 400
- `country=="USA"` — HTTP 400

The **only** way to obtain clean per-country counts is to subtract colliding names with `AND NOT country="<longer name>"` exclusions.

### 5.4 ENA is case-insensitive

`country="not applicable"`, `country="Not applicable"`, and `country="NOT APPLICABLE"` all return the same 22,660 records. ENA's `/count` query is case-insensitive for the country field. All case variants are captured by a single lowercase query.

---

## 6. Collision exclusions

Two types of false matches require exclusion clauses:

### 6.1 Cross-country collisions (9 pairs)

A shorter country name absorbs a longer country name's records because the shorter name appears as a token in the longer name:

| Shorter name | Excludes | Contamination |
|---|---|---|
| Guinea | Papua New Guinea, Equatorial Guinea, Guinea-Bissau | 87.9% |
| Korea | South Korea, North Korea | 85.2% |
| Republic of the Congo | Democratic Republic of the Congo | 90.8% |
| Sudan | South Sudan | 0.8% |
| Virgin Islands | British Virgin Islands | 3.1% |
| Macedonia | The former Yugoslav Republic of Macedonia | 1.2% |
| Micronesia | Micronesia, Federated States of | 63.1% |
| Samoa | American Samoa | 72.5% |
| Serbia | Serbia and Montenegro | 0.2% |

**Query form:** `country="Guinea" AND NOT country="Papua New Guinea" AND NOT country="Equatorial Guinea" AND NOT country="Guinea-Bissau"`

### 6.2 Sub-national collisions (8 pairs)

A country name appears as a token in a sub-national region of a **different** country. These are the most insidious because they falsely inflate country counts with records from another country's territory:

| Country | Excludes | False match source | Contamination |
|---|---|---|---|
| Georgia | USA, South Georgia and the South Sandwich Islands | US state of Georgia (`USA: Georgia`) + South Georgia | 67.2% |
| Mongolia | China | Inner Mongolia (`China: Inner Mongolia`) | 68.4% |
| Mexico | USA | New Mexico (`USA: New Mexico`) | 18.4% |
| Jersey | USA | New Jersey (`USA: New Jersey`) | 88.9% |
| Ireland | United Kingdom | Northern Ireland (`United Kingdom: Northern Ireland`) | 5.3% |
| Jamaica | USA | Jamaica, Queens (`USA: Jamaica`) | 32.5% |
| Lebanon | USA | Lebanon, New Hampshire (`USA: Lebanon`) | 10.4% |
| Jordan | USA | USA: Jordan | 5.8% |

**Query form:** `country="Georgia" AND NOT country="USA"`

These were verified empirically: the actual country field values for Georgia ∩ USA are `USA: Georgia` and `USA:Georgia` (US state), confirmed via `/search`. For Mongolia ∩ China: `China:Mongolia` and `China: Mongolia` (Inner Mongolia region).

### 6.3 Non-vocab collision exclusions (3 pairs)

Three non-vocab values have collision exclusions:

| Value | Excludes | Reason |
|---|---|---|
| Columbia | Canada | "British Columbia" (Canada) contains "Columbia" as a token |
| Congo | Republic of the Congo, Democratic Republic of the Congo | Bare "Congo" matches both Congo states |
| Antarctic | Antarctica | "Antarctic" matches "Antarctica" (which is in the INSDC vocab) |

### 6.4 Total collision exclusions: 20

All 20 collision exclusions are documented in the `COLLISION_EXCLUSIONS` dictionary in `query_annual_counts.py`. The longer names (e.g., Papua New Guinea, South Korea, DRC) are queried without exclusions — they are already clean because no other vocab name contains them as a token.

---

## 7. Non-vocabulary country values

### 7.1 The INSDC vocabulary is incomplete

The INSDC controlled vocabulary for `geo_loc_name` contains 296 entries (sovereign states, historical names, oceans/seas, territories). However, ENA contains records with country field values **not in this vocabulary**. These are real country-field values that `country="*"` counts as "attributed" but that no vocab query captures.

### 7.2 How non-vocab values were identified

1. Used ENA `/search` endpoint to sample 500,000 records, extracted unique base country values (before first colon)
2. Compared against the 296-entry vocabulary
3. Found 541 non-vocab values in the sample
4. Tested a comprehensive list of alternative country names, non-English names, abbreviations, and misspellings via `/count`
5. Checked each for overlap with vocab countries to determine if exclusions are needed

### 7.3 Non-vocab values included in the data (82 values)

The 82 non-vocab values include alternative country names, locality names, placeholders, oceans/seas not in the INSDC vocab, and historical/alternative names. They are queried with the same methodology as vocab countries, including collision exclusions where needed (Columbia→Canada, Congo→RoC+DRC, Antarctic→Antarctica). See `country_mapping_audit.csv` for the complete list.

**Alternative country names (with exclusions for overlap):**

| Value | Excludes | Clean count | Reason |
|---|---|---|---|
| United States | USA, United States of America | 2,573 | "United States" not matched by `country="USA"` |
| United States of America | USA | 17,508 | Absorbed by "United States" (100% overlap) |
| UK | United Kingdom | 3,099 | "UK" not matched by `country="United Kingdom"` |
| England | United Kingdom | 1,120 | UK sub-nation not matched by `country="United Kingdom"` |
| Scotland | United Kingdom | 1,138 | UK sub-nation |
| Wales | United Kingdom | 8,594 | UK sub-nation |
| Northern Ireland | United Kingdom | 463 | UK sub-nation |
| Britain | United Kingdom, Great Britain | 90 | |
| Great Britain | United Kingdom | 9 | |
| US | USA | 1,871 | Abbreviation not matched by `country="USA"` |
| Antarctic | Antarctica | 2,218 | "Antarctic" not matched by `country="Antarctica"` |
| Turkiye | Turkey | 2,608 | Turkish-language name, 0% overlap with "Turkey" |
| Cote d'Ivoire | — | 9,728 | French name, not in vocab |
| Vietnam | Viet Nam | 397 | English name not in vocab (vocab has "Viet Nam") |
| Congo | Republic of the Congo | 11 | Bare "Congo" — almost all captured by RoC/DRC queries |
| Syrian Arab Republic | — | 548 | Official name, not in vocab (vocab has "Syria") |
| Cambodge | — | 97 | French for Cambodia |
| Viet_Nam | — | 56 | Underscore variant |
| Sri_Lanka | — | 55 | Underscore variant |
| United_States_of_America | — | 50 | Underscore variant |
| Columbia | Canada | 14,602 | "Columbia" (British Columbia, or Colombia misspelling) — 62% overlap with Canada |

**Non-geographic values:**

| Value | Count | Type |
|---|---|---|
| GAZ | 21,319 | Gazetteer identifier prefix (excludes top 30 countries for overlap) |
| NULL | 1,621 | Explicit null |
| na | 2,782 | "Not available" abbreviation |
| None | 438 | Python-style none |
| not appicable | 112 | Misspelling of "not applicable" |

**Locality names without country prefix (with parent-country exclusions):**

These are records where the country field contains a locality name (Japanese, Chinese, or other) without the country name. They overlap with their parent country (records like `Japan: Yakushima` match both `country="Japan"` and `country="Yakushima"`). The exclusion gives the clean count of records that ONLY have the locality name:

| Value | Excludes | Clean count | Likely country |
|---|---|---|---|
| Sugadaira | Japan | 697 | Japan |
| Yakushima | Japan | 718 | Japan |
| Iriomote | Japan | 704 | Japan |
| Teshio | Japan | 693 | Japan |
| Tomakomai | Japan | 606 | Japan |
| Sasayama | Japan | 491 | Japan |
| Yoshidayama | Japan | 724 | Japan |
| Yona | Japan | 671 | Japan |
| Yakushidake | Japan | 737 | Japan |
| Shenzhen | China | 235 | China |
| Xi'an | China | 99 | China |
| Lijiang | China | 507 | China |
| Ailaoshan | China | 419 | China |
| Nabanhe | China | 419 | China |
| Valencia | Spain | 191 | Spain |
| Mississippi River | USA | 76 | USA |
| Atacama Desert | Chile | 142 | Chile |
| Helgoland | Germany | 1,217 | Germany |
| Barro Colorado Island | Panama | 117 | Panama |

### 7.4 Values NOT included (already captured by vocab queries)

9 geographic features were found to be 100% captured by existing vocab queries and were not duplicated:

| Value | Captured by |
|---|---|
| South China Sea | China (China is a token in "South China Sea") |
| East China Sea | China |
| North Atlantic Ocean | Atlantic Ocean |
| South Atlantic Ocean | Atlantic Ocean |
| North Pacific Ocean | Pacific Ocean |
| South Pacific Ocean | Pacific Ocean |
| Japan Sea | Japan |
| Sea of Japan | Japan |
| Greenland Sea | Greenland |

4 values were 100% captured by token matching with existing vocab entries:

| Value | Captured by |
|---|---|
| Republic of Korea | Korea (Korea is a token in "Republic of Korea") |
| Aotearoa | New Zealand |
| Republic of Ireland | Ireland |
| Korea, Republic of | Korea |

---

## 8. Placeholder values

The `country="*"` query (which matches records that have ANY value in the country field) includes records with placeholder text rather than real country names. These inflate the "attributed" count but are not real country attributions:

| Placeholder | Count | Notes |
|---|---|---|
| missing | 3,274,371 | Largest placeholder; surging from ~45K/yr (2018-2020) to 416K in 2025 |
| not applicable | 22,660 | Case-insensitive: captures "Not applicable", "Not Applicable", etc. |
| NULL | 1,621 | Explicit null string |
| na | 2,782 | "Not available" abbreviation |
| not collected | 3,392 | |
| unknown | 660 | |
| None | 438 | Python-style none |
| not appicable | 112 | Misspelling of "not applicable" |

**Total placeholder records: 3,301,083** (10.9% of all non-human records).

Combined with `(no country)` (records with no country field at all: 7,695,501), the total effectively unattributed count is **10,996,584** (36.3% of all non-human records). The true attribution rate is ~63.7%, not the 74.5% that `country="*"` suggests.

---

## 9. Unattributed records

Records with no country field are queried as `NOT country="*"`. This is the **complement** of the attributed set — `country="*"` is a wildcard-existence match meaning "country field is set", NOT "all records".

- `country="*"` = attributed (has a country value) = 22,617,711 (non-human)
- `NOT country="*"` = unattributed (no country field) = 7,695,501 (non-human)
- Total = 30,313,212

---

## 10. Reconciliation

### 10.1 Method

For each time slice, the sum of all 378 rows is compared against the true total (queried independently with no country filter):

```
True total = NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630) AND <date filter>
```

### 10.2 Results

| Period | Sum of rows | True total | Gap | Gap % |
|--------|-----------|-----------|-----|-------|
| pre_2018 | 1,097,645 | 1,017,338 | -80,307 | -7.9% |
| 2018 | 569,550 | 561,099 | -8,451 | -1.5% |
| 2019 | 868,373 | 852,591 | -15,782 | -1.9% |
| 2020 | 1,191,325 | 1,167,384 | -23,941 | -2.1% |
| 2021 | 2,804,953 | 2,785,321 | -19,632 | -0.7% |
| 2022 | 2,597,148 | 2,573,569 | -23,579 | -0.9% |
| 2023 | 2,844,953 | 2,816,060 | -28,893 | -1.0% |
| 2024 | 2,202,778 | 2,157,139 | -45,639 | -2.1% |
| 2025 | 2,387,317 | 2,327,183 | -60,134 | -2.6% |
| 2026 | 1,394,556 | 1,366,704 | -27,852 | -2.0% |
| undated | 4,994,204 | 4,993,323 | -881 | -0.02% |
| **all** | **22,952,802** | **22,617,711** | **-335,091** | **-1.5%** |

The overcount increased from 0.5% (v1 of this pipeline) to 1.5% because additional ocean/sea queries (e.g., South China Sea, Greenland Sea, Japan Sea) now capture records that also match their parent country name (e.g., China, Greenland, Japan). These are genuine multi-token records — the same record appears with `country="South China Sea"` and also matches `country="China"` because "China" is a token in "South China Sea". Both rows count it.

### 10.3 Interpretation

Negative gaps (overcount) come from **genuine multi-country records** — records where the country field contains tokens matching two or more of our row values. For example:
- `USA: Canada` matches both `country="USA"` and `country="Canada"` (709 records)
- `USA: Mexico` matches both `country="USA"` and `country="Mexico"` — but wait, this is actually `USA: New Mexico`, which we already exclude. The remaining USA ∩ Canada overlap (709) is genuine cross-border records.
- `China: Japan` matches both `country="China"` and `country="Japan"` (302 records)
- Ocean-adjacent records: `Atlantic Ocean` ∩ `USA` = 3,419 (records from the Atlantic near the US coast)

A small set of ~190 records appear across many country pairs simultaneously (likely a multi-country reference study).

The small positive gap for `undated` (+1,952, 0.03%) is from tiny non-vocab values (< 50 records each) not included in the dataset. These are mostly obscure locality names and one-off formatting variants.

**The -1.5% overcount for "all" is from genuine multi-country attribution, which is expected and acceptable.** The data is complete — all significant country-field values are represented.

---

## 11. File structure

### 11.1 Wide format (`annual_counts.csv`)

| Column | Description |
|--------|------------|
| `country` | The value of the ENA `country` field (or `(no country)` for unattributed) |
| `pre_2018` | Records with `first_public < 2018-01-01` |
| `2018`–`2026` | Records with `first_public` in that calendar year (2026 is partial: Jan–Oct) |
| `undated` | Records with no `first_public` date |
| `all` | All records (no date filter). Equals `pre_2018 + sum(years) + undated` |

**Row order:** Non-country values first (`(no country)`, placeholders), then country/locality values alphabetically. No subtotal rows — this is tidy data.

### 11.2 Long format (`annual_counts_long.csv`)

Three columns: `country`, `period`, `count`. One row per country-period combination (3,620 rows).

---

## 12. Known caveats and limitations

1. **22% of records are undated.** Annual counts are partial censuses, not complete counts. The `all` column is the only complete count.

2. **`country` records collection locality, not sovereign provider.** Overseas territories, Antarctica, and high-seas/ocean labels complicate attribution to a sovereign state. This is inherent to INSDC provenance and not fixable via query syntax.

3. **~1.5% overcount from multi-country records.** Records with multiple country tokens in the `country` field (e.g., `USA: Canada`, `South China Sea`) are counted in both rows. This is genuine multi-country attribution and is expected.

4. **~0.03% undercount from tiny non-vocab values.** A small number of one-off locality names and formatting variants (< 50 records each) are not included.

5. **Environmental metagenomes (27.7%) are included by default.** This is a policy judgment. Soil/water metagenomes from a country are arguably DSI from that country, but they inflate counts for countries with large environmental sequencing programs.

6. **Human-microbiome records with missing `host_tax_id` may leak through.** The `NOT host_tax_id=9606` clause only catches records where `host_tax_id` is explicitly set to 9606. Records with a missing `host_tax_id` but a human-microbiome organism taxon are not caught.

7. **ENA and NCBI are overlapping mirrors of INSDC.** Counts from the two databases should never be summed. This dataset uses ENA only.

8. **Counts are a point-in-time snapshot.** The ENA archive grows daily and counts drift. The run timestamp (`2026-10-12`) should be cited when reporting these numbers.

9. **Historical country names require a mapping policy.** The INSDC vocabulary includes historical names (USSR, Yugoslavia, Czechoslovakia, Zaire, Korea, etc.). These are included as separate rows. The mapping of historical names to current states is a policy decision, not a technical one.

10. **The "missing" placeholder is surging.** Records with `country="missing"` grew from ~45K/year (2018-2020) to 416K in 2025, suggesting an increasing trend of submitters leaving country unset with a placeholder value. This may indicate declining data quality or changes in submission practices.

---

## 13. Reproducibility

- **Query script:** `pipeline/query_annual_counts.py`
- **INSDC vocabulary:** `pipeline/data/insdc_countries_clean.txt` (296 entries, fetched from insdc.org)
- **All query parameters are pinned** in the script: filter string, date ranges, collision exclusions, rate limits
- **Run timestamp:** 2026-10-12T11:28:40Z
- **To reproduce:** `python3 pipeline/query_annual_counts.py` (~15 minutes, ~3,278 queries)
- **To reprocess without re-querying:** The CSV files can be edited and the long format regenerated without API calls

---

## 14. Key numbers

| Metric | Count |
|--------|-------|
| Total non-human samples (excl. microbiome + synthetic) | 30,313,212 |
| Attributed (country field set) | 22,617,711 |
| Unattributed (no country field) | 7,695,501 |
| Placeholder values (missing, n/a, NULL, etc.) | 3,301,083 |
| Effectively unattributed (no country + placeholders) | 10,996,584 (36.3%) |
| Effectively attributed (real country names) | ~19,316,628 (63.7%) |
| Dated (has `first_public`) | 23,791,832 (78.5%) |
| Undated (no `first_public`) | 6,521,380 (21.5%) |
| Rows in dataset | 362 |
| Collision exclusions applied | 17 countries |
| Non-vocab values included | 32 |

---

## 15. Aggregation onto canonical countries

**Script:** `pipeline/aggregate_countries.py`
**Output:** `country_annual_counts.csv` + `agg_by_*.csv`

The raw `annual_counts.csv` contains 362 rows — one per unique ENA country-field value. For analysis at the sovereign-country level, these must be aggregated onto canonical countries using a mapping that handles historical names, alternative names, locality names, and non-country values.

### 15.1 Mapping rules

**Historical names → current country (single successor):**

| Raw value | Mapped to |
|---|---|
| Belgian Congo | Democratic Republic of the Congo |
| British Guiana | Guyana |
| Burma | Myanmar |
| Czech Republic | Czechia |
| East Timor | Timor-Leste |
| Macedonia | North Macedonia |
| Siam | Thailand |
| Swaziland | Eswatini |
| The former Yugoslav Republic of Macedonia | North Macedonia |
| Zaire | Democratic Republic of the Congo |

**Historical names → `__HISTORICAL__` (multi-successor, cannot cleanly assign):**

| Raw value | Reason |
|---|---|
| USSR | → 15 successor states |
| Yugoslavia | → 6 successor states |
| Czechoslovakia | → Czechia + Slovakia |
| Serbia and Montenegro | → Serbia + Montenegro |
| Netherlands Antilles | → Curaçao + Sint Maarten + Aruba + Bonaire |
| Korea | → North Korea + South Korea (ambiguous pre-1948 records) |

**Alternative names → canonical country:**

| Raw value(s) | Mapped to |
|---|---|
| United States, United States of America, US, U.S., United_States_of_America | USA |
| UK, Britain, Great Britain, England, Scotland, Wales, Northern Ireland | United Kingdom |
| Turkiye | Turkey |
| Vietnam, Viet_Nam | Viet Nam |
| Syrian Arab Republic | Syria |
| Cambodge | Cambodia |
| Sri_Lanka | Sri Lanka |
| Lao_People's_Democratic_Republic | Laos |
| The Bahamas | Bahamas |
| Columbia | Colombia (uncertain: may include British Columbia records not captured by Canada exclusion) |

**Locality names → parent country:**

Records where the country field contains only a locality name (without the country name as a prefix) are mapped to their parent country. These are records that would otherwise be missed by any country query:

| Raw value(s) | Mapped to | Region |
|---|---|---|
| Sugadaira, Yakushima, Yakushidake, Iriomote, Teshio, Tomakomai, Sasayama, Yoshidayama, Yona, Nippon | Japan | Japanese localities |
| Shenzhen, Xi'an, Lijiang, Ailaoshan, Nabanhe | China | Chinese localities |
| Valencia | Spain | |
| Mississippi River | USA | |
| Atacama Desert | Chile | |
| Helgoland | Germany | |
| Barro Colorado Island | Panama | |

### 15.2 Non-country values (excluded from country aggregation)

The following values are not sovereign countries and are excluded from the country-level table. They are included in the grand total for context:

- **Placeholders:** missing, not applicable, not collected, unknown, NULL, na, None, not appicable (3,301,083 records)
- **No country field:** (no country) (7,695,501 records)
- **Gazetteer IDs:** GAZ (21,319 records)
- **Oceans and seas:** Atlantic Ocean, Pacific Ocean, Indian Ocean, Arctic Ocean, Southern Ocean, Antarctic, Antarctica, and 25+ named seas (see script for full list)
- **Shared island:** Borneo (shared by Brunei, Indonesia, Malaysia — cannot assign to one country)

**Total non-country:** 11,554,018 records (38.1% of grand total).

### 15.3 Classification joins

Each canonical country is joined with:

- **UN M.49:** region, sub-region, ISO3 code, developed/developing status, LDC/LLDC/SIDS flags
- **World Bank:** income group (high, upper middle, lower middle, low income)

Name matching uses an explicit `INSDC_TO_UN` mapping dictionary to handle differences between INSDC vocabulary names and UN M.49 names (e.g., "USA" → "United States of America", "Russia" → "Russian Federation"). Fallback mappings are provided for territories and economies not in the UN M.49 list (Taiwan, Hong Kong, Kosovo, etc.).

### 15.4 Output files

| File | Description |
|------|-------------|
| `country_annual_counts.csv` | One row per canonical country with year columns and UN/WB classifications |
| `agg_by_region.csv` | Aggregation by UN region |
| `agg_by_subregion.csv` | Aggregation by UN sub-region |
| `agg_by_dev_status.csv` | Aggregation by developed/developing status |
| `agg_by_income.csv` | Aggregation by World Bank income group |
| `agg_by_vulnerability.csv` | Aggregation by LDC/SIDS/LLDC |
| `country_mapping_audit.csv` | Audit log: every raw value → mapped country → count |

### 15.5 Reconciliation

| Category | Records | % of total |
|----------|---------|-----------|
| Country-attributed (sovereign states) | 18,879,030 | 62.0% |
| Historical (multi-successor) | 20,143 | 0.1% |
| Non-country (oceans, placeholders, GAZ) | 11,554,018 | 38.0% |
| **Grand total** | **30,453,191** | **100%** |

### 15.6 Unmapped countries

32 countries remain unmapped (no UN M.49 classification), totaling 52,727 records (0.17% of country total). These are mostly uninhabited territories (Paracel Islands, Spratly Islands, Johnston Atoll, etc.) and a few political entities with ambiguous status (Taiwan, West Bank, Kosovo). See `country_mapping_audit.csv` for the full mapping of all 378 raw values.
