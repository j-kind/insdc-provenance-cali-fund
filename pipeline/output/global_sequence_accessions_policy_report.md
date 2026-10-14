# Global Variation in Sequence Accessions Over Time: Implications for the Cali Fund

**Date:** 13 October 2026

---

## 1. Executive summary

This report examines global variation in the deposition of non-human genetic sequence records in public databases, with a focus on the distribution of those records across countries and over time. The findings are directly relevant to discussions under the Convention on Biological Diversity (CBD) regarding the multilateral mechanism for benefit-sharing from digital sequence information (DSI), including the Cali Fund established at COP16.

The analysis is based on 30,313,212 non-human sequence records held in the European Nucleotide Archive (ENA), the European mirror of the International Nucleotide Sequence Database Collaboration (INSDC). Records were counted by country of collection and by year of first public release, covering the period from 2018 through the first ten months of 2026.

Three findings stand out:

First, the global distribution of sequence records is deeply unequal. Developed countries hold 70.4 per cent of all records that can be attributed to a sovereign country, despite accounting for only 63 of the 238 classified countries and territories in the dataset. The 47 least developed countries (LDCs) combined hold fewer records than Canada alone.

Second, this inequality is narrowing, though from a very low base. The developed-country share of annual records fell from 74.2 per cent in 2018 to 50.9 per cent in the first ten months of 2026. This shift is driven primarily by rapid growth in upper middle income countries, particularly China, rather than by broad-based gains across the developing world.

Third, a substantial proportion of records, 38.3 per cent, cannot be attributed to any country at all. This is because the country field is absent, contains a placeholder value, or records a geographic feature such as an ocean rather than a political jurisdiction. This limits the utility of database provenance as a basis for country-level allocation.

The report concludes that INSDC provenance data, while informative for understanding broad trends in global sequencing capacity, should not serve as a direct allocation criterion for the Cali Fund. The data are too incomplete, too concentrated in a small number of countries, and too distorted by the COVID-19 pandemic to support a fair and transparent allocation formula.

---

## 2. Introduction and policy context

The multilateral mechanism for benefit-sharing from DSI, agreed at COP16 in Cali, Colombia, includes a fund to which users of DSI are expected to contribute. A central question for the mechanism's operation is how to allocate those funds among eligible countries, particularly developing countries and those with high biodiversity but low sequencing capacity.

One possible basis for allocation is the geographic distribution of sequence records in public databases. Countries that are the source of many sequenced organisms might be considered to have contributed more genetic resources to the global commons and therefore deserve a larger share of benefits. Alternatively, countries with few records might be prioritised for capacity-building support.

This report tests whether INSDC provenance data could support either approach. It does not prescribe a specific allocation formula. Rather, it examines whether the underlying data are fit for that purpose by assessing their completeness, their geographic distribution, their temporal trends, and the factors that distort them.

---

## 3. Methodology

### 3.1 Data source

All counts were obtained from the European Nucleotide Archive (ENA) Portal API, which provides programmatic access to metadata for biological samples deposited in INSDC databases. ENA is the European partner of the INSDC, which also includes the DNA Data Bank of Japan (DDBJ) and the US National Center for Biotechnology Information (NCBI). The three databases exchange data daily, so counts from ENA are representative of the global INSDC holdings.

The analysis uses the sample record type, which corresponds to one record per biological sample deposited. This is the appropriate unit of analysis for provenance questions because a single sample may generate multiple sequencing runs, and counting runs would inflate the numbers.

### 3.2 Scope and filters

The analysis covers non-human records only. Three categories of records were excluded:

- Records classified under the human organism (taxonomic identifier 9606), which are not relevant to biodiversity benefit-sharing.
- Records identified as human microbiome samples, where the host organism is a human, for the same reason.
- Records classified as synthetic constructs (taxonomic identifier 32630), which do not correspond to biological genetic resources.

After applying these filters, the total record count was 30,313,212. This figure was verified by an independent query to the ENA API on the same date and matches exactly.

### 3.3 Temporal anchor

Each record was assigned to a year based on the date it was first made publicly available. This date is set by the database, not by the submitter, and is therefore a reliable indicator of when the record entered the public domain.

Not all records have a public release date. Approximately 21.5 per cent of records have no date recorded. These undated records are reported separately in an "undated" column rather than being distributed across years. This means that annual counts are partial censuses, not complete enumerations.

### 3.4 Country attribution

Each record's country of collection is recorded in a geographic location field. The analysis queried 378 distinct values found in this field, comprising 296 entries from the INSDC controlled vocabulary plus 82 additional values identified through systematic sampling of the database. These additional values include alternative country names (for example, "UK" for the United Kingdom), locality names recorded without a country prefix (for example, Japanese site names), and placeholder values (for example, "missing" or "NULL").

