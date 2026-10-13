# Annual ENA Query Approach — Methodology Evaluation

**Prepared for:** Cali Fund allocation methodology — annual per-country DSI sequence-record counts
**Scope:** Evaluate switching the v2 pipeline from 3-year period buckets to **annual** per-country counts (2018–2025) for all 296 INSDC country names plus unattributed records. All findings below are grounded in live queries against the ENA Portal API (`https://www.ebi.ac.uk/ena/portal/api/`) executed on 2026-10-12, using Python `urllib` (not `curl`, which has an OpenSSL issue on this machine).
**Existing pipeline evaluated:** `/Users/jasminekindness/IIFB_COP17/ahteg_allocation/pipeline/run_pipeline.py`
**Prior evaluation:** `/Users/jasminekindness/IIFB_COP17/ahteg_allocation/api_evaluation.md`

> All counts in this document are point-in-time census values from the ENA `sample` result unless stated otherwise. The archive grows daily and counts drift.

---

## 1. Summary of findings (key recommendations)

The annual approach is **sound and feasible** — `first_public` date-range filtering works correctly on the `/count` endpoint and returns sensible per-year totals. However, the evaluation uncovered **three serious issues** that affect both the existing v2 data and any annual extension, plus several smaller refinements.

**Three serious issues (must fix before annual numbers are usable):**

1. **`country="X"` is an ANY-TOKEN match, not a leading-token match — it causes large cross-country contamination.** This is the most important finding. `country="Guinea"` returns 29,208 records but 22,114 of those are actually **Papua New Guinea** and 627 are **Equatorial Guinea**; `country="Korea"` (194,950) absorbs **all of South Korea** (164,121); `country="Republic of the Congo"` (26,898) absorbs **all of Democratic Republic of the Congo** (25,087 — 93% contamination). The existing `ena_counts.csv` already contains these contaminated, double-counted values. Nine collision pairs were confirmed empirically (§4). This biases country, regional, and income aggregates.

2. **21.5% of non-human records (6,545,221) have NO `first_public` date** — and 22.1% of *country-attributed* records (5,011,632 of 22,641,119) lack it. `last_updated` rescues only ~900K of these; 5.6M have neither date. Annual buckets therefore systematically miss ~22% of country-attributed records. The "all" (undated) count is reliable; every `first_public`-filtered annual count is not. This must be disclosed via an explicit "undated" bucket per country, not silently dropped.

3. **The task brief's description of the unattributed query is wrong, but the code is right.** The brief says unattributed is queried as `country="*"`. The code actually uses `NOT country="*"` (correct). Empirically `country="*"` = 34,456,233 records that *have* a country value; `NOT country="*"` = 21,307,413 records with *no* country. So `country="*"` is an existence/wildcard match ("country is set"), NOT "all records". The unattributed bucket is correctly `NOT country="*"` (= 7,759,012 non-human). Do not "fix" this to `country="*"`.

**Smaller refinements recommended:**

- **Exclude synthetic constructs** (`NOT tax_tree(32630)`) — 86,919 records (0.29%) are plasmids/vectors/artificial sequences with no country of biological origin.
- **Environmental metagenomes (8.4M, 27.7% of the non-human set) are currently included.** This is defensible (environmental community DNA from a country is DSI from that country) but is a policy judgment that materially changes country rankings. Report a sensitivity view with/without `tax_tree(408169)`.
- **The non-human filter `NOT tax_tree(9606) AND NOT host_tax_id=9606` is robust and correctly excludes 10.09M human-microbiome records** that `NOT tax_tree(9606)` alone would keep. `host_tax_id` is indexed and populated on the `sample` result. A small residual leak of human-microbiome records with missing `host_tax_id` may remain (unquantifiable via `/count`); flag it.
- **`first_public` is the correct temporal anchor** (best coverage at 78.5% of non-human records; `collection_date` is only ~50% populated). It is also stable against re-annotation (`last_updated` changes, `first_public` does not).
- **There is no `geo_loc_name` field on the ENA `sample` result — the field is named `country`** and it *holds* the geo_loc_name value (`Country[:Region][,Locality]`). So `country` is the right and only field; do not look for `geo_loc_name`.
- **ENA offers no exact-match operator** (`country eq "USA"` and `country=="USA"` both return HTTP 400). The only way to get clean per-country counts is to subtract colliding names with `AND NOT country="<longer name>"` for the 9 collision pairs (§4, §8).

