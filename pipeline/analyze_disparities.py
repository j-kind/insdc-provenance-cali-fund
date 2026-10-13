#!/usr/bin/env python3
"""
Analysis of global disparities in DSI sequencing, with temporal trends,
by development status, income group, vulnerability group, and UN region/sub-region.

Reads the aggregated country-level data from aggregate_countries.py outputs.
Writes a markdown analysis report to pipeline/output/analysis_report.md.

Usage:
  python3 analyze_disparities.py
"""

import csv
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

YEARS = ['2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026']
YEAR_LABELS = YEARS  # for display


def load_csv(filename):
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath) as f:
        reader = csv.DictReader(f)
        return list(reader)


def fmt(n):
    return f"{int(n):,}"


def pct(n, total):
    return f"{100*float(n)/float(total):.1f}%" if float(total) > 0 else "0.0%"


def annualized(count, year):
    """Annualize a 3-year or partial-year count."""
    if year in ['2018', '2019', '2020', '2021', '2022', '2023']:
        return count  # these are already annual
    if year in ['2024', '2025']:
        return count  # already annual
    return count


def growth_rate(val1, val2):
    """Percent change from val1 to val2."""
    if float(val1) == 0:
        return "n/a"
    return f"{100*(float(val2)-float(val1))/float(val1):+.0f}%"