The database's country field uses token-based matching, meaning that a query for a short country name will match any record where that name appears as a word anywhere in the field. This creates false matches, for example when querying "Mexico" and matching records from "USA: New Mexico". Twenty collision exclusions were applied to prevent these false matches, covering nine cross-country pairs (such as Guinea matching Papua New Guinea), eight sub-national pairs (such as Mexico matching the US state of New Mexico), and three non-standard values (such as "Columbia" matching British Columbia in Canada).

Raw country-field values were then aggregated onto 267 sovereign countries. Historical names with a single successor state were mapped to the current country (for example, Zaire to the Democratic Republic of the Congo). Historical names with multiple successor states, such as the USSR and Yugoslavia, were set aside as they cannot be cleanly assigned.

### 3.5 Classification

Countries were classified using two reference datasets:

- The UN M.49 standard, which provides regional groupings, sub-regional groupings, a developed/developing classification, and flags for three vulnerability categories: least developed countries (LDCs), small island developing states (SIDS), and landlocked developing countries (LLDCs).
- The World Bank income classification, which assigns each country to one of four income groups: high income, upper middle income, lower middle income, and low income.

### 3.6 Snapshot date

All counts are a point-in-time snapshot taken on 13 October 2026. The ENA database continues to grow as new records are deposited, so counts will increase over time. The 2026 figures cover only January through October and should not be compared to full-year counts for earlier years without accounting for the partial coverage.

### 3.7 Reconciliation

The sum of all 378 country-field values was compared against the true total of attributed records (records with any country field present). The sum exceeds the true total by 1.0 per cent. This overcount is expected and is caused by records whose country field contains multiple country names, for example a record collected at a border region or an ocean shared by multiple countries. Such records are counted in both country rows. There is no evidence of undercount, which would appear as the sum falling below the true total.

---

## 4. Findings

### 4.1 Overview

Table 1 summarises the distribution of all 30,313,212 records.

**Table 1: Distribution of non-human sequence records by attribution status**

| Attribution status | Record count | Per cent of total |
|---|---|---|
| Attributed to a sovereign country | 18,987,186 | 62.6% |
| No country field present | 7,695,501 | 25.4% |
| Non-country value (oceans, placeholders) | 3,920,292 | 12.9% |
| Historical (multi-successor states) | 20,143 | 0.1% |
| Multi-country overcount | 309,910 | 1.0% |
| **Total** | **30,313,212** | **100%** |

*Notes:* The multi-country overcount is an arithmetic artefact, not a distinct category of records. It represents records counted in more than one country row because their country field contains multiple country names. The total is the verified count from the database, not the sum of the rows above.

Nearly two-thirds of records can be attributed to a sovereign country. The remaining third cannot, either because no country was recorded at all (25.4 per cent) or because the recorded value is a geographic feature or placeholder rather than a country (12.9 per cent). This is a critical finding for any proposal to use these data as an allocation basis: more than a third of records would be excluded from a country-level allocation formula.

### 4.2 Developed versus developing countries

Among records attributed to sovereign countries, developed countries hold 70.4 per cent and developing countries hold 29.5 per cent. A small remainder, 0.1 per cent, belongs to territories without a UN classification.

**Table 2: Annual record counts by development status**

| Year | Developed | Developing | Developed share (%) |
|---|---|---|---|
| 2018 | 384,484 | 133,652 | 74.2 |
| 2019 | 574,492 | 223,179 | 72.0 |
| 2020 | 774,188 | 331,632 | 69.9 |
| 2021 | 2,272,486 | 454,492 | 83.3 |
| 2022 | 1,899,839 | 565,962 | 77.0 |
| 2023 | 1,783,313 | 649,674 | 73.3 |
| 2024 | 998,971 | 723,822 | 58.0 |
| 2025 | 1,036,890 | 863,901 | 54.6 |
| 2026 (Jan-Oct) | 561,709 | 540,012 | 50.9 |

*Notes:* 2026 covers January through October only. Percentages are calculated on the sum of developed and developing records, excluding the small number of unclassified territories.

The developed-country share fell from 74.2 per cent in 2018 to 50.9 per cent in the first ten months of 2026. This is a genuine shift, not merely a statistical artefact. However, the trend is not smooth. The share rose sharply in 2021, reaching 83.3 per cent, before declining through 2024, 2025, and 2026.