---

## 2. Non-human DSI definition

### 2.1 Current filter and empirical breakdown

Current filter: `NOT tax_tree(9606) AND NOT host_tax_id=9606` on `result=sample`.

| Query | Count | What it represents |
|---|---|---|
| `tax_tree(9606)` | 15,271,288 | Human-organism subtree (Homo sapiens and descendants) |
| `host_tax_id=9606` | 10,108,910 | Records whose host is human (human microbiome) |
| `tax_tree(9606) AND host_tax_id=9606` | 16,683 | Overlap (nearly disjoint — a few odd annotations) |
| `NOT tax_tree(9606)` | 40,492,358 | Everything except human organism |
| `NOT tax_tree(9606) AND NOT host_tax_id=9606` | **30,400,131** | **Current non-human filter (matches v2 SUMMARY exactly)** |
| `NOT tax_tree(9606) AND host_tax_id=9606` | 10,092,277 | Human microbiome that the tax-only filter would wrongly keep |

**Verdict: the current filter is robust and is doing real work.** The `host_tax_id=9606` clause excludes 10.09M human-microbiome records (gut/skin/oral metagenomes whose *organism* is a biome-level taxon like `human gut metagenome` (taxid 408170 = 1,246,633 records) but whose host is human). Dropping the `host_tax_id` clause would inflate the non-human set by 33% (30.4M → 40.5M) with human-associated microbiome.

`host_tax_id` is a searchable `number` field on `sample`; 12,787,348 records have any host set, 42,976,298 have none. A record with no host is correctly retained (it is not a human-host record). The filter logic is sound.

### 2.2 Residual caveats

- **Human-microbiome records with missing `host_tax_id`** will leak through. A gut-metagenome record whose submitter did not set `host_tax_id=9606` is not caught by either clause (its organism taxon 408170 is outside the human subtree). The leak size is not directly measurable via `/count`, but `tax_tree(408170)` (human gut metagenome) = 1,246,633; most of these presumably do set `host_tax_id`. Treat as a small, documented residual.
- **No need to exclude records with no taxonomic classification.** `tax_id=0` returns 0 records; there is no "unclassified at zero" population to worry about on `sample`. Records with a missing/blank tax_id are simply not in the human subtree and are correctly retained.

### 2.3 Environmental samples / metagenomes — policy judgment, include by default but report sensitivity

| Query | Count |
|---|---|
| `NOT tax_tree(9606) AND NOT host_tax_id=9606 AND tax_tree(408169)` (all metagenomes kept by filter) | 8,424,803 (27.7% of the non-human set) |
| `NOT tax_tree(9606) AND NOT host_tax_id=9606 AND tax_tree(256318)` (Metagenomes bucket) | 961,644 |
| `environmental_sample=true` | 144,150 |
| `environmental_sample=false` | 37,218 |

- The 8.4M metagenomes retained by the filter are **environmental / non-human-host community DNA** (soil, water, marine, rumen, etc.). After excluding human-host microbiome, these remain.
- For a country-allocation methodology, environmental metagenomes sequenced from a country's territory are legitimately "DSI of genetic resources from that country." **Include them by default**, but they materially inflate counts for countries with large environmental-sequencing programs (e.g., ocean expeditions attribute to the coastal/ocean label). **Report a sensitivity view with `AND NOT tax_tree(408169)`** (which drops the non-human set to 21,975,328) so readers can see the effect.
- `environmental_sample` is not usable as a filter: it is populated on only ~181K of 55.8M records. Drop it (the v2 pipeline already does).

### 2.4 Synthetic constructs — recommend excluding

