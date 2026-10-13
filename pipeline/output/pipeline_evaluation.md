# Pipeline and Analysis Evaluation

**Evaluator:** Independent subagent evaluation
**Date:** 2026-10-12 (live API verification)
**Scope:** Pipeline correctness, aggregation correctness, data quality, analysis report quality, statistical practice, completeness

---

## 1. Summary

The pipeline is a well-conceived and largely sound effort to count non-human DSI records in INSDC/ENA per country per year for Cali Fund allocation assessment. The core methodology — ENA `/count` with `first_public` temporal anchor, non-human filter, and collision exclusions — is correct and was verified against the live ENA API. The analysis report is policy-relevant and its headline conclusions are defensible.

However, the evaluation identified **four significant issues** that affect data accuracy and one **reproducibility gap**:

1. **Missed collision pair (HIGH):** Georgia does not exclude "South Georgia and the South Sandwich Islands," causing 1,655 records (100% of South Georgia) to be double-counted in both Georgia (Asia) and South Georgia (Americas).
2. **Temporal identity failure (HIGH):** The "all" column includes ~1.44 million 2026 records not captured in any year column (2018–2025), making the methodology's claim that `pre_2018 + sum(years) + undated = all` false for 234 of 270 country rows.
3. **Hardcoded key findings with stale numbers (MEDIUM):** Three key findings in the analysis report contain numbers that do not match the computed tables in the same report (+212% vs +245%, +1148% vs +407%, +55% vs +59%).
4. **Reproducibility gap (MEDIUM):** The provided `query_annual_counts.py` script only queries 296 INSDC vocab countries, but the output `annual_counts.csv` has 362 rows including 65 non-vocab values with their own collision exclusions (Columbia→Canada, Congo→RoC/DRC, Antarctic→Antarctica). These non-vocab queries are not in the script.

**Overall assessment:** The pipeline is fit for its stated purpose — assessing whether INSDC provenance data *could* support a Cali Fund allocation methodology — with appropriate caveats. The conclusion that INSDC provenance data should not be used as a direct allocation criterion is well-supported by the evidence (36% effectively unattributed, 21.5% undated, collection-locality vs sovereign-provider mismatch, COVID-19 distortion). The issues found are correctable and do not change the fundamental conclusion, but they should be fixed before the data is used for any quantitative allocation formula.

---

## 2. Pipeline Issues Found

### 2.1 Missed collision pair: Georgia / South Georgia (HIGH)

**Finding:** `country="Georgia"` matches "South Georgia and the South Sandwich Islands" because "Georgia" appears as a word-boundary token after "South " in that name. The current exclusion (`AND NOT country="USA"`) removes US state of Georgia records but does NOT remove South Georgia records.

**Live API verification:**
```
Georgia ∩ South Georgia: 1,655  (= 100% of South Georgia's records)
Georgia clean (excl USA only): 15,926  (current pipeline value)
Georgia clean (excl USA + South Georgia): 14,271  (correct value)
```

**Impact:**
- Georgia (country) is overcounted by 1,655 records (10.4% inflation: 15,926 vs true 14,271)
- South Georgia's 1,655 records are double-counted: once in South Georgia's own row (Americas) and once in Georgia's row (Asia)
- Regional totals are affected: Asia is overcounted by 1,655; Americas is overcounted by 1,655 (from the South Georgia row, which is correct, but the Georgia row also counts them)
- The grand total overcount (−0.5%) includes this double-counting

**Fix:** Add `'Georgia': ['USA', 'South Georgia and the South Sandwich Islands']` to `COLLISION_EXCLUSIONS` in `query_annual_counts.py`.

### 2.2 Temporal identity failure: 2026 records missing from year columns (HIGH)

**Finding:** The year columns cover 2018–2025 (`first_public >= YYYY-01-01 AND first_public < YYYY+1-01-01`), but the "all" column is queried with no date filter and includes records with `first_public` in 2026 (January–October 2026, since the run date is 2026-10-12). The methodology (§4.2) explicitly claims:

> **`pre_2018 + sum(years) + undated = all`** for each row. This identity holds exactly.

This is **false**. The identity fails for 234 of 270 country rows in `country_annual_counts.csv`.

