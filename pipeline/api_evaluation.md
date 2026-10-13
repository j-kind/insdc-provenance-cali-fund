# API Approach Evaluation for INSDC Provenance Analysis (v2)

**Prepared for:** Cali Fund allocation methodology — country-level DSI sequence-record provenance
**Scope:** Evaluate ENA Portal API and NCBI ESearch/E-utilities before querying. No code or live queries executed.
**Date of research:** October 2026 (current API documentation as retrieved)

---

## Executive summary

The v1 approach rests on two assumptions that the current documentation shows to be **false or fixable**:

1. **"ENA has no count endpoint"** — Incorrect. The ENA Portal API exposes a dedicated `/count` endpoint (GET and POST) that returns the number of rows matching a query *without downloading any records*. v1's entire quarterly/monthly subdivision machinery (built to work around a 500k download cap) is unnecessary for obtaining counts.
2. **"NCBI `country="X"[all]` is the only matching mode"** — A red herring. The correct NCBI construct is the `[country]` field tag, which is a token-indexed field that matches sub-national values such as `USA: California`. v1's 39% coverage is an artifact of using `[all]` exact-phrase matching, not an inherent limitation of NCBI.

Additionally, the v1 design treats ENA and NCBI as **independent data sources to be summed/cross-referenced**. They are not independent: ENA, NCBI (GenBank), and DDBJ are the three partners of INSDC and **exchange and mirror each other's records**. ENA and NCBI therefore measure overlapping subsets of the *same* archive. Their counts must never be summed, and the cross-reference should be interpreted as a coverage/indexing sanity check, not an independent replicate.

The recommended v2 architecture uses **ENA `/count` as the primary counting engine** (cheap, exact-vocabulary, taxonomy-filterable), **NCBI ESearch `rettype=count` with `[country]` as a coverage cross-check**, downloads a minimal field set only for attribution validation, and pins every input vocabulary and query string for reproducibility.

---

## 1. ENA Portal API — findings

Source: ENA Portal API Swagger/OpenAPI spec at `https://www.ebi.ac.uk/ena/portal/api/` and ENA documentation on Read the Docs (`ena-docs.readthedocs.io`).

### 1.1 Endpoints available (from the live Swagger spec)

The Search & Discovery group exposes:

| Endpoint | Purpose |
|---|---|
| `GET /search` | Perform a warehouse search (returns records) |
| `POST /search` | Same, via POST (essential for long query strings) |
| **`GET /count`** | **Count rows matching search parameters (no records returned)** |
| **`POST /count`** | Same, via POST |
| `GET /filereportcount` | Row count for a file report |
| `GET /filereport` | File report (sizes, FTP paths) |
| `GET /searchFields?result=<R>` | List of searchable fields for a result type |
| `GET /returnFields?result=<R>` | List of returnable fields for a result type |
| `GET /results?dataPortal=ena` | List of available result types (sample, read_run, analysis, sequence, assembly, …) |
| `GET /controlledVocab` | List of allowed values for a controlled-vocabulary field |
| `GET /links/{dataType}` | Cross-reference links |
| `POST /files` | Returns a download script for matched records' data files |

**This directly refutes the v1 claim that "ENA API has no count endpoint."** `/count` returns just the integer count of matching rows. This means per-country counts can be obtained with a single lightweight HTTP call per country — no record download, no pagination, no quarterly subdivision.

### 1.2 Record limits and pagination

- Default search output is capped at **100,000 records**.
- Setting **`&limit=0`** retrieves *all* matching records, including sets >1 million. (Confirmed in ENA advanced-search docs: "If you would like to retrieve all records resulting from a search, even for large sets of results (e.g. >1 million) you can set the limit to 0 by adding `&limit=0`.")
- There is **no offset/cursor pagination** in the conventional sense; `limit=0` is the supported way to fetch large sets. The practical guidance is to avoid downloading very large sets unless needed, and to keep concurrent searches to **no more than 10 at a time**.
- For *counts* the limit is irrelevant — `/count` returns the total regardless.

### 1.3 Rate limits

- Upper limit: **50 requests per second**. Exceeding returns HTTP 429 "Too Many Requests."
- ENA additionally recommends not running more than 10 searches concurrently.
- This is far more permissive than NCBI (see §2), so ENA is the better primary source for a few-hundred-country sweep.

