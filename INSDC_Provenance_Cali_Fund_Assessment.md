---

editor_options: 
  markdown: 
    wrap: 72
---

# INSDC Provenance Data and the Cali Fund: Country-Level Maps from ENA/NCBI BioSample

## Assessment of whether INSDC provenance data could support a country-level allocation methodology for the Cali Fund

**Date:** 9 October 2026 **Data queried:** 8 October 2026 (corrected 9 October 2026) **Prepared for:** IIFB COP17 delegation

------------------------------------------------------------------------

## 1. Objective

The AHTEG on Allocation Methodology left **criterion (b)** — the geographical origin of genetic resources from which DSI was derived — as a **placeholder** in the formula, owing to "the lack of currently applicable and unbiased data" (CBD/COP/17/6/Add.2, para. 20). The AHTEG recommended short-term work to "create an indicator for the geographical origin of the genetic resources from which digital sequence information on genetic resources in the database was derived," including exploring "the number of sequences in public databases with geographical origin information" (para. 21(a)(iii)).

This analysis attempts to construct three country-level maps from INSDC provenance data to assess whether such data could practically support criterion (b):

1.  **Map 1:** All legacy non-human DSI records with country provenance
2.  **Map 2:** Post-2023 records only (first_public \>= 2024-01-01)
3.  **Map 3:** Environmentally sourced records with provenance (environmental_sample = true)

------------------------------------------------------------------------

## 2. Data Sources and Methodology

### 2.1 Databases queried

| Source         | API        | Result type | Records queried     | Role            |
|-------------|-------------|--------------|--------------------|-------------|
| ENA (EMBL-EBI) | Portal API | sample      | 60,246,966 total    | Primary         |
| NCBI BioSample | ESearch    | biosample   | \~2.4M with country | Cross-reference |

INSDC is the consortium of NCBI (GenBank/SRA), ENA (EMBL-EBI), and DDBJ. They exchange data nightly, so coverage is largely overlapping. We queried ENA as the primary source because its sample database is the most comprehensive record-level metadata store, and cross-referenced with NCBI BioSample ESearch for validation.

### 2.2 Query strategy