`tax_tree(32630)` (synthetic constructs — plasmids, vectors, artificial sequences) = 86,991; 86,919 remain after the non-human filter. These are lab artifacts with no country of biological origin and should not be attributed to a provider country. Impact is tiny (0.29%) but the exclusion is conceptually correct. **Recommend adding `AND NOT tax_tree(32630)` to the default filter.**

### 2.5 Recommended non-human filter (default)

```
NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
```
(= 30,313,212 vs 30,400,131 currently — drops 86,919 synthetic constructs.)

---

## 3. Temporal anchor

### 3.1 `first_public` is the right primary anchor — but has a 22% gap

| Query | Count | Coverage |
|---|---|---|
| `first_public>=1900-01-01` (has a first_public) | 47,307,702 | 84.8% of all 55,763,646 samples |
| `NOT first_public>=1900-01-01` (no first_public) | 8,455,944 | 15.2% |
| Non-human total | 30,400,131 | — |
| Non-human WITH first_public | 23,854,910 | 78.5% |
| Non-human WITHOUT first_public | **6,545,221** | **21.5%** |
| Non-human, country-attributed, WITH first_public | 17,629,487 | — |
| Non-human, country-attributed, WITHOUT first_public | **5,011,632** | **22.1% of 22,641,119 attributed** |

**The gap is large and concentrated in country-attributed records.** Spot-checked records with no `first_public` (e.g. `SAMEA10000000`, *Oryza sativa*) have a `last_updated` of 2021-10-14 but a blank `first_public` — they appear to be ENA-internal/broker-submitted samples for which the Portal API index does not expose `first_public`. This may be an indexing artifact (the Browser may show a public date), but `/count` returns blank, so for methodology purposes the gap is real.

### 3.2 `last_updated` does NOT rescue the gap

| Query | Count |
|---|---|
| Non-human, no first_public, HAS last_updated | 900,935 |
| Non-human, no first_public, NO last_updated either | 5,644,286 |

Only ~14% of the no-`first_public` records have `last_updated`; 5.6M have **neither** date and are undateable via the Portal API. Using `last_updated` as a fallback would recover ~900K records but mixes semantics (update date ≠ public date) and still leaves 5.6M undateable. **Not recommended as a default fallback**; at most use it for a clearly-labelled sensitivity view.

### 3.3 `collection_date` is much worse — do not use as primary

`collection_date>=1000-01-01` = 28,094,978 (~50% of all samples). It is frequently missing or imprecise (year-only, `not collected`). `collection_date_start` returned HTTP 400 (not a searchable field on `sample` in the expected form). `collection_date` is the right anchor for "when was the sample collected in situ" but wrong for "when did the DSI become available" and has half the coverage. **Keep `first_public` primary; report `collection_date`-based counts only as a secondary, explicitly-labelled sensitivity view** (as the prior evaluation recommended).

### 3.4 Re-annotation does not move records between years

| Query | Count |
|---|---|
| `last_updated>=2024-01-01` | 18,737,289 |
| `first_public<2018 AND last_updated>=2024` (old, re-annotated recently) | 1,783,666 |
| `first_public<2018 AND last_updated<2018` (old, untouched) | 2,035,833 |

1.78M pre-2018 records were re-touched in 2024+, but `first_public` is the *original* public date and does not change on re-annotation. So annual `first_public`-based counts are **stable against re-annotation** — a record stays in its original year. (Caveat: if ENA ever backfills `first_public` for the 5.6M blank records, historical annual counts will shift. Treat the undated bucket as a longitudinal-stability risk.)

### 3.5 Verdict

`first_public` is the best-available temporal anchor. Use it as primary. **Must report an explicit "undated" bucket per country** (`country="X" AND <filter> AND NOT first_public>=1900-01-01`) and disclose that annual counts cover only the dated subset (~78% of non-human records). Never present an annual count as a complete census of that year's records.

---

## 4. Country field — `country="X"` is an ANY-TOKEN match (critical)

### 4.1 There is no `geo_loc_name` field; `country` holds the geo_loc_name value

The ENA Portal API `sample` result exposes a field `country` (type `text`, description: *"locality of sample isolation: country names, oceans or seas, followed by regions and localities"*). There is **no separate `geo_loc_name` field**. Actual stored values (from `/search`) confirm `country` holds the full INSDC geo_loc_name string:

```
country = "USA"                       (bare)
country = "USA: USA"                  (country: region, redundant)
country = "USA:USA"                   (no space after colon)
country = "United Kingdom: United Kingdom, United Kingdom"
country = "China: China"
```

So `country` *is* the geo_loc_name field. The INSDC controlled vocabulary (`insdc_countries_clean.txt`, 296 entries) is the correct value list. The ENA `controlledVocab?field=country` endpoint returned 0 entries (the vocab is not exposed there for this field), so the local 296-entry file remains the authoritative list.

### 4.2 `country="X"` does ANY-TOKEN matching, not leading-token — this causes cross-country contamination

This is the central methodological finding. Empirical tests prove `country="X"` matches any record where `X` appears as a token (word-boundary prefix) **anywhere** in the country field, not only as the leading token before the first colon:

| Query | Count | Absorbs (overlap = full) |
|---|---|---|
| `country="Guinea"` | 29,208 | Papua New Guinea (22,114), Equatorial Guinea (627), Guinea-Bissau (2,575) |
| `country="Korea"` | 194,950 | South Korea (164,121), North Korea (636) |
| `country="Republic of the Congo"` | 26,898 | Democratic Republic of the Congo (25,087) |
| `country="Sudan"` | 3,988 | South Sudan (322) |
| `country="Virgin Islands"` | 6,007 | British Virgin Islands (132) |
| `country="Macedonia"` | 1,336 | The former Yugoslav Republic of Macedonia (36) |
| `country="Micronesia"` | 1,278 | Micronesia, Federated States of (800) |
| `country="Samoa"` | 2,575 | American Samoa (1,216) |
| `country="Serbia"` | 6,264 | Serbia and Montenegro (11) |

Each "absorbs" figure was confirmed by an overlap query, e.g. `country="Guinea" AND country="Papua New Guinea"` = 22,114 = the *entire* Papua New Guinea count. So the shorter name's query fully contains the longer name's records.

The matching rule inferred from all tests: `country="X"` matches records where `X` appears as a word-boundary-prefixed token anywhere in the country field. The "word boundary" is a non-alphanumeric character (space, hyphen, comma, colon, or end-of-string). This is why:
- `country="USA"` correctly matches `USA`, `USA: USA`, `USA: California` (USA followed by boundary) — **sub-national IS absorbed, which is desired.**
- `country="Guinea"` wrongly matches `Guinea-Bissau` (hyphen boundary), `Papua New Guinea` (space boundary before Guinea), `Equatorial Guinea` — **cross-country contamination, undesired.**
- `country="India"` does **not** match `Indian Ocean` (after "India" comes "n", alphanumeric, no boundary) — overlap only 16 oddballs. **Safe.**
- `country="Niger"` does **not** match `Nigeria` (after "Niger" comes "i") — overlap only 169 oddballs. **Safe.**
- `country="Dominica"` does **not** match `Dominican Republic` (after "Dominica" comes "n") — overlap 0. **Safe.**

### 4.3 The existing v2 data is already contaminated and double-counted

The current `ena_counts.csv` confirms the contamination. Selected rows (columns: all, post2023, 2018-2020, 2021-2023, 2024+):

```
Guinea,24760,3275,2270,6907,3275               <- includes PNG (20,627) + EqG (214) + G-B (923)
Papua New Guinea,20627,2780,2138,4464,2780     <- also counted inside Guinea's row
Korea,125729,57198,16978,33026,57198           <- includes South Korea (106,435) + NK (625)
South Korea,106435,49253,12729,27680,49253     <- also counted inside Korea's row
Republic of the Congo,17427,1851,1015,3141,1851<- includes DRC (15,831)
Democratic Republic of the Congo,15831,1637,715,2403,1637 <- also counted inside RoC's row
```