**Live API verification:**
```
2026 total records (first_public in 2026): 1,441,401
USA 2026 records: 284,890  (= exactly the gap between USA's slice sum and USA's "all")
Total gap (all - slices): 1,451,345  (≈ 2026 records + multi-country overcount)
```

**Impact:**
- The "all" column (used for total counts, percentage shares, and the LDC-vs-Canada comparison) includes ~1.44M 2026 records
- The year columns (used for temporal trends and growth rates) do not include 2026 records
- This creates a systematic inconsistency: totals include 2026, trends don't
- The methodology's identity claim is incorrect and misleading

**Fix:** Either (a) add a 2026 year column, or (b) filter the "all" query to `first_public < 2026-01-01 OR NOT first_public >= 1900-01-01` to exclude 2026 records, or (c) correct the methodology to state that "all" includes records beyond the year-column range.

### 2.3 Reproducibility gap: script does not produce the output (MEDIUM)

**Finding:** The provided `query_annual_counts.py` script loads 296 countries from `insdc_countries_clean.txt` and queries only those, plus unattributed and attributed-total rows. This would produce 298 rows. But `annual_counts.csv` has 362 rows, including 65 non-vocab values (Columbia, Congo, UK, England, Scotland, Wales, Cote d'Ivoire, GAZ, oceans/seas, Japanese/Chinese localities, etc.) with their own collision exclusions.

The non-vocab collision exclusions are NOT in the script's `COLLISION_EXCLUSIONS` dictionary. For example:
- `Columbia` was queried with `AND NOT country="Canada"` (clean count 14,602 = raw 38,348 − 23,746 Canada overlap)
- `Congo` was queried with `AND NOT country="Republic of the Congo" AND NOT country="Democratic Republic of the Congo"` (clean count 11 = raw 17,438 − 17,427 RoC overlap)
- `Antarctic` was queried with `AND NOT country="Antarctica"` (clean count 2,218)

**Live API verification:**
```
Columbia raw: 38,348; Columbia ∩ Canada: 23,746; Columbia clean: 14,602 ✓
Congo raw: 17,438; Congo ∩ RoC: 17,427; Congo clean: 11 ✓
Antarctic raw: 6,437; Antarctic ∩ Antarctica: 4,219; Antarctic clean: 2,218 ✓
```

**Impact:** Running the provided script would NOT reproduce the output data. The non-vocab query logic is undocumented in the code.

**Fix:** Add the non-vocab values and their collision exclusions to the script (or to a separate config file), so the script is self-contained and reproducible.

### 2.4 Non-human filter: robust (VERIFIED)

The filter `NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)` was verified:
- Grand total: **30,313,212** (live API, matches methodology exactly)
- `NOT tax_tree(9606)` excludes 15,271,288 human organism records
- `NOT host_tax_id=9606` excludes 10,092,277 human microbiome records
- `NOT tax_tree(32630)` excludes 86,919 synthetic constructs
- The residual leak (human-microbiome records with missing `host_tax_id`) is acknowledged in the methodology and is expected to be small

### 2.5 Collision exclusions: 17 pairs verified, 1 missed

All 17 documented collision exclusions were verified as correctly applied:

| Pair | Raw | Clean | Verified |
|------|-----|-------|----------|
| Guinea (excl PNG, EqG, G-B) | 24,760 | 2,996 | ✓ |
| Korea (excl SK, NK) | 194,950* | 18,625 | ✓ |
| Sudan (excl South Sudan) | 2,899 | 2,877 | ✓ |
| Georgia (excl USA) | 48,511 | 15,926 | ✓ (but missing South Georgia exclusion) |
| Mongolia (excl China) | 46,408 | 14,642 | ✓ |

*Korea raw figure from earlier evaluation; current live count differs due to archive growth.

**Confirmed non-collisions** (no exclusion needed):
- Niger / Nigeria: overlap 161 (genuine multi-country records, not token collision)
- India / Indian Ocean: overlap 16 (genuine multi-country)
- Dominica / Dominican Republic: overlap 0

**Missed collision: Georgia / South Georgia** — see §2.1 above.

### 2.6 Temporal anchor: correctly used (VERIFIED)

- `first_public` date-range queries work correctly on `/count`
- 2024 total: **2,398,672** (live, matches methodology)
- 2025 total: **2,527,321** (live, matches methodology)
- Undated: **6,521,380** (live, matches methodology)
- `NOT first_public>=1900-01-01` correctly captures records with no `first_public`

---

## 3. Aggregation Issues

### 3.1 Congo duplicate (MEDIUM)

**Finding:** "Congo" (bare, 11 records) and "Republic of the Congo" (1,596 records) appear as **separate rows** in `country_annual_counts.csv`, both with `iso3=COG`. The `COUNTRY_MAPPING` dict does not include `'Congo': 'Republic of the Congo'`, so bare "Congo" is treated as a distinct canonical country.

**Impact:**
- The country count is inflated by 1 (270 instead of 269)
- The Africa region counts 59 "countries" but one is a duplicate
- Record totals are correct (11 + 1,596 = 1,607 for the combined entity), but the split is confusing
- Any analysis that counts unique countries per region will overcount

**Fix:** Add `'Congo': 'Republic of the Congo'` to `COUNTRY_MAPPING` in `aggregate_countries.py`.

### 3.2 Line Islands not mapped to Kiribati (LOW)

**Finding:** "Line Islands" (186 records) is in the INSDC vocab and appears in `annual_counts.csv`, but is NOT in `COUNTRY_MAPPING` or `NON_COUNTRY`. It is treated as a separate canonical country with no UN M.49 classification (dev_status=Unknown, no ISO3, no region).

The Line Islands are an integral part of Kiribati (not a disputed territory). They should be mapped to Kiribati.

**Impact:** 186 records are excluded from the Kiribati total and from all regional/income aggregations (classified as "Unknown").

**Fix:** Add `'Line Islands': 'Kiribati'` to `COUNTRY_MAPPING`.

### 3.3 Turkiye referenced but not in data (LOW)

**Finding:** `COUNTRY_MAPPING` includes `'Turkiye': 'Turkey'` and the methodology (§7.3) claims "Turkiye | Turkey | 2,608 records." However, "Turkiye" does NOT appear in `annual_counts.csv` or `country_mapping_audit.csv`. It was apparently never queried, or its row was lost.

**Impact:** Up to ~2,608 Turkish records submitted under the Turkish-language name "Turkiye" may be missing from the Turkey total. The methodology document references data that doesn't exist in the output.

**Fix:** Query `country="Turkiye"` and add the results to `annual_counts.csv`, or remove the reference from the methodology if the count is zero.

### 3.4 Ocean/sea contamination of country counts (LOW–MEDIUM)

**Finding:** When a country name appears as a token in an ocean/sea name, the country query captures those ocean records. This affects:

| Country | Contaminating ocean | Overlapping records | % of country total |
|---------|--------------------|--------------------|--------------------|
| China | South China Sea + East China Sea | ~24,127 | 0.7% |
| Japan | Japan Sea + Sea of Japan | ~949 | 0.3% |
| Greenland | Greenland Sea | 116 | 0.7% |

The methodology (§7.4) documents this as "captured by" the country query, but does not flag it as a data quality issue. These ocean records inflate the country counts and are not separately identified or excludable.

**Impact:** Small but systematic inflation of counts for countries whose names appear in ocean names. China's count is the most affected (~24,127 records).

**Fix:** For affected countries, add `AND NOT country="South China Sea"` etc. to the country query. Or document this as an accepted limitation with quantified impact.

### 3.5 UN M.49 and World Bank classification joins: verified correct

Spot-checked classifications against the UN M.49 source file (`unsd-country-codes.csv`):

| Country | UN dev_status | UN region | WB income | In CSV | Correct? |
|---------|--------------|-----------|-----------|--------|----------|
| South Korea | Developing | Asia/Eastern Asia | High income | ✓ | ✓ (UN classifies ROK as Developing) |
| Czechia | Developed | Europe/Eastern Europe | High income | ✓ | ✓ |
| Russia | Developed | Europe/Eastern Europe | High income | ✓ | ✓ |
| Turkey | Developing | Asia/Western Asia | Upper middle income | ✓ | ✓ |
| Venezuela | Developing | Americas/LAC | (blank) | ✓ | ✓ (WB suspended Venezuela's classification) |
| Taiwan | N/A (not in UN M.49) | — | High income | ✓ | ✓ (via fallback) |

**Note on South Korea:** Classified as "Developing" per UN M.49 standard, which is the correct application of the UN methodology. Many modern classifications consider South Korea developed, but the pipeline correctly follows the UN M.49 designation. This is a classification sensitivity, not a bug.

**Note on Venezuela:** World Bank income classification is blank because the WB suspended Venezuela's classification. Venezuela's 8,417 records fall into the "Unknown" income group. This is correct behavior.

### 3.6 LDC/SIDS/LLDC flags: verified correct, but groups overlap

The flags are correctly set from the UN M.49 file. However, the vulnerability groups are **not mutually exclusive**:

| Overlap | Records |
|---------|---------|
| LDC ∩ SIDS | 17,380 |
| LDC ∩ LLDC | 184,732 |
| SIDS ∩ LLDC | 0 |
| LDC ∩ SIDS ∩ LLDC | 0 |

The analysis report says "LDCs, SIDS, and LLDCs together account for only ~3.5%." Summing the three groups (527,333 + 218,557 + 235,701 = 981,591) double-counts the 184,732 LDC∩LLDC overlap and 17,380 LDC∩SIDS overlap. The correct unique total is 981,591 − 184,732 − 17,380 = 779,479 (4.1% of country total). The "~3.5%" figure understates the true combined total because it uses the sum of non-overlapping percentages (2.8% + 1.2% + 1.2% = 5.2%, but the report says ~3.5% which doesn't match either way — see §5.4 below).

### 3.7 Columbia → Colombia mapping: verified correct

**Live API verification:**
```
Columbia ∩ Colombia: 0  (no overlap — Columbia is NOT a misspelling that matches Colombia)
Columbia ∩ Canada: 23,746  (British Columbia records)
Columbia raw: 38,348
Columbia clean (excl Canada): 14,602 ✓
```

The Columbia → Colombia mapping is reasonable: the 14,602 clean Columbia records (after excluding Canada overlap) are likely Colombia misspellings. The 23,746 British Columbia records are correctly excluded and counted in Canada. The methodology's caveat about potential residual British Columbia records is appropriate but the overlap is well-handled.

---

## 4. Data Quality Issues

### 4.1 Annual counts reconciliation: verified

- Sum of all "all" columns in `annual_counts.csv`: **30,453,191** (matches methodology)
- True total (live API): **30,313,212**
- Overcount: 139,979 (−0.5%, from genuine multi-country records)
- This is correctly explained in the methodology as multi-country attribution

### 4.2 The −0.5% reconciliation gap: explained

The overcount comes from records whose `country` field contains tokens matching two or more row values (e.g., `USA: Canada`, `China: Japan`, `Atlantic Ocean ∩ USA`). The Georgia/South Georgia double-count (§2.1) contributes 1,655 to this overcount. The gap is small and correctly documented.

### 4.3 The 21.5% undated rate: correctly handled

- Undated total: **6,521,380** (live verified)
- The undated bucket is reported separately per country in the `undated` column
- The methodology correctly states that annual counts are partial censuses
- **However:** the undated distribution is highly uneven across countries. For example, LDCs have 44.6% undated (235,437 of 527,333) vs Canada's 14.7% (78,162 of 530,725). This means temporal comparisons between countries with very different undated rates may be biased. The methodology notes this risk but does not quantify it per country.

### 4.4 2026 records in "all" but not in year columns: see §2.2

~1.44 million 2026 records (4.7% of total) are in the "all" column but not in any year column. This is the largest data quality issue and is undocumented.

### 4.5 No unexpected zero counts found

Spot-checked countries with zero or very low counts (e.g., Belgian Congo=0, Gaza Strip=0, Ashmore and Cartier Islands=0) are legitimately zero — these are tiny territories or historical names with no records in ENA.

---

## 5. Analysis Report Issues

### 5.1 Hardcoded key findings with stale/incorrect numbers (MEDIUM)

The `analyze_disparities.py` script contains **hardcoded** numbers in key findings that do not match the computed tables in the same report. These appear to be from an earlier data run and were not updated:

| Key finding | Stated value | Actual computed value (from tables in same report) |
|-------------|-------------|---------------------------------------------------|
| #4: Developed growth 2018-2020 → 2021-2023 | +212% | **+245%** (from Annualized growth table) |
| #4: Developing growth 2018-2020 → 2021-2023 | +142% | **+145%** (from Annualized growth table) |
| #3 text: LDC surge 2021→2022 | +1148% | **+407%** (from YoY growth table) |
| #6: Upper middle income growth 2021-2023 → 2024-2025 | +55% | **+59%** (computed from income table) |
| #6: High income decline 2021-2023 → 2024-2025 | −51% | **−47%** (computed from income table) |

**Arithmetic verification:**
```
Developed: 574,615 → 1,980,438 = +245% (not +212%)
Developing: 226,613 → 554,390 = +145% (not +142%)
LDC 2021→2022: (116,833 - 23,051) / 23,051 = +407% (not +1148%)
Upper middle income: 414,035 → 659,522 = +59% (not +55%)
High income: 2,023,087 → 1,063,305 = -47% (not -51%)
```

**Fix:** Replace hardcoded numbers in key findings with computed values from the data, or use f-string interpolation referencing the actual computed values.

### 5.2 Key finding #8: percentage/definition mismatch (LOW)

The report states: "36% of all non-human records cannot be attributed to any country (oceans, seas, placeholders, GAZ identifiers, or no country field)."

The parenthetical describes the "non-country" category (oceans + placeholders + GAZ + no country), which is **37.9%** of the grand total. The "36%" figure comes from a different definition — "effectively unattributed" (no country + placeholders only, excluding oceans/seas/GAZ), which is **36.1%**. The key finding mixes the two definitions.

### 5.3 "~71%" vs "70.4%" (LOW)

The key finding text says "Developed countries dominate with ~71% of country-attributed records." The table shows 70.4%. Rounding 70.4% to the nearest whole number gives 70%, not 71%. Minor imprecision in hardcoded text.

### 5.4 Vulnerability group "~3.5%" claim (LOW)

The key finding says "LDCs, SIDS, and LLDCs together account for only ~3.5% of country-attributed records." The individual shares are 2.8% + 1.2% + 1.2% = 5.2% (sum of non-overlapping). The unique combined total (excluding overlaps) is 4.1%. The "~3.5%" figure doesn't match either calculation and appears to be a stale hardcoded value.

### 5.5 LDC vs Canada comparison: accurate but fragile (VERIFIED)

**Finding:** "47 LDCs combined have fewer records than Canada alone (527,333 vs 530,725)."

**Verification:** LDC total = 527,333, Canada = 530,725. 527,333 < 530,725. **Correct.**

**Caveats:**
- The margin is extremely thin: 3,392 records (0.6%). This comparison could flip with a different snapshot date.
- Both totals include 2026 records (from the "all" column). If the comparison used only dated records (pre_2018 + 2018–2025 + undated, excluding 2026), LDCs would have 493,362 vs Canada's 491,231 — **LDCs would have MORE records than Canada**. The comparison is sensitive to whether 2026 records are included.
- LDCs have a much higher undated rate (44.6% vs Canada's 14.7%), so the comparison on "all" records may mask different temporal patterns.

### 5.6 COVID-19 effect: correctly attributed but not isolated (MEDIUM)

The report correctly identifies the 2021–2023 surge as COVID-19 sequencing (COG-UK in the UK, US sequencing centers). However:

- The "reversal" narrative (key finding #4: "This is now reversing") conflates the **end of the COVID surge** with a **genuine shift in developing-country sequencing capacity**. The developed-country decline from 2021–2023 to 2024–2025 (−49%) is primarily because SARS-CoV-2 sequencing wound down, not because developing countries overtook developed countries.
- To assess whether there is a genuine shift, one would need to exclude SARS-CoV-2 records (e.g., `NOT tax_tree(2697049)`) and re-compute the trends. The report does not do this.
- The UK count (4,109,861) is 81% from 2021–2023 (COVID years), confirming massive COVID distortion. The report acknowledges this in caveats but does not provide a non-COVID sensitivity view.

### 5.7 Growth rate calculations: verified correct in tables

All growth rates in the **tables** (YoY growth, annualized period growth) were verified correct:

| Metric | Table value | Computed value | Match? |
|--------|------------|---------------|--------|
| Developed 2018→2019 | +49% | (569,766-382,875)/382,875 = +49% | ✓ |
| Developed 2020→2021 | +194% | (2,268,141-771,203)/771,203 = +194% | ✓ |
| Developed period growth | +245% | (1,980,438-574,615)/574,615 = +245% | ✓ |
| Developing period growth | +145% | (554,390-226,613)/226,613 = +145% | ✓ |
| LDC 2021→2022 | +407% | (116,833-23,051)/23,051 = +407% | ✓ |

The tables are correct. Only the hardcoded key finding text is wrong (§5.1).

### 5.8 Percentage share calculations: verified correct

- Developed share: 13,294,736 / 18,879,030 = 70.4% ✓
- Europe share: 7,729,070 / 18,879,030 = 40.9% ✓
- Africa share: 688,721 / 18,879,030 = 3.6% ✓
- Developed share 2018: 382,875 / (382,875 + 133,279) = 74.2% ✓
- Developed share 2025: 1,024,120 / (1,024,120 + 858,291) = 54.4% ✓

### 5.9 "Northern Europe alone has more records than all of Africa and Oceania combined": verified

- Northern Europe: 5,241,195
- Africa + Oceania: 688,721 + 605,192 = 1,293,913
- 5,241,195 > 1,293,913 ✓ (4× more)

### 5.10 Conclusion on INSDC provenance for Cali Fund allocation: well-supported

The report's conclusion that "INSDC provenance data should not be used as a direct Cali Fund allocation criterion" is well-supported by the evidence:
- 36% of records effectively unattributed (no country or placeholder)
- 21.5% of records undated (no `first_public`)
- `country` records collection locality, not sovereign provider of genetic resources
- COVID-19 massively distorts temporal trends (UK alone has 4.1M records, 81% from COVID years)
- Developed countries hold 70.4% of records; 47 LDCs combined have fewer than Canada alone
- Environmental metagenomes (27.7%) inflate counts for countries with large environmental programs

These findings collectively demonstrate that INSDC provenance data is too noisy, incomplete, and biased to serve as a direct allocation formula. The conclusion is appropriate and defensible.

---

## 6. Statistical Concerns

### 6.1 Reproducibility: partially compromised

- The query script (`query_annual_counts.py`) does not reproduce the output (§2.3). Non-vocab queries and their exclusions are missing.
- The INSDC vocabulary file, UN M.49 file, and WB file are provided as static inputs, which is good.
- The run timestamp (2026-10-12) is documented, but counts are a point-in-time snapshot and drift daily.
- Query strings are pinned in the script for the 296 vocab countries but not for the 65 non-vocab values.

### 6.2 COVID-19 surge biases temporal trends (MEDIUM)

The 2021–2023 period is massively distorted by COVID-19 genomic surveillance:
- UK 2021: 1,591,040 records (vs 162,561 in 2020 — a 10× jump)
- The developed-country annual average grew from 574,615 (2018–2020) to 1,980,438 (2021–2023), but most of this growth is SARS-CoV-2 sequencing, not a genuine increase in biodiversity DSI
- Any temporal trend analysis that includes 2021–2023 without controlling for COVID-19 will overstate developed-country growth and understate the baseline trend
- **Recommendation:** Publish a sensitivity view excluding SARS-CoV-2 (`NOT tax_tree(2697049)`) to separate COVID surveillance from underlying biodiversity sequencing trends

### 6.3 Undated bucket distribution is uneven (MEDIUM)

The 21.5% undated rate is an aggregate. The distribution across countries is highly uneven:
- LDCs: 44.6% undated (235,437 of 527,333)
- Canada: 14.7% undated (78,162 of 530,725)
- USA: 8.2% undated (325,629 of 3,964,655)

This means temporal comparisons between countries with very different undated rates are potentially biased. Countries with high undated rates will appear to have fewer records in annual counts relative to their true total. The methodology acknowledges this risk but does not publish per-country undated rates or provide a sensitivity view.

### 6.4 Confidence intervals: appropriately not used

The pipeline correctly treats counts as census values (not samples) and does not attach frequentist confidence intervals. This is the right approach — the counts are population values at a point in time, not estimates. The real uncertainty is attributional and methodological, as the api_evaluation.md correctly identified.

### 6.5 Environmental metagenomes: policy judgment, documented

The inclusion of environmental metagenomes (27.7% of non-human records) is a policy judgment that materially affects country rankings. The methodology documents this and provides a sensitivity view (excluding `tax_tree(408169)` drops the total to ~21.9M). This is adequate treatment.

### 6.6 Confounding variables not fully addressed

- **COVID-19:** see §6.2
- **Sequencing center concentration:** A few large sequencing centers (COG-UK, Earth Microbiome Project, etc.) can dominate a country's count. The report acknowledges this for UK/USA but does not quantify the concentration.
- **Submitter country vs collection country:** The `country` field records collection locality, not the submitter's country. A Kenyan sample sequenced in the UK appears as "Kenya" in the data. This is inherent to INSDC and is correctly caveated.
- **Overseas territories:** Territories (Greenland, Puerto Rico, French Guiana, etc.) are counted separately from their sovereign state. The report does not aggregate territories to their sovereign state, which could undercount some sovereign states and overcount the number of "countries."

---

## 7. Recommendations

### 7.1 High priority

1. **Fix the Georgia/South Georgia collision:** Add `'South Georgia and the South Sandwich Islands'` to Georgia's exclusion list. This removes 1,655 double-counted records.

2. **Fix the 2026 temporal gap:** Either add a 2026 year column, or restrict the "all" query to exclude 2026+ records, or correct the methodology's identity claim. The current state where "all" includes 2026 but year columns don't is misleading.

3. **Fix hardcoded key finding numbers:** Replace the stale hardcoded values (+212%, +142%, +1148%, +55%, −51%) in `analyze_disparities.py` with computed values from the data. The tables are correct; only the key finding text is wrong.

### 7.2 Medium priority

4. **Make the script reproducible:** Add the 65 non-vocab values and their collision exclusions to `query_annual_counts.py` (or a config file) so the script produces the full 362-row output.

5. **Map "Congo" to "Republic of the Congo":** Add `'Congo': 'Republic of the Congo'` to `COUNTRY_MAPPING` to eliminate the duplicate country row.

6. **Add a COVID-19 sensitivity view:** Publish a table excluding SARS-CoV-2 (`NOT tax_tree(2697049)`) to separate pandemic surveillance from underlying biodiversity DSI trends.

7. **Publish per-country undated rates:** Add an "undated %" column to `country_annual_counts.csv` so users can assess temporal completeness per country.

### 7.3 Low priority

8. **Map "Line Islands" to Kiribati** in `COUNTRY_MAPPING`.

9. **Verify Turkiye records:** Query `country="Turkiye"` and add to the dataset if non-zero, or remove the reference from the methodology.

10. **Quantify ocean contamination:** For China, Japan, and Greenland, document the number of ocean records included in the country count, or add exclusions for the contaminating ocean names.

11. **Fix key finding #8 percentage:** Use 37.9% (non-country) or 36.1% (effectively unattributed) consistently, not a mix.

12. **Fix vulnerability group "~3.5%" claim:** Compute the unique combined LDC+SIDS+LLDC total accounting for overlaps, or clarify that the percentages are individual group shares.

---

## 8. Verification Tests

### 8.1 Live ENA API queries executed (2026-10-12)

All queries used Python `urllib` (not `curl`, which has an OpenSSL issue on this machine) against `https://www.ebi.ac.uk/ena/portal/api/count` with `result=sample`.

| Test | Query | Result | Expected | Match? |
|------|-------|--------|----------|--------|
| Grand total | `NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)` | 30,313,212 | 30,313,212 | ✓ |
| USA | `country="USA" AND <filter>` | 3,964,655 | 3,964,655 | ✓ |
| Guinea clean | `country="Guinea" AND NOT country="Papua New Guinea" AND NOT country="Equatorial Guinea" AND NOT country="Guinea-Bissau" AND <filter>` | 2,996 | 2,996 | ✓ |
| Korea clean | `country="Korea" AND NOT country="South Korea" AND NOT country="North Korea" AND <filter>` | 18,625 | 18,625 | ✓ |
| Attributed total | `country="*" AND <filter>` | 22,617,711 | 22,617,711 | ✓ |
| Unattributed | `NOT country="*" AND <filter>` | 7,695,501 | 7,695,501 | ✓ |
| Undated | `NOT first_public>=1900-01-01 AND <filter>` | 6,521,380 | 6,521,380 | ✓ |
| 2024 total | `first_public>=2024-01-01 AND first_public<2025-01-01 AND <filter>` | 2,398,672 | 2,398,672 | ✓ |
| 2025 total | `first_public>=2025-01-01 AND first_public<2026-01-01 AND <filter>` | 2,527,321 | 2,527,321 | ✓ |
| 2026 total | `first_public>=2026-01-01 AND first_public<2027-01-01 AND <filter>` | 1,441,401 | (not in data) | **Gap confirmed** |

### 8.2 Collision pair tests

| Pair | Overlap | Collision? | Excluded in pipeline? |
|------|---------|-----------|----------------------|
| Guinea ∩ Papua New Guinea | 20,627 | Yes | ✓ |
| Georgia ∩ USA | 32,585 | Yes | ✓ |
| Georgia ∩ South Georgia | 1,655 | **Yes** | **NO — missed** |
| Mongolia ∩ China | 31,766 | Yes | ✓ |
| Sudan ∩ South Sudan | 22 | Yes | ✓ |
| Niger ∩ Nigeria | 161 | No (multi-country) | N/A |
| India ∩ Indian Ocean | 16 | No (multi-country) | N/A |
| Dominica ∩ Dominican Republic | 0 | No | N/A |
| China ∩ South China Sea | 17,870 | Yes (ocean in country) | Documented, not excluded |
| China ∩ East China Sea | 6,257 | Yes (ocean in country) | Documented, not excluded |
| Greenland ∩ Greenland Sea | 116 | Yes (ocean in country) | Documented, not excluded |
| Japan ∩ Japan Sea | 371 | Yes (ocean in country) | Documented, not excluded |
| Japan ∩ Sea of Japan | 578 | Yes (ocean in country) | Documented, not excluded |

### 8.3 Columbia/Colombia/Canada verification

| Query | Result |
|-------|--------|
| Columbia raw | 38,348 |
| Columbia ∩ Canada | 23,746 (British Columbia records) |
| Columbia ∩ Colombia | 0 (no token overlap) |
| Columbia clean (excl Canada) | 14,602 ✓ |

### 8.4 Congo verification

| Query | Result |
|-------|--------|
| Congo (bare) raw | 17,438 |
| Congo ∩ Republic of the Congo | 17,427 |
| Congo ∩ Democratic Republic of the Congo | 15,831 |
| Congo clean (excl both) | 11 ✓ |

### 8.5 Arithmetic verification

| Check | Result |
|-------|--------|
| Sum of annual_counts.csv "all" column | 30,453,191 ✓ |
| Row identity (pre_2018 + years + undated = all) | **234 of 270 rows FAIL** (2026 gap) |
| Developed share | 70.4% ✓ |
| LDC total < Canada total | 527,333 < 530,725 ✓ |
| Growth rates in tables | All verified correct ✓ |
| Key finding hardcoded numbers | **5 of 5 checked are wrong** (stale values) |

---

## 9. Conclusion

The pipeline demonstrates a thorough understanding of ENA API semantics, the INSDC country vocabulary, and the methodological challenges of using archive provenance data for policy purposes. The collision-exclusion approach is innovative and correctly handles the any-token matching behavior of ENA's `country` field. The non-human filter, temporal anchor choice, and reconciliation methodology are all sound and verified against the live API.

The analysis report's headline conclusion — that INSDC provenance data should not be used as a direct Cali Fund allocation criterion — is well-supported and defensible. The data shows severe attribution gaps (36% effectively unattributed), temporal incompleteness (21.5% undated), COVID-19 distortion, and enormous disparities (47 LDCs < Canada alone).

The issues identified (missed Georgia/South Georgia collision, 2026 temporal gap, stale hardcoded key findings, Congo duplicate, reproducibility gap) are correctable and do not change the fundamental conclusion. They should be fixed before the data is used for any quantitative application beyond the qualitative assessment already presented.