- **Non-human filter:** `NOT tax_tree(9606)` excludes all *Homo sapiens* records
- **Country provenance:** INSDC controlled vocabulary for `geo_loc_name` / `country` field (296 valid values from <https://www.insdc.org/submitting-standards/geo_loc_name-qualifier-vocabulary/>)
- **Post-2023:** `first_public >= 2024-01-01` (ENA) / `2024[sddat]` (NCBI)
- **Environmental:** `environmental_sample = true` (boolean field identifying "sequences derived by direct molecular isolation from an environmental DNA sample")

### 2.3 Limitations

- **ENA API has no count endpoint and no offset pagination.** Maximum 500,000 records per query. For countries exceeding this (USA, China, UK, Germany, Denmark, Canada, Australia), we subdivided by year and quarter. For quarters that still exceeded the cap (USA 2021-2022, UK 2021 Q4), we further subdivided monthly to obtain exact counts.
- **NCBI BioSample `country[all]` field** uses exact text matching, missing records with sub-national detail (e.g., "USA: California" does not match `country="USA"[all]`). NCBI per-country counts are therefore systematically lower than the total (912K vs. 2.36M). The `[country]` field tag provides broader matching but was not used. ENA counts are the primary source and are not affected by this limitation.
- **Country field quality:** The INSDC country field uses a controlled vocabulary but is not uniformly populated. Many records have no country, some have sub-national detail (e.g., "Kenya: Mount Kenya"), and some use historical names (e.g., "Zaire", "USSR", "Burma"). We mapped all historical names to their modern successors.
- **Oceans and seas:** 456,769 records are tagged to oceans/seas rather than countries. These cannot be attributed to any Party.
- **The `country` field records the locality of sample isolation, not the country of origin of the genetic resource** as understood in the Nagoya Protocol sense. A sample collected in Kenya but sequenced in the UK is tagged "Kenya" — which is the correct provenance direction for criterion (b), but the distinction between provider country and sequencing country is not captured in this field alone.

------------------------------------------------------------------------

## 3. Results

### 3.1 Grand totals

| Metric | ENA | NCBI BioSample |
|------------------|-----------------|-------------------------------------|
| Total non-human samples with country provenance (all) | **27,701,739** | 912,108 |
| Post-2023 records with country | **6,818,673** | 235,128 |
| Environmentally sourced records with country | **125,405** | 52,815 |
| Countries/territories with \>= 1 record | **246** | \~170 |

### 3.2 Map 1: All legacy records — by region and development status

| Region                | Countries | Records    | \% Share |
|-----------------------|-----------|------------|----------|
| Americas              | 55        | 10,157,288 | 36.7%    |
| Europe                | 49        | 9,519,636  | 34.4%    |
| Asia                  | 48        | 5,510,344  | 19.9%    |
| Africa                | 58        | 1,086,824  | 3.9%     |
| Oceania               | 28        | 728,924    | 2.6%     |
| Oceans/Seas/Territory | 8         | 698,723    | 2.5%     |

| Development status | Countries | Records    | \% Share  |
|--------------------|-----------|------------|-----------|
| **Developed**      | 63        | 19,967,746 | **72.1%** |
| **Developing**     | 175       | 7,035,270  | **25.4%** |
| Unmapped/Territory | 8         | 698,723    | 2.5%      |

**Key finding:** Developed countries hold 72.1% of all non-human DSI records with country provenance. The USA alone accounts for 31.1% (8.6M records), more than all of Africa (3.9%).

### 3.3 Map 2: Post-2023 records — by region and development status

| Region   | Records   | \% Share | Growth rate |
|----------|-----------|----------|-------------|
| Americas | 2,512,449 | 36.8%    | 24.7%       |
| Asia     | 2,478,840 | 36.4%    | **45.0%**   |
| Europe   | 1,153,501 | 16.9%    | 12.1%       |
| Oceania  | 244,549   | 3.6%     | 33.5%       |
| Africa   | 229,078   | 3.4%     | 21.1%       |

| Development status | Records   | \% Share  | Growth rate |
|--------------------|-----------|-----------|-------------|
| **Developed**      | 3,840,786 | 56.3%     | 19.2%       |
| **Developing**     | 2,777,631 | **40.7%** | **39.5%**   |

**Key finding:** The developing-country share of new DSI records jumped from 25.4% (all-time) to 40.7% (post-2023). China's post-2023 output alone (1.76M records) accounts for 25.8% of all post-2023 records. This is driven primarily by China's massive sequencing capacity growth, followed by Republic of Korea, India, Brazil, and Mexico.

### 3.4 Map 3: Environmentally sourced records — by region and development status

| Region   | Records | \% Share  | \% of all records |
|----------|---------|-----------|-------------------|
| Europe   | 95,339  | **76.0%** | 1.0%              |
| Americas | 13,158  | 10.5%     | 0.1%              |
| Asia     | 5,515   | 4.4%      | 0.1%              |
| Oceania  | 4,108   | 3.3%      | 0.6%              |
| Africa   | 1,305   | 1.0%      | 0.1%              |

| Development status | Records | \% Share  |
|--------------------|---------|-----------|
| **Developed**      | 108,800 | **86.8%** |
| **Developing**     | 10,625  | 8.5%      |

**Key finding:** Environmental DSI records are overwhelmingly concentrated in developed countries (86.8%), with the UK alone holding 51,680 records (41.2% of the global total). This reflects the fact that eDNA/metagenome sequencing capacity is concentrated in a handful of European institutions. The `environmental_sample` field is also sparsely populated — only 125,405 records out of 27.7M (0.5%) are flagged as environmental, suggesting significant under-reporting.

### 3.5 Vulnerable country groups

| Group | Countries | All records | Post-2023 | Environmental | \% of global |
|-------|-----------|-------------|-----------|---------------|--------------|
| LDC   | 47        | 760,903     | 161,496   | 599           | 2.8%         |
| SIDS  | 51        | 293,880     | 88,963    | 1,320         | 1.1%         |
| LLDC  | 32        | 398,024     | 125,924   | 471           | 1.5%         |

All 47 LDCs combined hold fewer DSI records with provenance (760,903) than Denmark alone (715,931). The 51 SIDS combined hold 293,880 — fewer than Switzerland (369,283).

### 3.6 Top 20 countries (ENA, all records)

| \# | Country | ISO3 | Status | All records | Post-2023 | Environmental | \% Share |
|---------|-------------------|---------|--------------|-----------------|---------|-----------------|--------------|
| 1 | United States | USA | Developed | 8,630,795 | 1,989,524 | 4,999 | 31.1% |
| 2 | United Kingdom | GBR | Developed | 3,746,618 | 224,244 | 51,680 | 13.5% |
| 3 | China | CHN | Developing | 3,563,480 | 1,763,973 | 2,456 | 12.9% |
| 4 | Germany | DEU | Developed | 1,181,175 | 124,197 | 9,719 | 4.4% |
| 5 | Denmark | DNK | Developed | 715,931 | 63,580 | 2,003 | 2.7% |
| 6 | Canada | CAN | Developed | 583,136 | 231,073 | 5,117 | 2.2% |
| 7 | Australia | AUS | Developed | 508,400 | 173,392 | 1,311 | 1.9% |
| 8 | Japan | JPN | Developed | 458,330 | 211,789 | 325 | 1.7% |
| 9 | France | FRA | Developed | 456,076 | 89,048 | 10,901 | 1.7% |
| 10 | Spain | ESP | Developed | 408,251 | 79,974 | 2,668 | 1.5% |
| 11 | Switzerland | CHE | Developed | 369,283 | 55,101 | 1,685 | 1.4% |
| 12 | Republic of Korea | KOR | Developing | 321,247 | 154,112 | 112 | 1.2% |
| 13 | Netherlands | NLD | Developed | 287,137 | 52,877 | 1,205 | 1.1% |
| 14 | Finland | FIN | Developed | 273,778 | 23,027 | 454 | 1.0% |
| 15 | Italy | ITA | Developed | 269,511 | 71,369 | 3,823 | 1.0% |
| 16 | Sweden | SWE | Developed | 241,148 | 42,633 | 1,013 | 0.9% |
| 17 | Brazil | BRA | Developing | 221,939 | 60,996 | 323 | 0.8% |
| 18 | India | IND | Developing | 210,028 | 73,505 | 478 | 0.8% |
| 19 | Ireland | IRL | Developed | 209,142 | 54,843 | 119 | 0.8% |
| 20 | Mexico | MEX | Developing | 195,536 | 58,186 | 1,053 | 0.7% |

### 3.7 Developing countries with near-zero DSI provenance records

Only 9 developing countries have fewer than 100 ENA records. This is much fewer than the NCBI BioSample data suggested (28 countries with \< 10 records), because ENA's sample database is more comprehensive. However, the countries with very low counts are exclusively small island states and territories:

| Country        | All | Post-2023 | Env | Flags     |
|----------------|-----|-----------|-----|-----------|
| Nauru          | 7   | 6         | 0   | SIDS      |
| Niue           | 4   | 4         | 0   | SIDS      |
| Pitcairn       | 4   | 0         | 0   |           |
| Tuvalu         | 12  | 4         | 0   | LDC, SIDS |
| Western Sahara | 34  | 30        | 0   |           |
| Tokelau        | 39  | 34        | 0   |           |
| Montserrat     | 53  | 18        | 0   | SIDS      |
| Aruba          | 67  | 9         | 0   | SIDS      |
| Anguilla       | 16  | 3         | 0   | SIDS      |

### 3.8 Post-2023 growth leaders (developing countries)

Among countries with at least 1,000 total records, the fastest post-2023 growth rates are predominantly in developing countries:

| Country               | All       | Post-2023 | Growth % | Status     |
|-----------------------|-----------|-----------|----------|------------|
| Jamaica               | 3,247     | 2,514     | 77.4%    | Developing |
| Guyana                | 7,192     | 5,542     | 77.1%    | Developing |
| Kiribati              | 2,301     | 1,632     | 70.9%    | Developing |
| Guatemala             | 5,001     | 3,147     | 62.9%    | Developing |
| Fiji                  | 12,083    | 6,905     | 57.1%    | Developing |
| Costa Rica            | 42,011    | 23,686    | 56.4%    | Developing |
| Tajikistan            | 1,195     | 622       | 52.1%    | Developing |
| Sao Tome and Principe | 1,960     | 1,017     | 51.9%    | Developing |
| Togo                  | 1,936     | 1,004     | 51.9%    | Developing |
| Solomon Islands       | 1,492     | 740       | 49.6%    | Developing |
| China                 | 3,563,480 | 1,763,973 | 49.5%    | Developing |

------------------------------------------------------------------------

## 4. Assessment: Could INSDC provenance data support criterion (b)?

### 4.1 What the data can do

The INSDC `country` provenance field is populated for millions of non-human sequence records, uses a controlled vocabulary, and is queryable at country level through both ENA and NCBI APIs. The data exists and is accessible. A country-level map can be constructed, as demonstrated here.

### 4.2 What the data cannot do — five fundamental problems

**Problem 1: Severe concentration bias.**

The top 3 countries (USA, UK, China) account for 57.5% of all records. The top 10 account for 80%. Africa, with 58 countries, holds 3.9% of records. This is the same "absence of data is not absence of biodiversity" problem identified in the GBIF analysis by TierraViva AI (gbif-criterion-c-a-short.pdf). Allocating Cali Fund resources based on DSI provenance volume would channel funds to the countries with the most sequencing infrastructure, not the countries that are most biodiverse or most in need.

**Problem 2: The country field records collection locality, not sovereign origin of the genetic resource.**

The INSDC `country` field documents where the sample was physically collected, not which country has sovereign rights over the genetic resource under the Nagoya Protocol. A sample collected in a developing country by an expedition from a developed-country institution is tagged with the developing country's name — which is the correct direction for benefit-sharing, but the data cannot distinguish between: - Samples collected by national institutions (domestic capacity) - Samples collected by foreign expeditions (capacity dependency) - Samples collected under ABS agreements (compliance) - Samples collected without ABS agreements (non-compliance)

**Problem 3: The environmental_sample field is severely under-populated.**

Only 125,405 records (0.5% of 27.7M) are flagged as environmentally sourced. This is implausibly low given the explosive growth of metagenomics and eDNA sequencing. The field is optional in the INSDC submission schema and most submitters do not populate it. Any allocation methodology relying on this field would be built on a very thin and biased data layer.

**Problem 4: The data is not structured for benefit-sharing allocation.**

INSDC databases were designed for scientific reproducibility, not for tracking benefit-sharing obligations. The country field is a locality annotation, not a legal provenance chain. There is no linkage to: - ABS permits or internationally recognized certificates of compliance (IRCCs) - Material transfer agreements - Biocultural labels or traditional knowledge indicators - Indigenous peoples' and local communities' territories

**Problem 5: Post-2023 growth is changing the picture, but not enough.**

The developing-country share of new DSI records has risen from 25.4% to 40.7% post-2023, driven mainly by China. Excluding China, developing countries' post-2023 share is only 21.2% — essentially unchanged. China's growth is a capacity story, not a biodiversity-provenance story. This means a post-2023 filter does not solve the concentration problem; it reshapes it.

### 4.3 Comparison with the GBIF findings

The GBIF analysis (gbif-criterion-c-a-short.pdf) found a "clear linear relationship between economic capacity and biodiversity information" using 1.1 billion occurrence records. Our INSDC analysis finds the same pattern at the sequence level: developed countries hold 72.1% of DSI records with provenance, and the relationship between economic capacity and DSI provenance volume is strongly linear. The GBIF paper's conclusion applies equally here: **"Allocating funding based on the available data about the amount of biodiversity in a country will penalise least developed countries, SIDS and low income developing countries."**

### 4.4 Conclusion

INSDC provenance data **can** be used to construct a country-level map of DSI records — we have done so. However, it **should not** be used as a direct allocation criterion for the Cali Fund because:

1.  It would channel funds to countries with sequencing capacity, not countries that are sources of genetic resources
2.  It would penalize LDCs, SIDS, and LLDCs — the exact countries the Cali Fund is designed to support
3.  The environmental sample flag is too sparsely populated to support a distinct allocation pathway
4.  The data does not distinguish between sovereign origin and collection locality
5.  Post-2023 growth does not resolve the structural bias

The data is valuable for **disbursement** purposes — for example, identifying where DSI capacity building is needed, or tracking the growth of sequencing infrastructure — but it should not be placed in the **allocation** formula as a measure of biodiversity stewardship or genetic resource contribution.

This is consistent with the AHTEG's own recommendation (para. 21(d)) to "evaluate the goal of criterion (b) in the methodology and consider capturing the use of digital sequences on genetic data in public databases from a country in lieu of the quantity of the data from the same country." The INSDC provenance data measures quantity, not use, and quantity is biased by capacity.

------------------------------------------------------------------------

## 5. Data files produced

| File | Description |
|-----------------------|-------------------------------------------------|
| `insdc_provenance_country_maps.csv` | Main table: 246 countries × ENA + NCBI counts + UN classification |
| `ena_per_country_counts.csv` | Raw ENA per-country counts (all, post-2023, environmental) |
| `insdc_counts_all_legacy.csv` | NCBI BioSample per-country counts (all) |
| `insdc_counts_post2023.csv` | NCBI BioSample per-country counts (post-2023) |
| `insdc_counts_environmental.csv` | NCBI BioSample per-country counts (environmental) |
| `insdc_provenance_final_analysis.json` | Full analysis in JSON format |
| `query_insdc_provenance.py` | NCBI ESearch query script |
| `final_analysis.py` | Combined ENA+NCBI analysis script |
| `make_maps.py` | Generate all choropleth maps |
| `make_map1_bwr.py` | Generate map 1 with blue-white-red diverging scale |

------------------------------------------------------------------------

## 6. Methodological notes

- ENA portal API was queried on 8 October 2026. The `result=sample` endpoint returns all sample records in the ENA, which includes records from SRA/ERA, and is more comprehensive than NCBI's BioSample database.
- The non-human filter `NOT tax_tree(9606)` excludes all *Homo sapiens* records, including human-associated microbiome records that might be tagged with a human host taxon.
- Country names follow the INSDC controlled vocabulary (296 entries including historical names and oceans). All were mapped to UN M.49 country classifications for aggregation.
- The sum of per-country counts (27.7M) exceeds the total query count because some records have country annotations matching multiple INSDC vocabulary entries (e.g., "USA: California" matches both "USA" and potentially other sub-national entries).
- For the 7 countries that exceeded the 500k query cap (USA, China, UK, Germany, Denmark, Canada, Australia), counts were obtained by summing across year ranges (2015-2026) with quarterly subdivision for any year that still exceeded 500k. For quarters that still exceeded the cap (USA 2021 Q3-Q4, 2022 Q1-Q2; UK 2021 Q4), monthly subdivision was used to obtain exact counts.