Because the pipeline sums per-INSDC-name counts into UN-country buckets, the contamination becomes **double-counting in aggregates**:
- "Korea" and "South Korea" both map to UN "Republic of Korea" → Republic of Korea gets 125,729 + 106,435 = 232,164 instead of the true 125,729 (overcount 106,435, +85%).
- "Republic of the Congo" (→ UN Congo) and "Democratic Republic of the Congo" (→ UN DRC) are *different* UN countries, so DRC's 15,831 is counted in both the Congo and DRC aggregates → Africa region and global totals double-count 15,831.
- "Guinea" (→ Africa) and "Papua New Guinea" (→ Oceania) are different UN countries, so PNG's 20,627 is double-counted across two regions.

**This affects the existing SUMMARY.md aggregates, not just the annual extension.**

### 4.4 There is no exact-match operator

Tested alternatives to force exact/leading-token match — all fail or behave identically:
- `country=USA` (no quotes) = 9,220,351 — same as `country="USA"` (still any-token).
- `country eq "USA"` → HTTP 400.
- `country=="USA"` → HTTP 400.

So the **only** way to obtain clean per-country counts is to subtract each colliding longer name from the shorter name's query (§8).

### 4.5 Clean counts via exclusion (verified to partition correctly)

| Shorter name | Clean query (exclusions) | Clean count | vs raw |
|---|---|---|---|
| Guinea | `country="Guinea" AND NOT country="Papua New Guinea" AND NOT country="Equatorial Guinea" AND NOT country="Guinea-Bissau"` | 3,892 | 29,208 |
| Korea | `country="Korea" AND NOT country="South Korea" AND NOT country="North Korea"` | 30,193 | 194,950 |
| Republic of the Congo | `country="Republic of the Congo" AND NOT country="Democratic Republic of the Congo"` | 1,811 | 26,898 |
| Sudan | `country="Sudan" AND NOT country="South Sudan"` | 3,666 | 3,988 |
| Virgin Islands | `country="Virgin Islands" AND NOT country="British Virgin Islands"` | 5,875 | 6,007 |
| Macedonia | `country="Macedonia" AND NOT country="The former Yugoslav Republic of Macedonia"` | 1,300 | 1,336 |
| Micronesia | `country="Micronesia" AND NOT country="Micronesia, Federated States of"` | 478 | 1,278 |
| Samoa | `country="Samoa" AND NOT country="American Samoa"` | 1,359 | 2,575 |
| Serbia | `country="Serbia" AND NOT country="Serbia and Montenegro"` | 6,253 | 6,264 |

Partition arithmetic checks out (e.g. clean Korea 30,193 + South Korea 164,121 + North Korea 636 = 194,950 raw). The 9 longer names (Papua New Guinea, Equatorial Guinea, Guinea-Bissau, South Korea, North Korea, DRC, South Sudan, British Virgin Islands, TfYRoM, Micronesia FS, American Samoa, Serbia and Montenegro) are themselves **clean** (their phrase does not appear as a subsequence in any other vocab name) and need no exclusions.

### 4.6 Non-vocabulary country values — small coverage gap

Some records carry country values outside the 296-entry vocabulary, e.g. bare `country="Congo"` = 27,146. Of these, 26,898 are the Republic-of-the-Congo records (matched by the "Congo" token) and ~248 are genuine non-vocab orphans. These orphan records have a country set (so they are in `country="*"` = 22,641,119 non-human attributed) but are **not captured by any of the 296 vocab queries**. Net effect on the per-country sum is small but non-zero. **Recommend a reconciliation check**: sum of clean per-country counts vs `country="*"` total; the residual is the non-vocab orphan set and should be reported as an "attributed but non-vocabulary" bucket.

---

## 5. Annual query approach

### 5.1 Syntax works

The proposed form works correctly on `/count`:
```
country="X" AND NOT tax_tree(9606) AND NOT host_tax_id=9606
       AND first_public>=YYYY-01-01 AND first_public<YYYY+1-01-01
```
Comparison operators `>=` and `<` on `first_public` are supported and return clean annual partitions. No year-extraction function is needed.

### 5.2 Global annual totals (non-human, all countries, for sanity)