The 2021 surge was caused by the COVID-19 pandemic. The COVID-19 Genomics UK (COG-UK) consortium alone deposited over 1.5 million SARS-CoV-2 records in 2021, all attributed to the United Kingdom. Similar surges occurred in the United States and other developed countries with large genomic surveillance programmes. This single event temporarily inflated the developed-country share by approximately 13 percentage points.

The decline from 2021 onwards reflects two forces: the winding down of pandemic surveillance in developed countries, and continued growth in developing-country sequencing, particularly from China. It is not yet clear whether the convergence visible in 2026 will be sustained once pandemic records are no longer distorting the baseline.

### 4.3 Income groups

**Table 3: Record counts by World Bank income group**

| Income group | Countries | Record count | Per cent of country total |
|---|---|---|---|
| High income | 82 | 13,806,686 | 72.7 |
| Upper middle income | 54 | 4,163,957 | 21.9 |
| Lower middle income | 52 | 684,992 | 3.6 |
| Low income | 26 | 261,334 | 1.4 |
| Unknown | 53 | 70,217 | 0.4 |

*Notes:* "Unknown" includes territories not classified by the World Bank and countries whose classification was suspended.

High-income countries dominate, holding nearly three-quarters of all country-attributed records. Upper middle income countries, led by China, hold just under a quarter. Lower middle income and low-income countries together account for only 5.0 per cent of records, despite containing 78 countries between them.

The temporal trend within income groups is revealing. Comparing the 2021 to 2023 period (the pandemic years) with the 2024 to 2026 period, upper middle income countries grew by 43 per cent on an annualised basis, while high-income countries declined by 55 per cent. This is the strongest evidence of a structural shift, as opposed to a pandemic artefact. However, the decline in high-income countries is partly the natural end of the COVID-19 surge, and the growth in upper middle income countries is driven substantially by a single country, China.

### 4.4 Vulnerable country groups

**Table 4: Record counts by vulnerability category**

| Category | Countries | Record count | Per cent of country total |
|---|---|---|---|
| LDCs | 47 | 527,519 | 2.8 |
| SIDS | 51 | 218,743 | 1.2 |
| LLDCs | 32 | 235,701 | 1.2 |

*Notes:* These categories overlap. Some countries are classified as both an LDC and an LLDC, or both an LDC and a SIDS. The percentages are individual group shares, not a combined total.

The most striking finding here is the comparison between LDCs and a single developed country. The 47 LDCs combined hold 527,519 records. Canada alone holds 530,725. The margin is thin, approximately 3,200 records, and could reverse with a single large deposition. But the comparison illustrates the scale of inequality: nearly fifty of the world's poorest countries, combined, generate fewer sequence records than one G7 economy.

The LDC share showed a brief surge in 2022, when annual records rose from 23,051 to 116,834, an increase of 407 per cent. This was driven by a small number of large projects, not by broad-based capacity growth. The following year, LDC records fell by 71 per cent, returning to a level close to their pre-surge trend. This volatility illustrates how dependent these counts are on individual projects and funding cycles.

### 4.5 Regional distribution

**Table 5: Record counts by UN region**

| Region | Countries | Record count | Per cent of country total |
|---|---|---|---|
| Europe | 49 | 7,768,889 | 40.9 |
| Americas | 53 | 5,217,623 | 27.5 |
| Asia | 50 | 4,654,034 | 24.5 |
| Africa | 58 | 688,721 | 3.6 |
| Oceania | 26 | 605,378 | 3.2 |

Europe holds 40.9 per cent of all country-attributed records, more than any other region. This is heavily influenced by the United Kingdom, which alone accounts for 4,143,928 records, or 21.8 per cent of the country total. The UK count is inflated by the COG-UK pandemic surveillance programme. Without the UK, Europe's share would fall from 40.9 per cent to approximately 19 per cent, closer to the Americas and Asia.

Africa, despite having 58 classified countries, holds only 3.6 per cent of records. This is the lowest regional share and has remained roughly constant throughout the period studied. Sub-Saharan Africa accounts for 658,822 records, or 3.5 per cent of the country total. Northern Africa accounts for the remaining 29,899 records.

At the sub-regional level, Northern Europe and Northern America together hold over half of all country-attributed records. Northern Europe alone, with 5,275,262 records, has more than eight times the combined total of Africa and Oceania.

### 4.6 Top countries

**Table 6: Top 10 countries by total record count**

| Rank | Country | Record count | Per cent of country total |
|---|---|---|---|
| 1 | United Kingdom | 4,143,928 | 21.8 |
| 2 | United States | 4,018,537 | 21.2 |
| 3 | China | 3,357,157 | 17.7 |
| 4 | Canada | 530,725 | 2.8 |
| 5 | Germany | 510,489 | 2.7 |
| 6 | Australia | 424,457 | 2.2 |
| 7 | Denmark | 403,788 | 2.1 |
| 8 | France | 388,062 | 2.0 |
| 9 | Japan | 380,094 | 2.0 |
| 10 | Spain | 331,748 | 1.7 |