### 1.4 `country` field matching semantics

- The `country` field is searched with **quoted exact value match**: `country="United Kingdom"`.
- **Wildcards are supported with `*`**, e.g. `specimen_voucher="ZMB:*"` and `bio_material="ZMB:Moll:*"` (documented examples). By the same mechanism, `country="USA:*"` is the way to match sub-national values such as `USA: California`, `USA: Texas`.
- The controlled vocabulary for country is the INSDC geo_loc_name list (see §4). `GET /controlledVocab` can enumerate allowed values.
- **Important nuance:** ENA's `country` field records the *collection locality* (the geo_loc_name as submitted: `Country[:Region][,Locality]`). It is **not** a sovereign-origin field. This is the same semantic caveat as v1 noted, and it remains valid.

### 1.5 Taxonomy filtering (non-human)

- `tax_eq(<taxid>)` matches exactly that taxon.
- `tax_tree(<taxid>)` matches the taxon and all descendants.
- Human = taxid 9606. Non-human filter: **`NOT tax_tree(9606)`**.
- For human-associated microbiome exclusion, `host_tax_id` is a searchable field on read/analysis results, so `NOT host_tax_id=9606` is available (see §5.6).

### 1.6 Date fields for time-period analysis

- `first_public` (archive deposition/public date) and `collection_date` (sample collection date) are both searchable/returnable on the `sample` (and read/analysis) result.
- ENA query syntax supports comparison operators (`>=`, `<=`, `=`) on these fields, so period filters such as `first_public>=2018 AND first_public<=2020` can be pushed into the `/count` query. *(Verify exact operator syntax for date fields during implementation; the comparison-operator pattern is standard in ENA's query grammar.)*

### 1.7 Bulk download / FTP options

- File-level data is available via **FTP or Aspera**; the `/filereport` endpoint summarises file locations and sizes for an accession.
- `enaBrowserTools` (GitHub: `enasequence/enaBrowserTools`) provides command-line scripts to bulk-fetch records by accession and to download all records linked to a Sample or Study.
- The **Browser API** (`https://www.ebi.ac.uk/ena/browser/api/xml/search?result=...&query=...`) returns full XML metadata records for a search — useful when you need metadata not indexed for Portal API search.

### 1.8 Exact query syntax to use (v2)

Count all non-human sample records for a country:
```
GET https://www.ebi.ac.uk/ena/portal/api/count?result=sample&query=country="USA" AND NOT tax_tree(9606)&format=json
```
Count with sub-national inclusion (equivalent of NCBI `[country]` broad match), explicit:
```
query=country="USA" OR country="USA:*" AND NOT tax_tree(9606)
```
(Note: `country="USA"` already matches the bare token; `USA:*` additionally guarantees sub-national variants are caught. Test whether the bare quoted form already absorbs sub-national entries on ENA; if not, OR in the `:*` form.)

Count for a time period:
```
query=country="USA" AND NOT tax_tree(9606) AND first_public>=2018 AND first_public<=2020
```

For long per-country query strings, use `POST /count` with the query in the body.

---

## 2. NCBI ESearch / E-utilities — findings

Sources: NLM Data Guide E-utilities reference, NCBI E-utilities book (NBK25497), NCBI SRA search docs, NCBI API-key guidance.

### 2.1 `rettype=count` returns the accurate total

- ESearch `rettype=count` "Displays only the total number of results, without the list of UIDs or query translation." This is the **total count of the full matching set**, independent of `retmax`.
- Even with the default `rettype=uilist`, the `<Count>` element in the ESearch XML/JSON response is the **total** number of matching records (the full result set), while `retmax` only controls how many UIDs are returned. So counts are available cheaply without retrieving UIDs.
- This makes NCBI a viable *counting* engine too — but see §2.4 on rate limits.

### 2.2 `[country]` field tag — how matching works

- NCBI Entrez fields are **token-indexed** with browsable term lists (the Advanced Search Builder's "Show index list" enumerates the indexed terms for a field). This is confirmed by the SRA/BioSample advanced-search documentation.
- The BioSample/sequence databases have a dedicated **`[country]`** field indexing the `/geo_loc_name` (formerly `/country`) qualifier. Because the field is tokenised on delimiters (`:` and `,`), a query like `USA[country]` matches records whose stored value is `USA`, `USA: California`, `USA: Texas, Houston`, etc. This is the **broader matching** v1 needed and failed to get from `[all]`.
- v1's `country="USA"[all]` did an **exact-phrase** match against the All Fields index, so `USA: California` did not match — explaining the ~61% loss and the 39% per-country sum.
- **Wildcards (`*`) are supported** on truncatable fields (up to 600 expansions). `USA*[country]` is therefore also possible, but plain `USA[country]` token matching is the cleaner, more predictable form.
- **Recommendation:** use `"<Country>"[country]` (token match). Do **not** use `[all]`.

### 2.3 Best way to get per-country counts from NCBI

- Use `esearch.fcgi?db=biosample&term=<Country>[country] AND NOT txid9606[orgn]&rettype=count&retmode=json`. The returned `esummary`/`count` is the total.
  - Note: in NCBI Entrez taxonomy filtering is expressed as `NOT txid9606[orgn]` (the `txid<id>[orgn]` form for "no descendants" vs `NOT "Homo sapiens"[orgn]`; to exclude the human subtree use `NOT txid9606[orgn]` which by convention includes descendants). Confirm subtree semantics during implementation.
- For a **single global count** across all Entrez databases for a query, `EGQuery` (`egquery.fcgi?term=...`) returns result counts per database in one call — handy for a quick BioSample vs SRA vs Nucleotide overview.
- For large UID retrieval (if ever needed), use the **History server**: ESearch posts the result set to `WebEnv`/`query_key`, then EFetch/ESummary pages through with `retstart`/`retmax` (retmax max 100,000 for ESearch, 10,000 for ESummary/EFetch).

### 2.4 Rate limits and best practices

- **3 requests/second without an API key; 10 requests/second with a free NCBI API key** (confirmed via NLM Support Center and NCBI Insights). For a ~300-country sweep plus period subdivisions, an API key is effectively mandatory.
- Always send `tool=<appname>` and `email=<you>` parameters so NCBI can contact you.
- NCBI asks that large jobs run off-peak (weekends or 21:00–05:00 ET) — relevant if you download UIDs, not if you only use `rettype=count`.
- `retmax` caps at 100,000 UIDs per ESearch call; page with `retstart` for more.

### 2.5 Bulk / pre-aggregated NCBI options discovered

- **SRA on BigQuery** and **SRA on Athena** (NCBI cloud offerings): the full SRA metadata is queryable in SQL with aggregate `GROUP BY` over attributes. This is the closest thing to a **pre-aggregated country count** and is worth a side check, though BioSample attribute aggregation in BigQuery requires attribute-extraction SQL.
- **NCBI Datasets** (with its own API and API-key handling) provides record-level and dataset-level retrieval but not pre-aggregated country counts.
- There is **no NCBI-published FTP file of per-country record counts**. Aggregation must be done via ESearch counts or cloud SQL.

### 2.6 Exact query syntax to use (v2)

Count all non-human BioSample records for a country (JSON, count only):
```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
  ?db=biosample
  &term=USA[country]+AND+NOT+txid9606[orgn]
  &rettype=count
  &retmode=json
  &tool=<app>&email=<you>&api_key=<key>
```
With a date range (deposition/publication date; BioSample supports `pdat`/collection ranges — verify the BioSample-specific date field names):
```
&term=USA[country]+AND+NOT+txid9606[orgn]+AND+2018:2020[pdat]
```

---

## 3. The ENA–NCBI relationship: the most important conceptual fix

**INSDC = NCBI GenBank + EMBL-EBI ENA + DDBJ.** The three partners exchange records and maintain mirrored copies. Consequently:

- ENA's sample set and NCBI's BioSample set are **overlapping subsets of one archive**, not independent populations.
- The v1 framing of NCBI as an independent "cross-reference" whose sum should approximate the ENA total is conceptually wrong. A 39% overlap-of-coverage figure reflects **indexing and query-matching differences** (exact `[all]` vs token `[country]`; ENA quoted-vocab vs NCBI tokenisation), **not** two independent measurements.
- **Never sum ENA + NCBI counts.** That double-counts the shared records.
- Use one source as **primary** (recommend ENA, for the reasons in §1) and the other as a **coverage/indexing cross-check**: run the same per-country query on both, compare, and investigate large divergences as data-quality findings rather than additive contributions.

---

## 4. INSDC controlled vocabulary and historical country names

Source: NCBI INSDC Geographic Location Name List (`ncbi.nlm.nih.gov/genbank/collab/country`) and INSDC geo_loc_name vocabulary.

- The geo_loc_name value format is `"<country>[:<region>][, <locality>]"`. Country must come from the INSDC controlled vocabulary.
- The current list contains the **sovereign states plus oceans/seas/territories** (e.g., `USA`, `United Kingdom`, `Democratic Republic of the Congo`, `Republic of the Congo`, `Cote d'Ivoire`, `Eswatini`, `Czechia`, `State of Palestine`, `South Sudan`, `Timor-Leste`, `North Macedonia`).
- **Historical country names are an explicitly separate INSDC list**: `Belgian Congo`, `British Guiana`, `Burma`, `Czechoslovakia`, `Czech Republic`, `East Timor`, `Korea`, `Macedonia`, `Micronesia`, `Netherlands Antilles`, `Serbia and Montenegro`, `Siam`, `Swaziland`, `The former Yugoslav Republic of Macedonia`, `USSR`, `Yugoslavia`, `Zaire`.
- INSDC publishes **approved null terms** for missing values (`not collected`, `not provided`, `missing`, `not applicable`, `restricted access`) — see §5.5.

### Handling historical names

- Historical names appear on records collected before the political entity changed. They are **legitimate provenance values** and must not be silently dropped.
- For **Cali Fund allocation** (benefit-sharing to *current* providers of genetic resources), historical names need a **mapping layer** to current UN M.49 sovereign entities:
  - Unambiguous single-successor cases: `Zaire` → Democratic Republic of the Congo; `Burma` → Myanmar; `Czech Republic` → Czechia; `Swaziland` → Eswatini; `East Timor` → Timor-Leste; `Siam` → Thailand.
  - Multi-successor cases (`USSR`, `Yugoslavia`, `Czechoslovakia`, `Serbia and Montenegro`, `Netherlands Antilles`, `Korea`) are **not safely mappable to a single current state**. Recommended treatment: retain as a separate "historical/unattributable-to-current-state" bucket, report the count, and exclude from current-country allocation unless a sub-national locality in the geo_loc_name disambiguates (e.g., `USSR: Georgia` → Georgia). Where a region/locality is present, use it to attribute; otherwise leave unattributed.
- Keep the **original** geo_loc_name in the raw data and store the **mapped** country as a derived column, so the mapping is auditable and reversible.

---

## 5. Statistical and scientific-practice assessment

### 5.1 Per-country querying vs download-all-then-aggregate

- **For counts**, per-country querying is now the right approach: ENA `/count` and NCBI `rettype=count` return totals in one cheap call each, with no need to download records. The v1 subdivision machinery is obsolete.
- **For attribution validation and double-count analysis**, download a **minimal field set** for each country via ENA `/search` with `limit=0` and `fields=accession,country,first_public,collection_date,scientific_name,tax_id`. This is small (text only, no sequence data) and lets you (a) inspect the actual `country` strings to verify tokenisation assumptions, (b) measure sub-national distribution, (c) reconcile ENA vs NCBI divergences.
- **Download-all-then-aggregate locally** is the gold standard for reproducibility and is now feasible with `limit=0`, but for a few-hundred-country × several-period matrix it is far more efficient to push aggregation into the API via `/count`. Recommend a hybrid: API counts for the full matrix; a one-time minimal-field dump for validation.

### 5.2 Double-counting risk with `Country: Region`

- A single record has exactly one geo_loc_name, e.g., `USA: California`. It should be counted **once**, attributed to **USA** (the token before the first `:`).
- Do **not** separately count `California` as a country. Sub-national regions are not INSDC country-level values; they are the region/locality suffix.
- The token-before-colon rule is the correct attribution. ENA `country="USA"` (and NCBI `USA[country]`) both attribute to the sovereign token, so per-country counts are inherently one-record-one-country. No double counting arises *within* a country. Cross-source double counting (ENA vs NCBI) is handled by §3 (never sum).

### 5.3 `first_public` vs `collection_date` for time-period analysis

- **`first_public`** = the date the record was made public in the archive. It is **reliably populated** for essentially all records and is the date the DSI *became available to users* — the temporally relevant anchor for a benefit-sharing/allocation question framed around DSI *utilisation*.
- **`collection_date`** = when the biological sample was collected in situ. It is the temporally relevant anchor for a question about *when the resource was accessed in the country of origin*. It is **frequently missing or imprecise** (year only, or `not collected`).
- **Recommendation:** use `first_public` as the **primary** temporal anchor for the three periods (2018–2020, 2021–2023, 2024+) and for the post-2023 cut, because coverage is complete and it maps to DSI availability. **Report `collection_date`-based counts as a secondary, explicitly-labelled sensitivity view** so readers see the difference between "when DSI became available" and "when the sample was collected." Never mix the two in one table.

### 5.4 Records with no country / "missing"

- INSDC-approved null terms (`missing`, `not collected`, `not provided`, `not applicable`, `restricted access`) and genuinely empty country fields should be **excluded from country-level counts** but **reported as a separate "unattributed" category** with its count.
- The size of the unattributed bucket is informative: it bounds the share of DSI that cannot be allocated to any provider country and should affect the **denominator** (allocated-share vs total-share) reported transparently.
- Decide and document whether allocation percentages are computed over (a) all records, or (b) only country-attributed records. Both are defensible; (b) is cleaner for allocation shares, (a) is more conservative. Report both.

### 5.5 Non-human filter — sufficiency of `NOT tax_tree(9606)`

- `NOT tax_tree(9606)` excludes records whose **organism** is in the human taxonomic subtree. It does **not** exclude **human-associated microbiome** records (gut/skin/oral metagenomes), whose *organism* is a biome-level metagenome taxon (e.g., `human gut metagenome`, taxid 408170) but whose `host_tax_id` is 9606.
- For "non-human DSI" in the genetic-resources/benefit-sharing sense, human-associated microbiome is a **policy judgment**: is human gut metagenome DSI "human" or "microbial genetic resource from a human-associated sample"? Most benefit-sharing framings treat it as human-associated and exclude it.
- **Recommendation:** use `NOT tax_tree(9606) AND NOT host_tax_id=9606` as the default non-human filter on ENA read/analysis results (where `host_tax_id` is indexed), and flag this choice explicitly. On the `sample` result, verify `host_tax_id` availability; if unavailable, supplement by excluding the known human-microbiome biome taxa (`tax_tree(408170)` etc.) as a documented approximation. State the filter in every output table.

### 5.6 Confidence intervals / uncertainty estimates

- The counts are **censuses of the archive at a point in time**, not samples. Frequentist confidence intervals on the raw counts are **not meaningful** (the count is the population value, not an estimate).
- The real uncertainty is **attributional and methodological**, not sampling:
  1. **Historical-country attribution** (USSR etc.) — multi-successor cases cannot be uniquely assigned.
  2. **Sovereign vs collection-locality semantics** — `country` records where the sample was collected, not necessarily the sovereign provider; overseas territories, Antarctic, and high-seas samples complicate attribution.
  3. **Unattributed records** — the excluded bucket's size affects any share-based figure.
  4. **ENA↔NCBI indexing divergence** — same archive, different matching; a non-trivial divergence is a data-quality signal, not a sampling error.
  5. **Temporal anchor choice** — `first_public` vs `collection_date` yields different period distributions.
- **Recommendation:** report counts as census values. Provide **sensitivity ranges** across (a) attribution assumptions (e.g., with/without historical-country mapping; sovereign vs collection-locality), (b) the non-human filter variants (with/without human-microbiome exclusion), and (c) temporal anchor (first_public vs collection_date). Add an explicit **"INSDC mirror overlap" caveat** that ENA and NCBI are not independent. Do not attach CI bars to counts; attach assumption-ranges instead.

---

## 6. Specific weaknesses in the v1 approach

1. **Missed the ENA `/count` endpoint.** Built an elaborate quarterly→monthly subdivision scheme to count records by downloading them, when a single `/count` call per (country × period) returns the number directly. This was the largest unnecessary cost in v1.
2. **Used NCBI `country="X"[all]` (exact-phrase) instead of `X[country]` (token field).** This is the root cause of the 39% coverage. `[all]` matches the whole All-Fields index as an exact phrase; `[country]` matches the dedicated, colon-tokenised country field and absorbs sub-national values.
3. **Treated ENA and NCBI as independent sources.** They are mirrored partners of INSDC. Summing or expecting them to reconcile to a single total misframes the problem; the right use of the second source is coverage cross-check, not addition.
4. **500k cap subdivision was an artifact** of trying to download-to-count; with `/count` there is no per-query record cap to hit.
5. **5 ENA country names missing from the INSDC→UN mapping** — a vocabulary-maintenance gap; the ENA controlled vocab (`/controlledVocab`) and the INSDC list should be programmatically diffed to drive the mapping table, not hand-maintained.
6. **`environmental_sample=true` reliance** (0.5% populated) — correctly being dropped in v2; it was never a reliable field.
7. **No temporal-anchor decision documented** — mixing `first_public` and `collection_date` without stating which is primary undermines reproducibility.
8. **No handling of historical country names** — these are an explicit INSDC category and need a mapping/flagging policy, not silent inclusion or exclusion.
9. **Non-human filter incomplete** — `NOT tax_tree(9606)` alone leaves human-associated microbiome in the denominator.
10. **No reproducibility scaffolding** — no pinned query strings, timestamps, vocab versions, or raw-response archive.

---

## 7. Recommended improvements for v2

1. **Primary engine: ENA `/count`.** One call per (country × period × filter). Use `POST /count` for long queries.
2. **Cross-check: NCBI ESearch `rettype=count` with `[country]`.** Same matrix, run separately, compared per country. Investigate divergences > a stated threshold as data-quality findings. Never sum the two.
3. **Drop the download-to-count subdivision.** No quarterly/monthly fallback needed.
4. **Fix the country mapping table** by diffing the live INSDC/ENA vocabulary against the UN M.49 list; auto-flag unmapped names.
5. **Add a historical-country mapping layer** with a documented policy (single-successor map; multi-successor → unattributed bucket; use region/locality to disambiguate where present).
6. **Temporal anchor: `first_public` primary**, `collection_date` secondary sensitivity view. Three periods (2018–2020, 2021–2023, 2024+) plus a post-2023 cut, exactly as specified.
7. **Non-human filter:** `NOT tax_tree(9606) AND NOT host_tax_id=9606` (documented; with biome-taxon fallback where `host_tax_id` is unavailable).
8. **Unattributed bucket:** report null-term and empty-country counts separately; publish both "share of attributed" and "share of total" denominators.
9. **Aggregations:** UN region, sub-region, development status, World Bank income group, and LDC/SIDS/LLDC flags — all derived from the mapping table, never re-fetched per record.
10. **Validation download:** one-time minimal-field dump (`accession,country,first_public,collection_date,scientific_name,tax_id`) via ENA `/search?limit=0` for a stratified sample of countries to verify tokenisation and double-count behaviour.
11. **Reproducibility:** pin all query strings, record the exact API-call timestamps (the archive is live and grows daily), version the INSDC vocab, UN M.49 file, and WB_CLASS file, and archive raw `/count` and ESearch responses alongside the derived tables.

---

## 8. Recommended pipeline architecture

```
[Inputs / pinned assets]
  INSDC geo_loc_name vocabulary (current + historical)   ──┐
  ENA controlledVocab (country)                           ──┤
  UN M.49 (unsd-country-codes.csv)                       ──┼─► country_master table
  World Bank WB_CLASS.xlsx                                ──┘      (insdc_name → un_m49 → wb_income → ldc/sids/lldc)
  Query template + filter spec (non-human, periods)      ──► pinned query manifest

[Stage 1 — Counts (ENA primary)]
  for each country in country_master:
    for each period in {all, post-2023, 2018-2020, 2021-2023, 2024+}:
      ENA POST /count
        result=sample
        query = country="<insdc_name>"
                AND NOT tax_tree(9606)
                AND NOT host_tax_id=9606
                [AND first_public>=YYYY AND first_public<=YYYY]
      store raw response → ena_counts[country, period]

[Stage 2 — Cross-check (NCBI)]
  for each country (same matrix):
    NCBI esearch.fcgi db=biosample
      term = "<insdc_name>"[country] AND NOT txid9606[orgn] [AND YYYY:YYYY[pdat]]
      rettype=count, retmode=json, tool/email/api_key
    store → ncbi_counts[country, period]

[Stage 3 — Reconciliation]
  compare ena_counts vs ncbi_counts per (country, period)
  flag divergences > threshold → divergence_report
  (never sum; ENA is authoritative, NCBI is coverage evidence)

[Stage 4 — Attribution validation]
  one-time ENA /search?limit=0&fields=accession,country,first_public,
            collection_date,scientific_name,tax_id
  for a stratified sample of countries → validate tokenisation,
  sub-national distribution, historical-name handling

[Stage 5 — Aggregation]
  map country_master → {UN region, sub-region, dev status, WB income,
                        LDC, SIDS, LLDC}
  aggregate Stage 1 counts by each grouping × period
  compute attributed-share and total-share denominators
  carry unattributed bucket through

[Stage 6 — Reporting]
  tables: (a) all records, (b) post-2023, (c) three-year periods
          × {UN region, dev status, WB income, LDC, SIDS, LLDC}
  sensitivity views: first_public vs collection_date;
                     with/without historical mapping;
                     with/without human-microbiome exclusion
  caveats: INSDC mirror overlap; sovereign-vs-locality semantics;
           unattributed share; temporal-anchor choice

[Provenance archive]
  raw /count + esearch responses, query manifest, vocab versions,
  input file hashes, run timestamp → reproducibility bundle
```

---

## 9. Key references (retrieved October 2026)

- ENA Portal API Swagger/OpenAPI spec — `https://www.ebi.ac.uk/ena/portal/api/` (endpoints incl. `/count`, `/filereportcount`, `/controlledVocab`, `/searchFields`, `/returnFields`, `/results`).
- ENA Documentation (Read the Docs) — advanced search, programmatic access, rate limits (50 req/s), `&limit=0` for >1M records, `tax_tree`/`tax_eq`, `country="..."` exact + `*` wildcards.
- ENA Browser API — `https://www.ebi.ac.uk/ena/browser/api/xml/search` for full XML metadata.
- `enaBrowserTools` — `https://github.com/enasequence/enaBrowserTools` (bulk fetch by accession/Sample/Study; FTP/Aspera).
- NLM Data Guide / NCBI E-utilities book (NBK25497) — ESearch parameters, `rettype=count`, `retmax` 100k cap, `retstart` paging, History server (`WebEnv`/`query_key`).
- NCBI SRA/BioSample search docs — Advanced Search Builder, "Show index list" (token-indexed fields), wildcard `*`, field-tagged search.
- NCBI API-key guidance — 3 req/s without key, 10 req/s with key; `tool`/`email` parameters.
- NCBI INSDC Geographic Location Name List — `https://www.ncbi.nlm.nih.gov/genbank/collab/country/` (current + historical country names; null terms).
- INSDC geo_loc_name vocabulary — `https://www.insdc.org/submitting-standards/geo_loc_name-qualifier-vocabulary/`.
- NCBI SRA cloud search — BigQuery and Athena options for SQL aggregation over SRA metadata.

---

## 10. Bottom line

The v1 architecture was shaped by two incorrect premises (no ENA count endpoint; only `[all]` matching at NCBI) and one conceptual error (treating mirrored INSDC partners as independent). The v2 architecture removes all three: use **ENA `/count`** for cheap exact-vocabulary counts, use **NCBI `[country]` + `rettype=count`** as a coverage cross-check, treat the two as **overlapping views of one archive**, push time-period and non-human filters into the query, and add the missing **historical-country mapping**, **temporal-anchor policy**, **unattributed-bucket reporting**, and **reproducibility bundle**. No record download is required to produce the count matrix; a small validation dump suffices to verify attribution behaviour.