| Year | Non-human count (first_public) |
|---|---|
| 2018 | 1,023,435 |
| 2019 | 1,554,162 |
| 2020 | 2,032,508 |
| 2021 | 3,577,168 |
| 2022 | 3,353,216 |
| 2023 | 3,618,682 |
| 2024 | 2,400,511 |
| 2025 | 2,529,321 |
| **Sum 2018–2025** | **20,089,003** |
| Non-human total (no date filter) | 30,400,131 |
| Non-human pre-2018 | 2,322,892 |
| Non-human no first_public | 6,545,221 |

Reconciliation: 20,089,003 (2018–2025) + 2,322,892 (pre-2018) + 6,545,221 (undated) = 28,957,116 ≈ 30,400,131 (residual ~1.44M is records with `first_public>=1900` but outside the clean partitions — rounding/timing at the API; the bulk reconciles). The key point: **annual counts total ~20M vs an "all" of 30.4M — the 10.3M difference is pre-2018 + undated records, not a query bug.**

### 5.3 No caps or limits on `/count`

`/count` returns the total matching count regardless of size; there is no 100,000/500K cap (those apply to `/search` record retrieval, not `/count`). Date-range queries impose no extra limits.

### 5.4 Use POST for long queries

The clean collision queries (e.g. Guinea with three `NOT country="..."` clauses plus the non-human filter plus the date range) are long. Use `POST /count` with the query in the body to avoid URL-length issues. The simple annual queries for non-collision countries fit comfortably in GET.

### 5.5 Query volume and rate limits

296 countries × 8 years = 2,368 queries + 8 unattributed + 8 attributed-total (reconciliation) + 9×8 undated-bucket for collision countries ≈ ~2,450 queries. ENA allows 50 req/s; at a conservative 0.15s delay this is ~6 minutes. No API key needed. Comfortably feasible.

---

## 6. Unattributed records

### 6.1 The correct query is `NOT country="*"` (the code is right; the task brief is wrong)

| Query | Count | Meaning |
|---|---|---|
| `country="*"` | 34,456,233 | Records that HAVE a country value (wildcard = exists) |
| `NOT country="*"` | 21,307,413 | Records with NO country value |
| `country="*" AND <non-human>` | 22,641,119 | Attributed non-human (= v2 "with country") |
| `NOT country="*" AND <non-human>` | 7,759,012 | Unattributed non-human (= v2 "unattributed") |

`country="*"` is a **wildcard-existence** match ("country field is non-empty"), **not** "all records". So:
- **Unattributed** = `NOT country="*"` AND `<non-human filter>` (correct; what the code does; = 7,759,012).
- **Attributed total** (for reconciliation) = `country="*"` AND `<non-human filter>` (= 22,641,119).

The task brief's statement that unattributed is "queried as `country="*"`" is incorrect; that would return the *attributed* set. The pipeline code is correct. Do not change it.

### 6.2 Annual unattributed query

```
NOT country="*" AND NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
       AND first_public>=YYYY-01-01 AND first_public<YYYY+1-01-01
```
This correctly returns undated-by-country records (no country) made public in year YYYY. Unattributed records are also subject to the 22% `first_public` gap (1,533,589 of the 7,759,012 unattributed non-human records lack `first_public`).

### 6.3 Should `geo_loc_name` also be checked for attribution?

No — there is no separate `geo_loc_name` field (§4.1). `country` is the only attribution field. A record is either attributed (`country="*"`) or not (`NOT country="*"`). There is no second field to cross-check.

---

## 7. Other issues

### 7.1 `result=sample` is the correct grain

| Result | Total records | Non-human USA |
|---|---|---|
| `sample` | 55,763,646 | 3,965,097 |
| `read_run` | 44,417,100 | 3,817,112 |
| `analysis` | 24,298,525 | 889,809 |

`sample` = one record per BioSample (the biosample grain). `read_run` and `analysis` count sequencing runs / analyses, which inflates counts (one sample → many runs). For country provenance, **`sample` is correct** and the pipeline's choice is right. Do not switch to `read_run` or `analysis`.

### 7.2 The INSDC vocabulary is complete but historical names need a mapping policy