Three countries, the United Kingdom, the United States, and China, account for 60.7 per cent of all country-attributed records. No other country reaches 3 per cent. This concentration is a critical consideration for any allocation formula based on these data, as it means the global picture is heavily shaped by the sequencing practices of a very small number of countries.

### 4.7 Temporal trends

Table 7 compares three periods: the pre-pandemic baseline (2018 to 2020), the pandemic years (2021 to 2023), and the post-pandemic period (2024 to 2026, with 2026 being partial).

**Table 7: Annualised record counts by period and development status**

| Group | 2018-2020 (per year) | 2021-2023 (per year) | Change | 2024-2026 (per year) | Change |
|---|---|---|---|---|---|
| Developed | 577,721 | 1,985,212 | +244% | 865,856 | -56% |
| Developing | 229,487 | 556,709 | +143% | 709,245 | +27% |
| LDCs | 10,796 | 57,817 | +436% | 22,009 | -62% |
| SIDS | 9,617 | 24,792 | +158% | 20,408 | -18% |
| LLDCs | 7,292 | 19,763 | +171% | 14,088 | -29% |

*Notes:* Each period's count is the average annual record count within that period. "Change" is the percentage change from the previous period's annual average. The 2024 to 2026 period includes only ten months of 2026 data, so the annual average is an underestimate.

The pandemic period saw dramatic growth across all groups, but the growth was far larger for developed countries (+244 per cent) than for developing countries (+143 per cent). This widened the absolute gap between the two groups, even as it temporarily increased the developed-country share.

In the post-pandemic period, developed-country records declined by 56 per cent from their pandemic peak, while developing-country records continued to grow, by 27 per cent. For the first time in the period studied, developing countries are generating more records per year than developed countries, though the 2026 figure is based on partial-year data and should be treated with caution.

The vulnerable country groups all saw their records decline from pandemic peaks. LDCs fell by 62 per cent, LLDCs by 29 per cent, and SIDS by 18 per cent. This suggests that the pandemic-era growth in these groups was project-specific and temporary, not a sign of durable capacity expansion.

---

## 5. Discussion

### 5.1 Can INSDC provenance data support a Cali Fund allocation formula?

The findings of this report suggest that INSDC provenance data, while valuable for understanding broad trends, are not suitable as a direct basis for allocating Cali Fund resources among countries. Four problems stand out.

First, more than a third of records, 38.3 per cent, cannot be attributed to any country. A further 21.5 per cent of records have no public release date, making them invisible to temporal analysis. Any allocation formula based on these data would necessarily exclude a large fraction of the global sequencing record, and the excluded fraction is not random. It reflects systematic differences in data management practices across countries and institutions.

Second, the data are dominated by three countries. The United Kingdom, the United States, and China together account for 60.7 per cent of all country-attributed records. An allocation formula based on raw counts would channel most benefits to a small number of countries that already have substantial sequencing capacity, undermining the equity objectives of the Cali Fund.

Third, the COVID-19 pandemic has severely distorted the temporal record. The United Kingdom's record count in 2021, 1.65 million, was ten times its 2020 count. This was driven almost entirely by a single genomic surveillance consortium. Any temporal trend analysis that includes the 2021 to 2023 period without controlling for pandemic effects will overstate developed-country growth and misrepresent the underlying trajectory of biodiversity sequencing.

Fourth, the country field records where a sample was collected, not who sequenced it or who deposited the record. A sample collected in Kenya but sequenced in the United Kingdom appears as a Kenyan record. This means the data may overrepresent the contribution of biodiversity-rich countries while underrepresenting the role of the institutions that actually perform and fund the sequencing. For the purposes of the Cali Fund, which is concerned with benefit-sharing from the use of DSI, this distinction matters.

### 5.2 What the data can tell us

Despite these limitations, the data do reveal several patterns that are policy-relevant.

The convergence between developed and developing countries, visible in the 2024 to 2026 data, is a genuine phenomenon. Even after accounting for the pandemic decline in developed countries, developing-country records have grown steadily, from 133,652 in 2018 to a projected full-year equivalent of approximately 648,000 in 2026. This growth is broad-based within the developing world, though China accounts for a disproportionate share.