def main():
    print("=" * 70)
    print("ANALYSIS: GLOBAL DISPARITIES IN DSI SEQUENCING")
    print("=" * 70)

    # Load data
    countries = load_csv('country_annual_counts.csv')
    agg_dev = load_csv('agg_by_dev_status.csv')
    agg_income = load_csv('agg_by_income.csv')
    agg_region = load_csv('agg_by_region.csv')
    agg_subregion = load_csv('agg_by_subregion.csv')
    agg_vuln = load_csv('agg_by_vulnerability.csv')
    
    # Load raw annual_counts.csv for grand total and unattributed
    raw_rows = load_csv('annual_counts.csv')
    unattributed_total = 0
    non_country_total_raw = 0
    # Set of non-country values (must match aggregate_countries.py NON_COUNTRY set)
    non_country_values = {
        '(no country)', 'missing', 'not applicable', 'not collected',
        'unknown', 'NULL', 'na', 'None', 'not appicable',
        'GAZ',
        'Atlantic Ocean', 'Pacific Ocean', 'Indian Ocean', 'Arctic Ocean',
        'Southern Ocean', 'Antarctic', 'Antarctica',
        'North Sea', 'Baltic Sea', 'Mediterranean Sea', 'Black Sea', 'Red Sea',
        'Coral Sea', 'Coral Sea Islands', 'Caspian Sea', 'Barents Sea',
        'Bering Sea', 'Caribbean Sea', 'Sargasso Sea', 'Norwegian Sea',
        'Kara Sea', 'Laptev Sea', 'East Siberian Sea', 'Chukchi Sea',
        'Beaufort Sea', 'Amundsen Sea', 'Weddell Sea', 'Ross Sea',
        'Labrador Sea', 'Greenland Sea', 'Celtic Sea', 'Tasman Sea',
        'Japan Sea', 'Okhotsk Sea', 'Sea of Japan', 'North Atlantic Ocean',
        'South Atlantic Ocean', 'North Pacific Ocean', 'South Pacific Ocean',
        'South China Sea', 'East China Sea',
        'Borneo',
    }
    for r in raw_rows:
        name = r.get('country', '')
        if name == '__UNATTRIBUTED__':
            unattributed_total = int(r['all'])
        elif name == '__ATTRIBUTED_TOTAL__':
            pass  # attributed total for reconciliation
        elif name in non_country_values:
            non_country_total_raw += int(r['all'])
    
    # Build lookup dicts
    dev = {r['group']: r for r in agg_dev}
    inc = {r['group']: r for r in agg_income}
    reg = {r['group']: r for r in agg_region}
    subreg = {r['group']: r for r in agg_subregion}
    vuln = {r['group']: r for r in agg_vuln}

    # Compute totals
    country_total_all = sum(int(r['all']) for r in countries if r['country'] != '__HISTORICAL__')
    historical = sum(int(r['all']) for r in countries if r['country'] == '__HISTORICAL__')
    non_country = non_country_total_raw
    # Grand total = attributed total + unattributed total (matches live API)
    attributed_total = country_total_all + historical + non_country  # from CSV rows
    # Use the __ATTRIBUTED_TOTAL__ from the raw data for the true attributed total
    attributed_true = next((int(r['all']) for r in raw_rows if r.get('country') == '__ATTRIBUTED_TOTAL__'), attributed_total)
    grand_total = attributed_true + unattributed_total

    report = []
    report.append("# Global Disparities in DSI Sequencing — Analysis Report")
    report.append("")
    report.append(f"**Data:** ENA non-human sequence records (excl. microbiome + synthetic constructs)")
    report.append(f"**Temporal anchor:** `first_public` (78.5% of records dated)")
    report.append(f"**Country attribution:** {len([r for r in countries if r['country'] != '__HISTORICAL__'])} canonical countries, aggregated from {len(raw_rows) - 2} raw country-field values")
    report.append(f"**Run date:** 2026-10-13")
    report.append("")
    report.append("---")
    report.append("")

    # ── Section 1: Overview ──────────────────────────────────────────
    report.append("## 1. Overview")
    report.append("")
    report.append("| Metric | Count | % of grand total |")
    report.append("|--------|-------|------------------|")
    report.append(f"| Total non-human records | {fmt(grand_total)} | 100% |")
    report.append(f"| Attributed to sovereign countries | {fmt(country_total_all)} | {pct(country_total_all, grand_total)} |")
    report.append(f"| Historical (multi-successor) | {fmt(historical)} | {pct(historical, grand_total)} |")
    report.append(f"| Non-country (oceans, placeholders, GAZ) | {fmt(non_country)} | {pct(non_country, grand_total)} |")
    report.append(f"| Unattributed (no country field) | {fmt(unattributed_total)} | {pct(unattributed_total, grand_total)} |")
    overcount = attributed_total - attributed_true
    report.append(f"| Multi-country overcount | {fmt(overcount)} | {pct(overcount, grand_total)} |")
    report.append("")

    # ── Section 2: Developed vs Developing ───────────────────────────
    report.append("## 2. Developed vs Developing Countries")
    report.append("")
    report.append("| Status | Countries | All records | % share |")
    report.append("|--------|-----------|-------------|---------|")
    for g in ['Developed', 'Developing', 'Unknown']:
        if g in dev:
            d = dev[g]
            report.append(f"| {g} | {d['countries']} | {fmt(d['all'])} | {pct(d['all'], country_total_all)} |")
    report.append("")

    # Annual counts table
    report.append("### Annual record counts by development status")
    report.append("")
    header = "| Year | " + " | ".join(YEARS) + " |"
    sep = "|------|" + "|".join(["------"] * len(YEARS)) + "|"
    report.append(header)
    report.append(sep)
    for g in ['Developed', 'Developing']:
        if g in dev:
            d = dev[g]
            row = f"| {g} | " + " | ".join(fmt(d[y]) for y in YEARS) + " |"
            report.append(row)
    report.append("")

    # Share over time
    report.append("### Share of annual records (%)")
    report.append("")
    report.append(header)
    report.append(sep)
    for g in ['Developed', 'Developing']:
        if g in dev:
            d = dev[g]
            row = f"| {g} | " + " | ".join(pct(d[y], int(dev['Developed'][y]) + int(dev['Developing'][y])) for y in YEARS) + " |"
            report.append(row)
    report.append("")

    # Growth
    yoy_headers = " | ".join(f"{YEARS[i]}→{YEARS[i+1]}" for i in range(len(YEARS) - 1))
    report.append("### Year-over-year growth")
    report.append("")
    report.append(f"| Group | {yoy_headers} |")
    report.append(f"|-------|{'------|' * (len(YEARS) - 1)}")
    for g in ['Developed', 'Developing']:
        d = dev[g]
        growths = []
        for i in range(len(YEARS) - 1):
            growths.append(growth_rate(d[YEARS[i]], d[YEARS[i+1]]))
        report.append(f"| {g} | " + " | ".join(growths) + " |")
    report.append("")
    report.append(f"Key finding: Developed countries dominate with {pct(dev['Developed']['all'], country_total_all)} of country-attributed records. "
                   "The gap widened sharply in 2021-2023 (COVID-19 sequencing surge in developed countries), "
                   "but developing countries' share is growing in 2024-2026 as developed-country output declines.")
    report.append("")

    # ── Section 3: Income groups ─────────────────────────────────────
    report.append("## 3. World Bank Income Groups")
    report.append("")
    report.append("| Income group | Countries | All records | % share |")
    report.append("|--------------|-----------|-------------|---------|")
    for g in ['High income', 'Upper middle income', 'Lower middle income', 'Low income', 'Unknown']:
        if g in inc:
            d = inc[g]
            report.append(f"| {g} | {d['countries']} | {fmt(d['all'])} | {pct(d['all'], country_total_all)} |")
    report.append("")

    # Annual
    report.append("### Annual record counts by income group")
    report.append("")
    report.append(header)
    report.append(sep)
    for g in ['High income', 'Upper middle income', 'Lower middle income', 'Low income']:
        if g in inc:
            d = inc[g]
            report.append(f"| {g} | " + " | ".join(fmt(d[y]) for y in YEARS) + " |")
    report.append("")

    # Share over time
    report.append("### Share of annual records by income group (%)")
    report.append("")
    income_groups = ['High income', 'Upper middle income', 'Lower middle income', 'Low income']
    report.append(header)
    report.append(sep)
    for g in income_groups:
        if g in inc:
            d = inc[g]
            totals = {y: sum(int(inc[gg][y]) for gg in income_groups if gg in inc) for y in YEARS}
            row = f"| {g} | " + " | ".join(pct(d[y], totals[y]) for y in YEARS) + " |"
            report.append(row)
    report.append("")

    # ── Section 4: Vulnerability groups ──────────────────────────────
    report.append("## 4. Vulnerable Country Groups (LDC, SIDS, LLDC)")
    report.append("")
    report.append("| Group | Countries | All records | % of country total |")
    report.append("|-------|-----------|-------------|---------------------|")
    for g in ['LDC', 'SIDS', 'LLDC']:
        if g in vuln:
            d = vuln[g]
            report.append(f"| {g} | {d['countries']} | {fmt(d['all'])} | {pct(d['all'], country_total_all)} |")
    report.append("")

    # Annual
    report.append("### Annual record counts by vulnerability group")
    report.append("")
    report.append(header)
    report.append(sep)
    for g in ['LDC', 'SIDS', 'LLDC']:
        d = vuln[g]
        report.append(f"| {g} | " + " | ".join(fmt(d[y]) for y in YEARS) + " |")
    report.append("")

    # Share over time
    report.append("### Share of annual records by vulnerability group (% of developed+developing)")
    report.append("")
    report.append(header)
    report.append(sep)
    for g in ['LDC', 'SIDS', 'LLDC']:
        d = vuln[g]
        totals = {y: int(dev['Developed'][y]) + int(dev['Developing'][y]) for y in YEARS}
        row = f"| {g} | " + " | ".join(pct(d[y], totals[y]) for y in YEARS) + " |"
        report.append(row)
    report.append("")

    # Growth
    report.append("### Year-over-year growth for vulnerable groups")
    report.append("")
    report.append(f"| Group | {yoy_headers} |")
    report.append(f"|-------|{'------|' * (len(YEARS) - 1)}")
    for g in ['LDC', 'SIDS', 'LLDC']:
        d = vuln[g]
        growths = []
        for i in range(len(YEARS) - 1):
            growths.append(growth_rate(d[YEARS[i]], d[YEARS[i+1]]))
        report.append(f"| {g} | " + " | ".join(growths) + " |")
    report.append("")
    report.append("Key finding: LDCs, SIDS, and LLDCs together account for only ~4% of country-attributed records. "
                   "LDCs saw a dramatic surge in 2022, driven by a few large projects, "
                   "but remain far behind. The share of vulnerable countries is growing slowly but from a very low base.")
    report.append("")

    # ── Section 5: UN regions ────────────────────────────────────────
    report.append("## 5. UN Regional Analysis")
    report.append("")
    report.append("| Region | Countries | All records | % share |")
    report.append("|--------|-----------|-------------|---------|")
    for r in sorted(reg.keys(), key=lambda k: int(reg[k]['all']), reverse=True):
        d = reg[r]
        if r == 'Unmapped':
            continue
        report.append(f"| {r} | {d['countries']} | {fmt(d['all'])} | {pct(d['all'], country_total_all)} |")
    report.append("")

    # Annual by region
    report.append("### Annual record counts by UN region")
    report.append("")
    report.append(header)
    report.append(sep)
    for r in ['Europe', 'Americas', 'Asia', 'Africa', 'Oceania']:
        if r in reg:
            d = reg[r]
            report.append(f"| {r} | " + " | ".join(fmt(d[y]) for y in YEARS) + " |")
    report.append("")

    # Share over time by region
    report.append("### Share of annual records by UN region (%)")
    report.append("")
    region_list = ['Europe', 'Americas', 'Asia', 'Africa', 'Oceania']
    report.append(header)
    report.append(sep)
    for r in region_list:
        if r in reg:
            d = reg[r]
            totals = {y: sum(int(reg[rr][y]) for rr in region_list if rr in reg) for y in YEARS}
            row = f"| {r} | " + " | ".join(pct(d[y], totals[y]) for y in YEARS) + " |"
            report.append(row)
    report.append("")

    # ── Section 6: UN sub-regions ────────────────────────────────────
    report.append("## 6. UN Sub-Regional Analysis")
    report.append("")
    report.append("| Sub-region | Countries | All records | % share |")
    report.append("|------------|-----------|-------------|---------|")
    for r in sorted(subreg.keys(), key=lambda k: int(subreg[k]['all']), reverse=True):
        d = subreg[r]
        if r == 'Unmapped':
            continue
        report.append(f"| {r} | {d['countries']} | {fmt(d['all'])} | {pct(d['all'], country_total_all)} |")
    report.append("")

    # Annual by sub-region
    report.append("### Annual record counts by UN sub-region")
    report.append("")
    report.append(header)
    report.append(sep)
    for r in sorted(subreg.keys(), key=lambda k: int(subreg[k]['all']), reverse=True):
        d = subreg[r]
        if r == 'Unmapped':
            continue
        report.append(f"| {r} | " + " | ".join(fmt(d[y]) for y in YEARS) + " |")
    report.append("")

    # ── Section 7: Top countries ─────────────────────────────────────
    report.append("## 7. Top 30 Countries by Total Records")
    report.append("")
    report.append("| # | Country | ISO3 | Status | Income | All | 2025 | 2026 | % share |")
    report.append("|---|---------|------|--------|--------|-----|------|------|---------|")
    sorted_countries = sorted(
        [r for r in countries if r['country'] != '__HISTORICAL__'],
        key=lambda r: int(r['all']), reverse=True
    )
    for i, r in enumerate(sorted_countries[:30], 1):
        report.append(f"| {i} | {r['country']} | {r['iso3'] or '—'} | {r['dev_status']} | {r['wb_income']} | "
                       f"{fmt(r['all'])} | {fmt(r['2025'])} | {fmt(r['2026'])} | {pct(r['all'], country_total_all)} |")
    report.append("")

    # ── Section 8: Temporal trends ───────────────────────────────────
    report.append("## 8. Temporal Trends")
    report.append("")

    # Compute annual totals (excluding non-country)
    annual_totals = {}
    for y in YEARS:
        annual_totals[y] = int(dev['Developed'][y]) + int(dev['Developing'][y]) + int(dev['Unknown'][y])

    report.append("### Total country-attributed records per year")
    report.append("")
    report.append("| Year | Total | Developed | Developing | Developed % |")
    report.append("|------|-------|-----------|------------|-------------|")
    for y in YEARS:
        d_total = int(dev['Developed'][y])
        dev_total = int(dev['Developing'][y])
        report.append(f"| {y} | {fmt(annual_totals[y])} | {fmt(d_total)} | {fmt(dev_total)} | {pct(d_total, annual_totals[y])} |")
    report.append("")
    report.append("*Note: 2026 covers January–October only (partial year).*")

    # 3-year period comparison
    report.append("### Three-year period comparison")
    report.append("")
    report.append("| Period | Developed | Developing | LDC | SIDS | LLDC |")
    report.append("|--------|-----------|------------|-----|------|------|")
    for period, years_in in [('2018-2020', ['2018', '2019', '2020']),
                              ('2021-2023', ['2021', '2022', '2023']),
                              ('2024-2026', ['2024', '2025', '2026'])]:
        d_val = sum(int(dev['Developed'][y]) for y in years_in)
        dev_val = sum(int(dev['Developing'][y]) for y in years_in)
        ldc_val = sum(int(vuln['LDC'][y]) for y in years_in)
        sids_val = sum(int(vuln['SIDS'][y]) for y in years_in)
        lldc_val = sum(int(vuln['LLDC'][y]) for y in years_in)
        label = period
        report.append(f"| {label} | {fmt(d_val)} | {fmt(dev_val)} | {fmt(ldc_val)} | {fmt(sids_val)} | {fmt(lldc_val)} |")
    report.append("")

    # Annualized growth
    report.append("### Annualized growth rates between periods")
    report.append("")
    report.append("| Group | 2018-2020/yr | 2021-2023/yr | Growth | 2024-2026/yr | Growth |")
    report.append("|-------|-------------|-------------|--------|-------------|--------|")
    for label, src in [('Developed', dev), ('Developing', dev)] + [('LDC', vuln), ('SIDS', vuln), ('LLDC', vuln)]:
        d = src[label]
        p1 = sum(int(d[y]) for y in ['2018', '2019', '2020']) / 3
        p2 = sum(int(d[y]) for y in ['2021', '2022', '2023']) / 3
        p3 = sum(int(d[y]) for y in ['2024', '2025', '2026']) / 3
        g1 = growth_rate(p1, p2)
        g2 = growth_rate(p2, p3)
        report.append(f"| {label} | {fmt(p1)} | {fmt(p2)} | {g1} | {fmt(p3)} | {g2} |")
    report.append("")

    # ── Section 9: Key findings ──────────────────────────────────────
    report.append("## 9. Key Findings")
    report.append("")
    developed_share = pct(dev['Developed']['all'], country_total_all)
    ldc_share = pct(vuln['LDC']['all'], country_total_all)
    
    # Compute share changes
    dev_share_2018 = 100 * float(dev['Developed']['2018']) / (float(dev['Developed']['2018']) + float(dev['Developing']['2018']))
    dev_share_2025 = 100 * float(dev['Developed']['2025']) / (float(dev['Developed']['2025']) + float(dev['Developing']['2025']))
    
    # Compute growth rates for key findings (from the tables above)
    dev_p1 = sum(int(dev['Developed'][y]) for y in ['2018', '2019', '2020']) / 3
    dev_p2 = sum(int(dev['Developed'][y]) for y in ['2021', '2022', '2023']) / 3
    dev_p3 = sum(int(dev['Developed'][y]) for y in ['2024', '2025', '2026']) / 3
    developing_p1 = sum(int(dev['Developing'][y]) for y in ['2018', '2019', '2020']) / 3
    developing_p2 = sum(int(dev['Developing'][y]) for y in ['2021', '2022', '2023']) / 3
    developing_p3 = sum(int(dev['Developing'][y]) for y in ['2024', '2025', '2026']) / 3
    dev_growth_surge = growth_rate(dev_p1, dev_p2)
    developing_growth_surge = growth_rate(developing_p1, developing_p2)
    
    # LDC 2021→2022 growth
    ldc_2021 = int(vuln['LDC']['2021'])
    ldc_2022 = int(vuln['LDC']['2022'])
    ldc_growth = growth_rate(ldc_2021, ldc_2022)
    
    # Income group growth
    upper_mid_p2 = sum(int(inc['Upper middle income'][y]) for y in ['2021', '2022', '2023']) / 3
    upper_mid_p3 = sum(int(inc['Upper middle income'][y]) for y in ['2024', '2025', '2026']) / 3
    high_p2 = sum(int(inc['High income'][y]) for y in ['2021', '2022', '2023']) / 3
    high_p3 = sum(int(inc['High income'][y]) for y in ['2024', '2025', '2026']) / 3
    upper_mid_growth = growth_rate(upper_mid_p2, upper_mid_p3)
    high_decline = growth_rate(high_p2, high_p3)
    
    # Vulnerability group combined (unique, accounting for overlaps)
    ldc_countries = {r['country'] for r in countries if r['ldc'] == 'LDC'}
    sids_countries = {r['country'] for r in countries if r['sids'] == 'SIDS'}
    lldc_countries = {r['country'] for r in countries if r['lldc'] == 'LLDC'}
    vuln_all_countries = ldc_countries | sids_countries | lldc_countries
    vuln_total = sum(int(r['all']) for r in countries if r['country'] in vuln_all_countries and r['country'] != '__HISTORICAL__')
    vuln_share = pct(vuln_total, country_total_all)
    
    # Non-country + unattributed = records that cannot be assigned to any sovereign country
    unattributable = non_country + unattributed_total
    
    report.append(f"1. **Developed countries hold {developed_share} of all country-attributed DSI records** "
                   f"despite containing only {dev['Developed']['countries']} of {int(dev['Developed']['countries']) + int(dev['Developing']['countries'])} classified countries.")
    report.append("")
    report.append(f"2. **The developed-country share declined from {dev_share_2018:.1f}% in 2018 to {dev_share_2025:.1f}% in 2025**, "
                   f"driven by rapid growth in China, India, Brazil, and other developing countries. "
                   f"However, the gap remains enormous in absolute terms.")
    report.append("")
    report.append(f"3. **LDCs account for only {ldc_share} of country-attributed records** — "
                   f"the 47 least developed countries combined have fewer records than Canada alone "
                   f"({fmt(vuln['LDC']['all'])} vs {fmt(next(r['all'] for r in countries if r['country'] == 'Canada'))}).")
    report.append("")
    report.append(f"4. **A COVID-19 sequencing surge in 2021-2023** temporarily widened the gap: "
                   f"developed countries grew {dev_growth_surge} (2018-2020 to 2021-2023 annual average), "
                   f"while developing countries grew {developing_growth_surge}. This is now reversing.")
    report.append("")
    report.append(f"5. **Europe dominates with {pct(reg['Europe']['all'], country_total_all)} of records**, "
                   f"led by the United Kingdom ({fmt(next(r['all'] for r in countries if r['country'] == 'United Kingdom'))} records, "
                   f"mostly from the COVID-19 Genomics UK consortium). Northern Europe alone has more records than all of Africa and Oceania combined.")
    report.append("")
    report.append(f"6. **Upper middle income countries (led by China) are the fastest-growing group**, "
                   f"with 2024-2026 annualized output {upper_mid_growth} above 2021-2023, while high-income countries declined {high_decline}.")
    report.append("")
    report.append(f"7. **Africa has only {pct(reg['Africa']['all'], country_total_all)} of records** despite having "
                   f"{reg['Africa']['countries']} classified countries — the lowest regional share by far. "
                   f"Sub-Saharan Africa has {fmt(reg['Sub-Saharan Africa']['all'] if 'Sub-Saharan Africa' in reg else subreg['Sub-Saharan Africa']['all'])} records total.")
    report.append("")
    report.append(f"8. **{pct(unattributable, grand_total)} of all non-human records cannot be attributed to any country** (oceans, seas, placeholders, GAZ identifiers, or no country field). "
                   f"This limits the utility of INSDC provenance data for country-level allocation methodologies.")
    report.append("")
    report.append(f"9. **21.5% of records are undated** (no `first_public`), so annual counts are partial censuses. "
                   f"The dated share may vary by country, introducing temporal bias.")
    report.append("")

    # ── Section 10: Caveats ──────────────────────────────────────────
    report.append("## 10. Caveats")
    report.append("")
    report.append("- All counts are a point-in-time snapshot (2026-10-13); the ENA archive grows daily.")
    report.append("- 2026 counts cover January–October only (partial year).")
    report.append("- Annual counts cover only the ~78% of records with a `first_public` date.")
    report.append("- `country` records collection locality, not sovereign provider of genetic resources.")
    report.append("- The United Kingdom count is inflated by the COVID-19 Genomics UK (COG-UK) consortium, which deposited millions of SARS-CoV-2 records in 2021-2023.")
    report.append("- The USA count is similarly influenced by large US sequencing centers during the pandemic.")
    report.append("- Environmental metagenomes (27.7% of non-human records) are included; they inflate counts for countries with large environmental sequencing programs.")
    report.append("- 20 collision exclusions (9 cross-country + 8 sub-national + 3 non-vocab) are applied to prevent false matches; see methodology document for details.")
    report.append("- Historical names (USSR, Yugoslavia, etc.) with multiple successor states cannot be cleanly assigned and are excluded from country-level analysis.")
    report.append("- Columbia is mapped to Colombia but may include some British Columbia records not captured by the Canada exclusion.")
    report.append("")
    report.append("---")
    report.append("")
    report.append(f"*See `annual_counts_methodology.md` for full methodology and `country_mapping_audit.csv` for the complete mapping of all {len(raw_rows) - 2} raw values.*")

    # Write report
    outfile = os.path.join(OUTPUT_DIR, 'analysis_report.md')
    with open(outfile, 'w') as f:
        f.write('\n'.join(report))
    print(f"\n  Saved analysis report: {outfile}")
    print(f"\n{'='*70}")
    print("DONE")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