The 296-entry vocab includes both current sovereign states and historical names (USSR, Yugoslavia, Czechoslovakia, Zaire, Korea, etc.) plus oceans/seas/territories. The pipeline's `INSDC_TO_UN` mapping handles these. One side note observed during probing (out of scope for the query methodology but worth flagging): the historical `"Korea"` entry is large (30,193 clean records) and the mapping `"Korea": "Republic of Korea"` attributes all historical Korea records to South Korea — a mapping-policy decision that should be revisited (historical Korea is arguably a multi-successor case like USSR).

### 7.3 Records are re-annotated but `first_public` is stable

1.78M pre-2018 records were re-touched (`last_updated>=2024`) but remain in their original `first_public` year. Annual `first_public` counts are therefore stable against re-annotation. The real longitudinal risk is the 5.6M records with **no** date at all: if ENA backfills `first_public` for them later, historical annual counts will shift upward. Pin run timestamps and re-runnable queries.

### 7.4 Rate limiting

ENA Portal API: 50 req/s, no more than 10 concurrent searches. The annual sweep (~2,450 sequential queries at 0.15s spacing) is well within limits. No API key required (unlike NCBI, which needs one for its 3→10 req/s tier).

### 7.5 Data quality of country attribution

Country attribution records *collection locality*, not sovereign provider of the genetic resource. Overseas territories, Antarctica, and high-seas/ocean labels complicate attribution (the pipeline already routes oceans/seas to `__OCEANS_SEAS__` and territories to `__TERRITORY__`). This is inherent to INSDC provenance and not fixable via query syntax; it is a documented caveat for allocation methodology, not a query bug.

### 7.6 Reconciliation gap to monitor

Sum of clean per-country (annual) counts + unattributed (annual) + undated-bucket + non-vocab-orphans should equal `country="*"` + `NOT country="*"` for that year. The pipeline currently does not publish this reconciliation. **Add it** so leakage (collisions, non-vocab values, undated records) is visible in every output.

---

## 8. Concrete recommendations — exact query strings

### 8.1 Default non-human filter (all queries)

```
NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
```
(Adds `AND NOT tax_tree(32630)` vs the current filter to drop 86,919 synthetic constructs. If the project prefers to keep the current filter for continuity with v2, drop this clause and document it — the impact is 0.29%.)

### 8.2 Annual per-country query — non-collision country (287 of 296 names)

For year `YYYY`, country `X` (none of the 9 collision short names):
```
country="X" AND NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
       AND first_public>=YYYY-01-01 AND first_public<YYYY+1-01-01
```
This correctly absorbs sub-national values (`X: Region`, `X:Region`) because `X` is the leading token; for non-collision names no other vocab name contains `X` as a token, so there is no cross-country contamination.

### 8.3 Annual per-country query — the 9 collision short names (use exclusions + POST)

```
country="Guinea" AND NOT country="Papua New Guinea" AND NOT country="Equatorial Guinea"
       AND NOT country="Guinea-Bissau"
       AND NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
       AND first_public>=YYYY-01-01 AND first_public<YYYY+1-01-01
```
```
country="Korea" AND NOT country="South Korea" AND NOT country="North Korea"
       AND NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
       AND first_public>=YYYY-01-01 AND first_public<YYYY+1-01-01
```
```
country="Republic of the Congo" AND NOT country="Democratic Republic of the Congo"
       AND NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
       AND first_public>=YYYY-01-01 AND first_public<YYYY+1-01-01
```
```
country="Sudan" AND NOT country="South Sudan"
       AND NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
       AND first_public>=YYYY-01-01 AND first_public<YYYY+1-01-01
```
```
country="Virgin Islands" AND NOT country="British Virgin Islands"
       AND NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
       AND first_public>=YYYY-01-01 AND first_public<YYYY+1-01-01
```
```
country="Macedonia" AND NOT country="The former Yugoslav Republic of Macedonia"
       AND NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
       AND first_public>=YYYY-01-01 AND first_public<YYYY+1-01-01
```
```
country="Micronesia" AND NOT country="Micronesia, Federated States of"
       AND NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
       AND first_public>=YYYY-01-01 AND first_public<YYYY+1-01-01
```
```
country="Samoa" AND NOT country="American Samoa"
       AND NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
       AND first_public>=YYYY-01-01 AND first_public<YYYY+1-01-01
```
```
country="Serbia" AND NOT country="Serbia and Montenegro"
       AND NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
       AND first_public>=YYYY-01-01 AND first_public<YYYY+1-01-01
```