The persistence of the Africa gap, at 3.6 per cent of records across 58 countries, is a finding that should concern policy makers. If the Cali Fund aims to build sequencing capacity in biodiversity-rich but data-poor regions, the evidence here confirms that the need is greatest in Africa. The data also show that this gap has not narrowed over the period studied, suggesting that existing incentives and mechanisms have not been sufficient to close it.

The volatility of LDC record counts, which rose by 407 per cent in a single year and then fell by 71 per cent the following year, illustrates the fragility of sequencing capacity in these countries. A single large project can dominate the national record, and when it ends, capacity effectively disappears. This is consistent with a pattern of project-dependent, non-institutionalised sequencing that the Cali Fund might seek to address.

### 5.3 The distinction between collection and contribution

A fundamental question for any DSI benefit-sharing mechanism is whether benefits should flow to the country where the genetic resource was collected or to the country that contributed the sequence to the database. The INSDC country field records the former. The submitter's country, which is also recorded in the database but was not analysed in this report, records the latter.

For the Cali Fund, the relevant question is which of these better reflects a country's contribution to the global DSI commons. A country whose biodiversity has been extensively sequenced by foreign institutions has contributed its genetic resources, but not its sequencing capacity. A country that has invested in sequencing infrastructure and deposited many records has contributed its technical capacity, but may have sequenced organisms collected elsewhere.

This report does not resolve that question. It notes, however, that the two perspectives will produce very different allocation patterns, and that the choice between them is a policy decision, not a technical one. The data can inform the decision but cannot make it.

---

## 6. Limitations

Several limitations of this analysis should be noted.

The counts are a snapshot taken on 13 October 2026. The database grows continuously, and counts will change over time. The 2026 figures are based on ten months of data and are not comparable to full-year counts for earlier years.

The country field in INSDC is populated by the submitter and is not subject to standardised validation. Some records contain locality names rather than country names, some contain placeholder values, and some contain no geographic information at all. The analysis made every effort to capture and correctly attribute all country-field values, but the 1.0 per cent overcount indicates that some records match multiple country queries, and it is possible that a small number of rare values were not identified.

The non-human filter excludes records classified as human, human microbiome, or synthetic constructs. A small number of human-associated records may remain if the host organism field was not populated, but this residual is expected to be small based on the verified total matching the independent API query.

Environmental metagenome records, which constitute approximately 27.7 per cent of the non-human total, are included in the counts. These records, which sample entire microbial communities rather than individual organisms, inflate the counts for countries with large environmental sequencing programmes. Whether they should be included in a DSI benefit-sharing context is a policy question that this report does not resolve.

The UN M.49 developed/developing classification follows the UN standard, which classifies some countries, such as the Republic of Korea, as developing despite their high income and advanced sequencing infrastructure. The World Bank income classification provides an alternative lens and is presented alongside the UN classification to allow readers to assess the sensitivity of the findings to the choice of classification.

---

## 7. Conclusion and policy implications

The evidence presented in this report supports the following conclusions.

Global sequencing capacity, as measured by the deposition of non-human records in INSDC databases, remains highly concentrated. Three countries account for over 60 per cent of all country-attributed records, and the 47 least developed countries combined account for fewer records than Canada alone. This concentration has not materially changed over the period from 2018 to 2026, though the relative shares of individual countries have shifted, partly due to the COVID-19 pandemic.

The data show a narrowing of the developed-developing gap in recent years, but this narrowing is driven primarily by China and is superimposed on a pandemic-driven surge and decline in developed-country records. It is too early to determine whether the convergence visible in 2026 will be sustained.

The high proportion of records that cannot be attributed to any country, 38.3 per cent, and the high proportion without a public release date, 21.5 per cent, mean that any allocation formula based on these data would be building on an incomplete foundation. The excluded records are not randomly distributed. They reflect systematic differences in data management, submission practices, and institutional capacity across countries.

For the Cali Fund, these findings suggest that INSDC provenance data should inform, but not determine, allocation decisions. The data are useful for identifying broad patterns of inequality, for monitoring trends over time, and for highlighting the specific needs of regions and country groups. They are not suitable as a direct input to an allocation formula because they are too incomplete, too concentrated, and too distorted by external events to produce a fair and transparent result.

A more robust approach might combine INSDC provenance data with other indicators, such as biodiversity richness (for example, species counts from GBIF), sequencing capacity (for example, the number of sequencing facilities per country), or economic need (for example, GDP per capita or LDC/SIDS/LLDC status). The Cali Fund's allocation methodology should be a matter for Parties to negotiate, informed by evidence but not determined by it.

---

*This report is based on data queried from the European Nucleotide Archive on 13 October 2026. The full methodology, including all query parameters, classification rules, and data quality checks, is available in the technical documentation accompanying this report.*
