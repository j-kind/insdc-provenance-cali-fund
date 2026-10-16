#!/usr/bin/env python3
"""
Aggregate annual_counts_sequences.csv onto canonical countries (SEQUENCE pipeline).

Maps raw ENA country-field values to sovereign countries:
  - Historical names → current country (single successor) or "Historical (multi-successor)"
  - Alternative names → canonical country
  - Locality names without country prefix → parent country
  - Non-country values (oceans, seas, placeholders, GAZ) → excluded from country aggregation

Joins with UN M.49 (region, sub-region, dev status, LDC/SIDS/LLDC) and
World Bank (income group) classifications.

Outputs:
  - country_annual_counts.csv: one row per canonical country, year columns + classifications
  - agg_by_region.csv, agg_by_subregion.csv
  - agg_by_dev_status.csv, agg_by_income.csv, agg_by_vulnerability.csv

Usage:
  python3 aggregate_countries.py
"""

import csv
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "pipeline", "data")  # shared with sample pipeline
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

YEARS = ['pre_2018', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026', 'undated', 'all']

# ── Mapping: raw country-field value → canonical country ────────────
# Keys are values from annual_counts.csv that need to be mapped to a
# different canonical country name. Values not in this dict and not in
# NON_COUNTRY are used as-is (they are INSDC vocab countries that are
# already canonical).

COUNTRY_MAPPING = {
    # ── Historical names → current country (single successor) ──
    'Belgian Congo': 'Democratic Republic of the Congo',
    'British Guiana': 'Guyana',
    'Burma': 'Myanmar',
    'Czech Republic': 'Czechia',
    'East Timor': 'Timor-Leste',
    'Macedonia': 'North Macedonia',
    'Siam': 'Thailand',
    'Swaziland': 'Eswatini',
    'The former Yugoslav Republic of Macedonia': 'North Macedonia',
    'Zaire': 'Democratic Republic of the Congo',

    # ── Historical names → multi-successor (cannot cleanly assign) ──
    'USSR': '__HISTORICAL__',
    'Yugoslavia': '__HISTORICAL__',
    'Czechoslovakia': '__HISTORICAL__',
    'Serbia and Montenegro': '__HISTORICAL__',
    'Netherlands Antilles': '__HISTORICAL__',

    # ── Korea: historical "Korea" is ambiguous ──
    # The INSDC vocab has "Korea" as a separate entry. Most "Korea" records
    # are pre-1948 or ambiguous. We map to __HISTORICAL__ since Korea split
    # into North and South Korea (multi-successor).
    'Korea': '__HISTORICAL__',

    # ── Alternative names → canonical country ──
    'United States': 'USA',
    'United States of America': 'USA',
    'US': 'USA',
    'U.S.': 'USA',
    'United_States_of_America': 'USA',
    'UK': 'United Kingdom',
    'Britain': 'United Kingdom',
    'Great Britain': 'United Kingdom',
    'England': 'United Kingdom',
    'Scotland': 'United Kingdom',
    'Wales': 'United Kingdom',
    'Northern Ireland': 'United Kingdom',
    'Turkiye': 'Turkey',
    'Cote d\'Ivoire': 'Cote d\'Ivoire',  # canonical (not in INSDC vocab)
    'Vietnam': 'Viet Nam',
    'Viet_Nam': 'Viet Nam',
    'Syrian Arab Republic': 'Syria',
    'Cambodge': 'Cambodia',
    'Sri_Lanka': 'Sri Lanka',
    'Lao_People\'s_Democratic_Republic': 'Laos',
    'The Bahamas': 'Bahamas',
    'Columbia': 'Colombia',  # likely misspelling; may include some British Columbia records
    'Congo': 'Republic of the Congo',  # bare "Congo" → RoC (DRC is separate vocab entry)

    # ── Territory/island group → sovereign country ──
    'Line Islands': 'Kiribati',  # integral part of Kiribati

    # ── Locality names → parent country ──
    # Japanese localities (country field has locality without "Japan")
    'Sugadaira': 'Japan',
    'Yakushima': 'Japan',
    'Yakushidake': 'Japan',
    'Iriomote': 'Japan',
    'Teshio': 'Japan',
    'Tomakomai': 'Japan',
    'Sasayama': 'Japan',
    'Yoshidayama': 'Japan',
    'Yona': 'Japan',
    'Nippon': 'Japan',
    # Chinese localities
    'Shenzhen': 'China',
    'Xi\'an': 'China',
    'Lijiang': 'China',
    'Ailaoshan': 'China',
    'Nabanhe': 'China',
    # Other localities
    'Valencia': 'Spain',
    'Mississippi River': 'USA',
    'Atacama Desert': 'Chile',
    'Helgoland': 'Germany',
    'Barro Colorado Island': 'Panama',
}

# ── Non-country values (excluded from country aggregation) ──────────
NON_COUNTRY = {
    # Placeholders
    '(no country)', 'missing', 'not applicable', 'not collected',
    'unknown', 'NULL', 'na', 'None', 'not appicable',
    # Gazetteer IDs
    'GAZ',
    # Oceans and seas
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
    'South China Sea', 'East China Sea', 'Greenland Sea',
    # Shared island (multi-country)
    'Borneo',
}

# ── INSDC vocab name → UN M.49 country name mapping ─────────────────
# For countries where the INSDC vocab name differs from the UN name
INSDC_TO_UN = {
    'USA': 'United States of America',
    'United Kingdom': 'United Kingdom of Great Britain and Northern Ireland',
    'Russia': 'Russian Federation',
    'South Korea': 'Republic of Korea',
    'North Korea': "Democratic People's Republic of Korea",
    'Viet Nam': 'Viet Nam',
    'Czechia': 'Czechia',
    'Laos': "Lao People's Democratic Republic",
    'Tanzania': 'United Republic of Tanzania',
    'Iran': 'Iran (Islamic Republic of)',
    'Syria': 'Syrian Arab Republic',
    'Turkey': 'Turkey',  # UN CSV uses "Turkey" not "Türkiye"
    'Moldova': 'Republic of Moldova',
    'Bolivia': 'Bolivia (Plurinational State of)',
    'Venezuela': 'Venezuela (Bolivarian Republic of)',
    'Republic of the Congo': 'Congo',
    'Democratic Republic of the Congo': 'Democratic Republic of the Congo',
    "Cote d'Ivoire": "Côte d\u2019Ivoire",  # UN CSV uses right single quotation mark
    'North Macedonia': 'North Macedonia',
    'State of Palestine': 'State of Palestine',
    'Taiwan': 'Taiwan, Province of China',
    'Hong Kong': 'China,  Hong Kong Special Administrative Region',  # UN CSV has double space
    'Macau': 'China,  Macao Special Administrative Region',
    'Eswatini': 'Eswatini',
    'Timor-Leste': 'Timor-Leste',
    'Brunei': 'Brunei Darussalam',
    'Bahamas': 'Bahamas',
    'Cape Verde': 'Cabo Verde',
    'Micronesia': 'Micronesia (Federated States of)',
    'Micronesia, Federated States of': 'Micronesia (Federated States of)',
    'Fiji': 'Fiji',
    # Territories with different UN names
    'Reunion': 'Réunion',
    'Svalbard': 'Svalbard and Jan Mayen Islands',
    'Curacao': 'Curaçao',
    'Saint Barthelemy': 'Saint Barthélemy',
    'Falkland Islands (Islas Malvinas)': 'Falkland Islands (Malvinas)',
}


def load_un_classifications():
    """Load UN M.49 classifications."""
    filepath = os.path.join(DATA_DIR, 'unsd-country-codes.csv')
    classifications = {}
    with open(filepath, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            country_name = row['Country or Area']
            classifications[country_name] = {
                'un_region': row['Region Name'],
                'un_subregion': row['Sub-region Name'],
                'un_intermediate_region': row['Intermediate Region Name'],
                'iso3': row['ISO-alpha3 Code'],
                'm49': row['M49 Code'],
                'dev_status': row['Developed/Developing Countries'],
                'ldc': row['Least Developed Countries (LDC)'] == 'x',
                'lldc': row['Land Locked Developing Countries (LLDC)'] == 'x',
                'sids': row['Small Island Developing States (SIDS)'] == 'x',
            }
    return classifications


def load_wb_classifications():
    """Load World Bank income group classifications."""
    import openpyxl
    filepath = os.path.join(DATA_DIR, 'WB_CLASS.xlsx')
    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb.active
    classifications = {}
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue
        economy, code, region, income, lending = row[:5]
        if economy:
            classifications[economy] = {
                'wb_region': region,
                'wb_income': income,
            }
            # Also map by ISO3 code
            if code:
                classifications[f'ISO3:{code}'] = {
                    'wb_region': region,
                    'wb_income': income,
                }
    wb.close()
    return classifications


def main():
    print("=" * 70)
    print("AGGREGATING ANNUAL COUNTS ONTO CANONICAL COUNTRIES")
    print("=" * 70)

    # Load data
    infile = os.path.join(OUTPUT_DIR, 'annual_counts_sequences.csv')
    with open(infile) as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)
    print(f"\n  Loaded {len(raw_rows)} rows from annual_counts_sequences.csv")

    un_class = load_un_classifications()
    wb_class = load_wb_classifications()
    print(f"  UN M.49 classifications: {len(un_class)} entries")
    print(f"  World Bank classifications: {len([k for k in wb_class if not k.startswith('ISO3:')])} entries")

    # ── Aggregate onto canonical countries ───────────────────────────
    # {canonical_country: {year: count}}
    country_counts = defaultdict(lambda: {y: 0 for y in YEARS})
    non_country_total = {y: 0 for y in YEARS}
    mapping_log = []  # (raw_value, canonical, count_all) for audit

    for row in raw_rows:
        raw_name = row['country']
        # Skip metadata rows (reconciliation markers from query script)
        if raw_name.startswith('__') and raw_name.endswith('__'):
            continue
        counts = {y: int(row[y]) for y in YEARS}

        if raw_name in NON_COUNTRY:
            for y in YEARS:
                non_country_total[y] += counts[y]
            mapping_log.append((raw_name, '(non-country)', counts['all']))
            continue

        if raw_name in COUNTRY_MAPPING:
            canonical = COUNTRY_MAPPING[raw_name]
        else:
            canonical = raw_name  # INSDC vocab country, already canonical

        for y in YEARS:
            country_counts[canonical][y] += counts[y]
        mapping_log.append((raw_name, canonical, counts['all']))

    # ── Join with classifications ───────────────────────────────────
    def get_un_name(canonical):
        """Map canonical (INSDC) name to UN M.49 name."""
        if canonical in INSDC_TO_UN:
            return INSDC_TO_UN[canonical]
        if canonical == '__HISTORICAL__':
            return None
        return canonical  # assume same as UN name

    def classify_country(canonical):
        """Get UN M.49 + WB classifications for a canonical country."""
        if canonical == '__HISTORICAL__':
            return {
                'iso3': '', 'un_region': '', 'un_subregion': '',
                'dev_status': '', 'wb_income': 'Unknown',
                'ldc': False, 'sids': False, 'lldc': False,
            }

        un_name = get_un_name(canonical)
        result = {
            'iso3': '', 'un_region': '', 'un_subregion': '',
            'dev_status': '', 'wb_income': 'Unknown',
            'ldc': False, 'sids': False, 'lldc': False,
        }

        # UN M.49 lookup
        if un_name and un_name in un_class:
            c = un_class[un_name]
            result['iso3'] = c['iso3']
            result['un_region'] = c['un_region']
            result['un_subregion'] = c['un_subregion'] or c.get('un_intermediate_region', '')
            result['dev_status'] = c['dev_status']
            result['ldc'] = c['ldc']
            result['sids'] = c['sids']
            result['lldc'] = c['lldc']

        # WB lookup by UN name, then by ISO3
        if un_name and un_name in wb_class:
            result['wb_income'] = wb_class[un_name]['wb_income']
        elif result['iso3'] and f'ISO3:{result["iso3"]}' in wb_class:
            result['wb_income'] = wb_class[f'ISO3:{result["iso3"]}']['wb_income']

        # Fallbacks for common name mismatches
        if not result['dev_status']:
            fallbacks = {
                'USA': ('United States of America', 'Developed', 'High income'),
                'United Kingdom': ('United Kingdom of Great Britain and Northern Ireland', 'Developed', 'High income'),
                'Cote d\'Ivoire': ("Côte d'Ivoire", 'Developing', 'Lower middle income'),
                'Taiwan': ('Taiwan, China', 'Developed', 'High income'),
                'Hong Kong': ('Hong Kong SAR, China', 'Developed', 'High income'),
                'Macau': ('Macao SAR, China', 'Developed', 'High income'),
                'Kosovo': ('Kosovo', 'Developing', 'Upper middle income'),
                'Czechia': ('Czechia', 'Developed', 'High income'),
                'Eswatini': ('Eswatini', 'Developing', 'Lower middle income'),
                'Timor-Leste': ('Timor-Leste', 'Developing', 'Lower middle income'),
                'North Macedonia': ('North Macedonia', 'Developing', 'Upper middle income'),
            }
            if canonical in fallbacks:
                _, ds, wi = fallbacks[canonical]
                result['dev_status'] = ds
                result['wb_income'] = wi

        return result

    # ── Build country-level table ───────────────────────────────────
    output_columns = ['country', 'iso3', 'un_region', 'un_subregion',
                      'dev_status', 'wb_income', 'ldc', 'sids', 'lldc'] + YEARS

    country_rows = []
    for canonical in sorted(country_counts.keys()):
        cls = classify_country(canonical)
        row = {
            'country': canonical,
            'iso3': cls['iso3'],
            'un_region': cls['un_region'],
            'un_subregion': cls['un_subregion'],
            'dev_status': cls['dev_status'] or 'Unknown',
            'wb_income': cls['wb_income'],
            'ldc': 'LDC' if cls['ldc'] else '',
            'sids': 'SIDS' if cls['sids'] else '',
            'lldc': 'LLDC' if cls['lldc'] else '',
        }
        row.update({y: country_counts[canonical][y] for y in YEARS})
        country_rows.append(row)

    # Write country-level table
    outfile = os.path.join(OUTPUT_DIR, 'country_annual_counts_sequences.csv')
    with open(outfile, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=output_columns)
        writer.writeheader()
        for row in country_rows:
            writer.writerow(row)
    print(f"\n  Saved country-level table: {outfile} ({len(country_rows)} countries)")

    # ── Aggregation functions ───────────────────────────────────────
    def aggregate_by(key_func, key_name, exclude_historical=True):
        """Aggregate country counts by a classification key."""
        agg = defaultdict(lambda: {y: 0 for y in YEARS})
        countries = defaultdict(int)
        for row in country_rows:
            if exclude_historical and row['country'] == '__HISTORICAL__':
                continue
            key = key_func(row)
            if key:
                countries[key] += 1
                for y in YEARS:
                    agg[key][y] += int(row[y])
        return agg, countries

    # By UN region
    agg_region, n_region = aggregate_by(lambda r: r['un_region'] or 'Unmapped', 'un_region')
    # By UN sub-region
    agg_subregion, n_subregion = aggregate_by(lambda r: r['un_subregion'] or 'Unmapped', 'un_subregion')
    # By development status
    agg_dev, n_dev = aggregate_by(lambda r: r['dev_status'] or 'Unknown', 'dev_status')
    # By WB income group
    agg_income, n_income = aggregate_by(lambda r: r['wb_income'] or 'Unknown', 'wb_income')
    # By LDC/SIDS/LLDC
    agg_vuln = {}
    n_vuln = {}
    for label, field in [('LDC', 'ldc'), ('SIDS', 'sids'), ('LLDC', 'lldc')]:
        vuln_counts = {y: 0 for y in YEARS}
        vuln_countries = 0
        for row in country_rows:
            if row[field]:
                vuln_countries += 1
                for y in YEARS:
                    vuln_counts[y] += int(row[y])
        agg_vuln[label] = vuln_counts
        n_vuln[label] = vuln_countries

    # ── Write aggregation tables ────────────────────────────────────
    def write_agg(filename, agg_dict, count_dict, sort_by='all', reverse=True):
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['group', 'countries'] + YEARS)
            for key in sorted(agg_dict.keys(), key=lambda k: agg_dict[k].get(sort_by, 0), reverse=reverse):
                row = [key, count_dict.get(key, 0)] + [agg_dict[key][y] for y in YEARS]
                writer.writerow(row)
        print(f"  Saved {filename}")

    write_agg('agg_by_region.csv', agg_region, n_region)
    write_agg('agg_by_subregion.csv', agg_subregion, n_subregion)
    write_agg('agg_by_dev_status.csv', agg_dev, n_dev)
    write_agg('agg_by_income.csv', agg_income, n_income)

    # Vulnerability
    filepath = os.path.join(OUTPUT_DIR, 'agg_by_vulnerability.csv')
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['group', 'countries'] + YEARS)
        for label in ['LDC', 'SIDS', 'LLDC']:
            writer.writerow([label, n_vuln[label]] + [agg_vuln[label][y] for y in YEARS])
    print(f"  Saved agg_by_vulnerability.csv")

    # ── Print summary ───────────────────────────────────────────────
    print(f"\n  Non-country total (oceans, seas, placeholders, GAZ): {non_country_total['all']:,}")
    print(f"  Historical (multi-successor) total: {country_counts.get('__HISTORICAL__', {}).get('all', 0):,}")
    print(f"  Country-attributed total: {sum(country_counts[c]['all'] for c in country_counts if c != '__HISTORICAL__'):,}")

    print(f"\n  By development status:")
    for key in sorted(agg_dev.keys(), key=lambda k: agg_dev[k]['all'], reverse=True):
        d = agg_dev[key]
        pct = 100 * d['all'] / sum(agg_dev[k]['all'] for k in agg_dev) if sum(agg_dev[k]['all'] for k in agg_dev) else 0
        print(f"    {key:<15} {n_dev[key]:>3} countries  all={d['all']:>12,}  ({pct:.1f}%)")

    print(f"\n  By UN region:")
    for key in sorted(agg_region.keys(), key=lambda k: agg_region[k]['all'], reverse=True):
        d = agg_region[key]
        print(f"    {key:<25} {n_region[key]:>3} countries  all={d['all']:>12,}")

    # ── Write mapping audit log ─────────────────────────────────────
    audit_file = os.path.join(OUTPUT_DIR, 'country_mapping_audit_sequences.csv')
    with open(audit_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['raw_value', 'mapped_to', 'all_count'])
        for raw, canonical, count in sorted(mapping_log, key=lambda x: -x[2]):
            writer.writerow([raw, canonical, count])
    print(f"\n  Saved mapping audit: {audit_file} ({len(mapping_log)} entries)")

    print(f"\n{'='*70}")
    print("DONE")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