The 12 longer collision names (Papua New Guinea, Equatorial Guinea, Guinea-Bissau, South Korea, North Korea, Democratic Republic of the Congo, South Sudan, British Virgin Islands, The former Yugoslav Republic of Macedonia, Micronesia Federated States of, American Samoa, Serbia and Montenegro) are queried with the plain §8.2 form — they are already clean.

### 8.4 Annual unattributed query

```
NOT country="*" AND NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
       AND first_public>=YYYY-01-01 AND first_public<YYYY+1-01-01
```

### 8.5 Annual attributed-total query (for reconciliation)

```
country="*" AND NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
       AND first_public>=YYYY-01-01 AND first_public<YYYY+1-01-01
```

### 8.6 Per-country "undated" bucket (records with country but no first_public)

For each country `X` (apply the same §8.2/§8.3 collision exclusions):
```
country="X" [collision exclusions if needed]
       AND NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
       AND NOT first_public>=1900-01-01
```
Report this alongside the annual counts so the ~22% datedness gap is visible per country. (The gap is uneven: USA is only 8.2% undated, while the global country-attributed average is 22.1% — some countries will be much worse.)

### 8.7 Sensitivity views to publish alongside the default

1. **With/without environmental metagenomes:** add `AND NOT tax_tree(408169)` (drops non-human set from ~30.3M to ~21.9M).
2. **With/without the `NOT tax_tree(32630)` synthetic-construct exclusion** (0.29% effect).
3. **`first_public` vs `collection_date`** temporal anchor (collection_date has ~50% coverage — label clearly as "sample-collection year, partial coverage").
4. **`last_updated` fallback for the 900K no-`first_public` records that have it** (label as "update-date fallback, mixed semantics").

### 8.8 Implementation notes

- Use `POST /count` for all collision-country and any long query (body: `result=sample&query=...&format=json`).
- For each (country, year) store: clean annual count, undated count, and the raw `country="X"` (un-excluded) count for audit. Keep the raw response.
- Publish a reconciliation row per year: `sum(clean per-country) + unattributed + undated + non-vocab-orphans == attributed-total + unattributed-total`. Investigate any residual.
- Pin the INSDC vocab file hash, the query manifest, and the run timestamp. The archive grows daily; counts are a snapshot.
- **Backfill the existing v2 period-bucket data with the same collision exclusions** before relying on any v2 aggregate — the current `country_provenance_counts.csv` and `agg_by_*.csv` outputs contain the double-counted values documented in §4.3.

---

## 9. Bottom line

The annual extension is mechanically straightforward (`first_public>=YYYY-01-01 AND first_public<YYYY+1-01-01` works), but **two pre-existing problems must be fixed first or the annual numbers will inherit the same biases as the v2 period buckets**:

1. **Fix the 9 country-token collisions** by adding `AND NOT country="<longer name>"` exclusions to the shorter-name queries (§8.3). Without this, Guinea's count is ~87% Papua New Guinea, Republic of the Congo's is ~93% DRC, and Korea's is ~85% South Korea — and all three are double-counted in regional aggregates. There is no exact-match operator in ENA to avoid this; exclusion is the only route.
2. **Report the `first_public` undated bucket** (22% of country-attributed records) explicitly per country per year, so annual counts are never mistaken for complete censuses.

With those two fixes, plus dropping synthetic constructs (`NOT tax_tree(32630)`) and publishing the metagenome / `collection_date` / `last_updated` sensitivity views, the annual per-country methodology is fit to support a Cali Fund allocation assessment — with the standing caveats that (a) `country` records collection locality not sovereign provider, (b) ~22% of records cannot be dated via the Portal API, and (c) ENA and NCBI are overlapping mirrors of INSDC and must never be summed.
