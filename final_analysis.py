#!/usr/bin/env python3
"""
Final analysis: Combine ENA and NCBI per-country provenance counts,
map to UN classifications, and produce the three country-level maps
for the Cali Fund allocation methodology assessment.

Three maps:
  1. All legacy non-human DSI records with country provenance
  2. Post-2023 records (first_public >= 2024-01-01)
  3. Environmentally sourced records with provenance

Data sources:
  - ENA portal API: per-country sample counts (primary, comprehensive)
  - NCBI BioSample ESearch: per-country counts (cross-reference)
  - UN M.49 classifications from unsd-country-codes.csv
  - World Bank income classifications from WB_CLASS.xlsx
"""

import csv
import os
import json
from collections import defaultdict

OUTPUT_DIR = "/Users/jasminekindness/IIFB_COP17/ahteg_allocation"

# ── INSDC country name → UN country mapping ──────────────────────────────
INSDC_TO_UN = {
    "Afghanistan": "Afghanistan", "Albania": "Albania", "Algeria": "Algeria",
    "American Samoa": "American Samoa", "Andorra": "Andorra", "Angola": "Angola",
    "Anguilla": "Anguilla", "Antarctica": "Antarctica",
    "Antigua and Barbuda": "Antigua and Barbuda", "Argentina": "Argentina",
    "Armenia": "Armenia", "Aruba": "Aruba", "Australia": "Australia",
    "Austria": "Austria", "Azerbaijan": "Azerbaijan", "Bahamas": "Bahamas",
    "Bahrain": "Bahrain", "Bangladesh": "Bangladesh", "Barbados": "Barbados",
    "Belarus": "Belarus", "Belgium": "Belgium", "Belize": "Belize",
    "Benin": "Benin", "Bermuda": "Bermuda", "Bhutan": "Bhutan",
    "Bolivia": "Bolivia (Plurinational State of)",
    "Bosnia and Herzegovina": "Bosnia and Herzegovina", "Botswana": "Botswana",
    "Brazil": "Brazil", "British Virgin Islands": "British Virgin Islands",
    "Brunei": "Brunei Darussalam", "Bulgaria": "Bulgaria",
    "Burkina Faso": "Burkina Faso", "Burundi": "Burundi",
    "Cambodia": "Cambodia", "Cameroon": "Cameroon", "Canada": "Canada",
    "Cape Verde": "Cabo Verde", "Cayman Islands": "Cayman Islands",
    "Central African Republic": "Central African Republic", "Chad": "Chad",
    "Chile": "Chile", "China": "China", "Christmas Island": "Christmas Island",
    "Cocos Islands": "Cocos (Keeling) Islands", "Colombia": "Colombia",
    "Comoros": "Comoros", "Cook Islands": "Cook Islands",
    "Costa Rica": "Costa Rica", "Croatia": "Croatia", "Cuba": "Cuba",
    "Curacao": "Curaçao", "Cyprus": "Cyprus", "Czechia": "Czechia",
    "Czech Republic": "Czechia",
    "Democratic Republic of the Congo": "Democratic Republic of the Congo",
    "Denmark": "Denmark", "Djibouti": "Djibouti", "Dominica": "Dominica",
    "Dominican Republic": "Dominican Republic", "Ecuador": "Ecuador",
    "Egypt": "Egypt", "El Salvador": "El Salvador",
    "Equatorial Guinea": "Equatorial Guinea", "Eritrea": "Eritrea",
    "Estonia": "Estonia", "Eswatini": "Eswatini", "Ethiopia": "Ethiopia",
    "Falkland Islands (Islas Malvinas)": "Falkland Islands (Malvinas)",
    "Faroe Islands": "Faroe Islands", "Fiji": "Fiji", "Finland": "Finland",
    "France": "France", "French Guiana": "French Guiana",
    "French Polynesia": "French Polynesia", "Gabon": "Gabon",
    "Gambia": "Gambia", "Gaza Strip": "State of Palestine",
    "Georgia": "Georgia", "Germany": "Germany", "Ghana": "Ghana",
    "Gibraltar": "Gibraltar", "Greece": "Greece", "Greenland": "Greenland",
    "Grenada": "Grenada", "Guadeloupe": "Guadeloupe", "Guam": "Guam",
    "Guatemala": "Guatemala", "Guernsey": "Guernsey", "Guinea": "Guinea",
    "Guinea-Bissau": "Guinea-Bissau", "Guyana": "Guyana", "Haiti": "Haiti",
    "Honduras": "Honduras", "Hong Kong": "China, Hong Kong Special Administrative Region",
    "Hungary": "Hungary", "Iceland": "Iceland", "India": "India",
    "Indonesia": "Indonesia", "Iran": "Iran (Islamic Republic of)",
    "Iraq": "Iraq", "Ireland": "Ireland", "Israel": "Israel",
    "Italy": "Italy", "Jamaica": "Jamaica", "Japan": "Japan",
    "Jersey": "Jersey", "Jordan": "Jordan", "Kazakhstan": "Kazakhstan",
    "Kenya": "Kenya", "Kiribati": "Kiribati", "Kosovo": "Kosovo",
    "Kuwait": "Kuwait", "Kyrgyzstan": "Kyrgyzstan",
    "Laos": "Lao People's Democratic Republic", "Latvia": "Latvia",
    "Lebanon": "Lebanon", "Lesotho": "Lesotho", "Liberia": "Liberia",
    "Libya": "Libya", "Liechtenstein": "Liechtenstein",
    "Lithuania": "Lithuania", "Luxembourg": "Luxembourg",
    "Macau": "China, Macao Special Administrative Region",
    "Madagascar": "Madagascar", "Malawi": "Malawi", "Malaysia": "Malaysia",
    "Maldives": "Maldives", "Mali": "Mali", "Malta": "Malta",
    "Marshall Islands": "Marshall Islands", "Martinique": "Martinique",
    "Mauritania": "Mauritania", "Mauritius": "Mauritius", "Mayotte": "Mayotte",
    "Mexico": "Mexico",
    "Micronesia, Federated States of": "Micronesia (Federated States of)",
    "Micronesia": "Micronesia (Federated States of)",
    "Moldova": "Republic of Moldova", "Monaco": "Monaco",
    "Mongolia": "Mongolia", "Montenegro": "Montenegro",
    "Montserrat": "Montserrat", "Morocco": "Morocco",
    "Mozambique": "Mozambique", "Myanmar": "Myanmar", "Namibia": "Namibia",
    "Nauru": "Nauru", "Nepal": "Nepal", "Netherlands": "Netherlands",
    "New Caledonia": "New Caledonia", "New Zealand": "New Zealand",
    "Nicaragua": "Nicaragua", "Niger": "Niger", "Nigeria": "Nigeria",
    "Niue": "Niue", "North Korea": "Democratic People's Republic of Korea",
    "North Macedonia": "North Macedonia", "Norway": "Norway",
    "Oman": "Oman", "Pakistan": "Pakistan", "Palau": "Palau",
    "Panama": "Panama", "Papua New Guinea": "Papua New Guinea",
    "Paraguay": "Paraguay", "Peru": "Peru", "Philippines": "Philippines",
    "Pitcairn Islands": "Pitcairn", "Poland": "Poland", "Portugal": "Portugal",
    "Puerto Rico": "Puerto Rico", "Qatar": "Qatar",
    "Republic of the Congo": "Congo", "Reunion": "Réunion",
    "Romania": "Romania", "Russia": "Russian Federation",
    "Rwanda": "Rwanda", "Saint Barthelemy": "Saint Barthélemy",
    "Saint Helena": "Saint Helena", "Saint Kitts and Nevis": "Saint Kitts and Nevis",
    "Saint Lucia": "Saint Lucia",
    "Saint Martin": "Saint Martin (French Part)",
    "Saint Pierre and Miquelon": "Saint Pierre and Miquelon",
    "Saint Vincent and the Grenadines": "Saint Vincent and the Grenadines",
    "Samoa": "Samoa", "San Marino": "San Marino",
    "Sao Tome and Principe": "Sao Tome and Principe",
    "Saudi Arabia": "Saudi Arabia", "Senegal": "Senegal", "Serbia": "Serbia",
    "Seychelles": "Seychelles", "Sierra Leone": "Sierra Leone",
    "Singapore": "Singapore", "Sint Maarten": "Sint Maarten (Dutch part)",
    "Slovakia": "Slovakia", "Slovenia": "Slovenia",
    "Solomon Islands": "Solomon Islands", "Somalia": "Somalia",
    "South Africa": "South Africa", "South Korea": "Republic of Korea",
    "Korea": "Republic of Korea",
    "South Sudan": "South Sudan", "Spain": "Spain", "Sri Lanka": "Sri Lanka",
    "Sudan": "Sudan", "Suriname": "Suriname",
    "Svalbard": "Svalbard and Jan Mayen Islands",
    "Sweden": "Sweden", "Switzerland": "Switzerland",
    "Syria": "Syrian Arab Republic", "Taiwan": "Taiwan",
    "Tajikistan": "Tajikistan", "Tanzania": "United Republic of Tanzania",
    "Thailand": "Thailand", "Timor-Leste": "Timor-Leste",
    "East Timor": "Timor-Leste", "Togo": "Togo", "Tokelau": "Tokelau",
    "Tonga": "Tonga", "Trinidad and Tobago": "Trinidad and Tobago",
    "Tunisia": "Tunisia", "Turkey": "Turkey",
    "Turkmenistan": "Turkmenistan",
    "Turks and Caicos Islands": "Turks and Caicos Islands",
    "Tuvalu": "Tuvalu", "Uganda": "Uganda", "Ukraine": "Ukraine",
    "United Arab Emirates": "United Arab Emirates",
    "United Kingdom": "United Kingdom of Great Britain and Northern Ireland",
    "Uruguay": "Uruguay", "USA": "United States of America",
    "Uzbekistan": "Uzbekistan", "Vanuatu": "Vanuatu",
    "Venezuela": "Venezuela (Bolivarian Republic of)",
    "Viet Nam": "Viet Nam", "Vietnam": "Viet Nam",
    "Virgin Islands": "United States Virgin Islands",
    "Wallis and Futuna": "Wallis and Futuna Islands",
    "West Bank": "State of Palestine", "State of Palestine": "State of Palestine",
    "Western Sahara": "Western Sahara", "Yemen": "Yemen",
    "Zambia": "Zambia", "Zimbabwe": "Zimbabwe",
    # Historical/obsolete
    "Belgian Congo": "Democratic Republic of the Congo",
    "British Guiana": "Guyana", "Burma": "Myanmar",
    "Czechoslovakia": "Czechia", "East Timor": "Timor-Leste",
    "Macedonia": "North Macedonia",
    "Netherlands Antilles": "Curaçao",
    "Serbia and Montenegro": "Serbia", "Siam": "Thailand",
    "Swaziland": "Eswatini",
    "The former Yugoslav Republic of Macedonia": "North Macedonia",
    "USSR": "Russian Federation", "Yugoslavia": "Serbia",
    "Zaire": "Democratic Republic of the Congo",
    # Oceans and seas
    "Arctic Ocean": "__OCEANS_SEAS__", "Atlantic Ocean": "__OCEANS_SEAS__",
    "Baltic Sea": "__OCEANS_SEAS__", "Borneo": "__MULTINATIONAL__",
    "Indian Ocean": "__OCEANS_SEAS__", "Mediterranean Sea": "__OCEANS_SEAS__",
    "North Sea": "__OCEANS_SEAS__", "Pacific Ocean": "__OCEANS_SEAS__",
    "Ross Sea": "__OCEANS_SEAS__", "Southern Ocean": "__OCEANS_SEAS__",
    "Tasman Sea": "__OCEANS_SEAS__",
    # Territories
    "Ashmore and Cartier Islands": "__TERRITORY__",
    "Baker Island": "__TERRITORY__", "Bassas da India": "__TERRITORY__",
    "Bouvet Island": "__TERRITORY__", "Clipperton Island": "__TERRITORY__",
    "Coral Sea Islands": "__TERRITORY__", "Europa Island": "__TERRITORY__",
    "French Southern and Antarctic Lands": "French Southern Territories",
    "Glorioso Islands": "__TERRITORY__",
    "Heard Island and McDonald Islands": "Heard Island and McDonald Islands",
    "Howland Island": "__TERRITORY__", "Jan Mayen": "__TERRITORY__",
    "Jarvis Island": "__TERRITORY__", "Johnston Atoll": "__TERRITORY__",
    "Juan de Nova Island": "__TERRITORY__",
    "Kerguelen Archipelago": "__TERRITORY__",
    "Kingman Reef": "__TERRITORY__", "Line Islands": "__TERRITORY__",
    "Midway Islands": "__TERRITORY__", "Navassa Island": "__TERRITORY__",
    "Norfolk Island": "Norfolk Island", "Palmyra Atoll": "__TERRITORY__",
    "Paracel Islands": "__TERRITORY__", "Spratly Islands": "__TERRITORY__",
    "Wake Island": "__TERRITORY__",
}

def load_un_classifications():
    classifications = {}
    with open(os.path.join(OUTPUT_DIR, "unsd-country-codes.csv"), encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['Country or Area']
            classifications[name] = {
                'region': row['Region Name'],
                'sub_region': row['Sub-region Name'],
                'intermediate_region': row['Intermediate Region Name'],
                'iso3': row['ISO-alpha3 Code'],
                'm49': row['M49 Code'],
                'ldc': row['Least Developed Countries (LDC)'] == 'x',
                'lldc': row['Land Locked Developing Countries (LLDC)'] == 'x',
                'sids': row['Small Island Developing States (SIDS)'] == 'x',
                'dev_status': row['Developed/Developing Countries'],
            }
    return classifications

def load_ena_counts():
    counts = {}
    with open(os.path.join(OUTPUT_DIR, "ena_per_country_counts.csv"), encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            counts[row['country']] = {
                'all': int(row['all_records']),
                'post2023': int(row['post2023']),
                'env': int(row['environmental']),
            }
    return counts

def load_ncbi_counts():
    counts = {}
    for suffix in ['all_legacy', 'post2023', 'environmental']:
        counts[suffix] = {}
        with open(os.path.join(OUTPUT_DIR, f"insdc_counts_{suffix}.csv"), encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['country'] != '__TOTAL__':
                    counts[suffix][row['country']] = int(row['count'])
    return counts

def main():
    un_data = load_un_classifications()
    ena_counts = load_ena_counts()
    ncbi_counts = load_ncbi_counts()
    
    # ── Merge ENA INSDC names that map to the same UN country ──
    merged = {}
    for insdc_name, data in ena_counts.items():
        if data['all'] <= 0 and data['post2023'] <= 0 and data['env'] <= 0:
            continue
        un_name = INSDC_TO_UN.get(insdc_name, "__UNMAPPED__")
        if un_name not in merged:
            merged[un_name] = {'all': 0, 'post2023': 0, 'env': 0, 'insdc_names': []}
        merged[un_name]['all'] += data['all']
        merged[un_name]['post2023'] += data['post2023']
        merged[un_name]['env'] += data['env']
        merged[un_name]['insdc_names'].append(insdc_name)
    
    # Also merge NCBI counts (separate cross-reference)
    ncbi_merged = {}
    for insdc_name, count in ncbi_counts['all_legacy'].items():
        if count <= 0:
            continue
        un_name = INSDC_TO_UN.get(insdc_name, "__UNMAPPED__")
        if un_name not in ncbi_merged:
            ncbi_merged[un_name] = {'all': 0, 'post2023': 0, 'env': 0}
        ncbi_merged[un_name]['all'] += count
    for insdc_name, count in ncbi_counts['post2023'].items():
        if count <= 0:
            continue
        un_name = INSDC_TO_UN.get(insdc_name, "__UNMAPPED__")
        if un_name not in ncbi_merged:
            ncbi_merged[un_name] = {'all': 0, 'post2023': 0, 'env': 0}
        ncbi_merged[un_name]['post2023'] += count
    for insdc_name, count in ncbi_counts['environmental'].items():
        if count <= 0:
            continue
        un_name = INSDC_TO_UN.get(insdc_name, "__UNMAPPED__")
        if un_name not in ncbi_merged:
            ncbi_merged[un_name] = {'all': 0, 'post2023': 0, 'env': 0}
        ncbi_merged[un_name]['env'] += count
    
    # ── Build enriched table ──
    enriched = []
    for un_name, data in merged.items():
        un_info = un_data.get(un_name, {})
        ncbi = ncbi_merged.get(un_name, {'all': 0, 'post2023': 0, 'env': 0})
        enriched.append({
            'country': un_name,
            'iso3': un_info.get('iso3', ''),
            'm49': un_info.get('m49', ''),
            'region': un_info.get('region', ''),
            'sub_region': un_info.get('sub_region', ''),
            'dev_status': un_info.get('dev_status', ''),
            'ldc': 'x' if un_info.get('ldc') else '',
            'lldc': 'x' if un_info.get('lldc') else '',
            'sids': 'x' if un_info.get('sids') else '',
            'ena_all': data['all'],
            'ena_post2023': data['post2023'],
            'ena_env': data['env'],
            'ncbi_all': ncbi['all'],
            'ncbi_post2023': ncbi['post2023'],
            'ncbi_env': ncbi['env'],
            'insdc_names': '; '.join(data['insdc_names']),
        })
    
    enriched.sort(key=lambda x: x['ena_all'], reverse=True)
    
    # ── Write main CSV ──
    outfile = os.path.join(OUTPUT_DIR, "insdc_provenance_country_maps.csv")
    with open(outfile, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'country', 'iso3', 'm49', 'region', 'sub_region', 'dev_status',
            'ldc', 'lldc', 'sids',
            'ena_all', 'ena_post2023', 'ena_env',
            'ncbi_all', 'ncbi_post2023', 'ncbi_env',
            'insdc_names'
        ])
        writer.writeheader()
        for row in enriched:
            writer.writerow(row)
    print(f"Saved main table to {outfile}")
    
    # ── Compute totals ──
    ena_total_all = sum(r['ena_all'] for r in enriched)
    ena_total_post = sum(r['ena_post2023'] for r in enriched)
    ena_total_env = sum(r['ena_env'] for r in enriched)
    ncbi_total_all = sum(r['ncbi_all'] for r in enriched)
    ncbi_total_post = sum(r['ncbi_post2023'] for r in enriched)
    ncbi_total_env = sum(r['ncbi_env'] for r in enriched)
    
    # ── Aggregations ──
    def aggregate(key_func):
        agg = defaultdict(lambda: {'all': 0, 'post2023': 0, 'env': 0, 'countries': 0})
        for r in enriched:
            k = key_func(r)
            agg[k]['all'] += r['ena_all']
            agg[k]['post2023'] += r['ena_post2023']
            agg[k]['env'] += r['ena_env']
            agg[k]['countries'] += 1
        return dict(agg)
    
    by_region = aggregate(lambda r: r['region'] or 'Unmapped/Territory')
    by_dev = aggregate(lambda r: r['dev_status'] or 'Unmapped/Territory')
    by_subregion = aggregate(lambda r: r['sub_region'] or 'Unmapped/Territory')
    
    # ── Print results ──
    print(f"\n{'='*90}")
    print(f"INSDC PROVENANCE COUNTRY-LEVEL MAPS FOR CALI FUND ALLOCATION")
    print(f"{'='*90}")
    print(f"\nData sources: ENA portal API (primary) + NCBI BioSample ESearch (cross-reference)")
    print(f"Scope: Non-human (tax_tree excluding 9606) sample records with country provenance")
    
    print(f"\n{'─'*90}")
    print(f"GRAND TOTALS (ENA)")
    print(f"{'─'*90}")
    print(f"  Total non-human samples with country provenance (all):  {ena_total_all:>12,}")
    print(f"  Post-2023 records (first_public >= 2024):               {ena_total_post:>12,}")
    print(f"  Environmentally sourced records:                         {ena_total_env:>12,}")
    print(f"  Countries/territories with >= 1 record:                 {len(enriched):>12}")
    
    print(f"\n{'─'*90}")
    print(f"GRAND TOTALS (NCBI BioSample, cross-reference)")
    print(f"{'─'*90}")
    print(f"  Total non-human biosamples with country:                {ncbi_total_all:>12,}")
    print(f"  Post-2023:                                               {ncbi_total_post:>12,}")
    print(f"  Environmental:                                           {ncbi_total_env:>12,}")
    
    # ── Map 1: All legacy records by region ──
    print(f"\n{'='*90}")
    print(f"MAP 1: ALL LEGACY NON-HUMAN DSI RECORDS WITH COUNTRY PROVENANCE (ENA)")
    print(f"{'='*90}")
    print(f"\n{'Region':<30} {'Countries':>10} {'Records':>14} {'% Share':>8}")
    print(f"{'─'*65}")
    for r in sorted(by_region.keys(), key=lambda x: by_region[x]['all'], reverse=True):
        d = by_region[r]
        pct = 100 * d['all'] / ena_total_all if ena_total_all else 0
        print(f"{r:<30} {d['countries']:>10} {d['all']:>14,} {pct:>7.1f}%")
    
    print(f"\n{'Development Status':<25} {'Countries':>10} {'Records':>14} {'% Share':>8}")
    print(f"{'─'*60}")
    for s in sorted(by_dev.keys(), key=lambda x: by_dev[x]['all'], reverse=True):
        d = by_dev[s]
        pct = 100 * d['all'] / ena_total_all if ena_total_all else 0
        print(f"{s:<25} {d['countries']:>10} {d['all']:>14,} {pct:>7.1f}%")
    
    # ── Map 2: Post-2023 ──
    print(f"\n{'='*90}")
    print(f"MAP 2: POST-2023 NON-HUMAN DSI RECORDS (first_public >= 2024-01-01)")
    print(f"{'='*90}")
    print(f"\n{'Region':<30} {'Countries':>10} {'Records':>14} {'% Share':>8} {'Growth%':>8}")
    print(f"{'─'*73}")
    for r in sorted(by_region.keys(), key=lambda x: by_region[x]['post2023'], reverse=True):
        d = by_region[r]
        pct = 100 * d['post2023'] / ena_total_post if ena_total_post else 0
        growth = 100 * d['post2023'] / d['all'] if d['all'] > 0 else 0
        print(f"{r:<30} {d['countries']:>10} {d['post2023']:>14,} {pct:>7.1f}% {growth:>7.1f}%")
    
    print(f"\n{'Development Status':<25} {'Countries':>10} {'Records':>14} {'% Share':>8} {'Growth%':>8}")
    print(f"{'─'*68}")
    for s in sorted(by_dev.keys(), key=lambda x: by_dev[x]['post2023'], reverse=True):
        d = by_dev[s]
        pct = 100 * d['post2023'] / ena_total_post if ena_total_post else 0
        growth = 100 * d['post2023'] / d['all'] if d['all'] > 0 else 0
        print(f"{s:<25} {d['countries']:>10} {d['post2023']:>14,} {pct:>7.1f}% {growth:>7.1f}%")
    
    # ── Map 3: Environmental ──
    print(f"\n{'='*90}")
    print(f"MAP 3: ENVIRONMENTALLY SOURCED NON-HUMAN DSI RECORDS WITH PROVENANCE")
    print(f"{'='*90}")
    print(f"\n{'Region':<30} {'Countries':>10} {'Records':>14} {'% Share':>8} {'% of All':>8}")
    print(f"{'─'*73}")
    for r in sorted(by_region.keys(), key=lambda x: by_region[x]['env'], reverse=True):
        d = by_region[r]
        pct = 100 * d['env'] / ena_total_env if ena_total_env else 0
        env_rate = 100 * d['env'] / d['all'] if d['all'] > 0 else 0
        print(f"{r:<30} {d['countries']:>10} {d['env']:>14,} {pct:>7.1f}% {env_rate:>7.1f}%")
    
    print(f"\n{'Development Status':<25} {'Countries':>10} {'Records':>14} {'% Share':>8} {'% of All':>8}")
    print(f"{'─'*68}")
    for s in sorted(by_dev.keys(), key=lambda x: by_dev[x]['env'], reverse=True):
        d = by_dev[s]
        pct = 100 * d['env'] / ena_total_env if ena_total_env else 0
        env_rate = 100 * d['env'] / d['all'] if d['all'] > 0 else 0
        print(f"{s:<25} {d['countries']:>10} {d['env']:>14,} {pct:>7.1f}% {env_rate:>7.1f}%")
    
    # ── LDC/SIDS/LLDC ──
    print(f"\n{'='*90}")
    print(f"VULNERABLE COUNTRY GROUPS SUMMARY (ENA)")
    print(f"{'='*90}")
    print(f"\n{'Group':<10} {'Countries':>10} {'All':>14} {'Post-2023':>14} {'Environmental':>14} {'% of All':>8}")
    print(f"{'─'*75}")
    for cat, label in [('ldc', 'LDC'), ('sids', 'SIDS'), ('lldc', 'LLDC')]:
        rows = [r for r in enriched if r[cat] == 'x']
        a = sum(r['ena_all'] for r in rows)
        p = sum(r['ena_post2023'] for r in rows)
        e = sum(r['ena_env'] for r in rows)
        pct = 100 * a / ena_total_all if ena_total_all else 0
        print(f"{label:<10} {len(rows):>10} {a:>14,} {p:>14,} {e:>14,} {pct:>7.1f}%")
    
    # ── Top 40 countries (ENA) ──
    print(f"\n{'='*90}")
    print(f"TOP 40 COUNTRIES BY ALL DSI RECORDS WITH PROVENANCE (ENA)")
    print(f"{'='*90}")
    print(f"\n{'#':>3} {'Country':<35} {'ISO3':>5} {'Dev':<10} {'All':>12} {'Post-23':>10} {'Env':>8} {'% Share':>7}")
    print(f"{'─'*95}")
    for i, row in enumerate(enriched[:40], 1):
        pct = 100 * row['ena_all'] / ena_total_all if ena_total_all else 0
        dev = (row['dev_status'] or '?')[:10]
        print(f"{i:>3} {row['country'][:35]:<35} {row['iso3'] or '---':>5} {dev:<10} {row['ena_all']:>12,} {row['ena_post2023']:>10,} {row['ena_env']:>8,} {pct:>6.1f}%")
    
    # ── Developing countries with zero or near-zero ──
    print(f"\n{'='*90}")
    print(f"DEVELOPING COUNTRIES WITH < 100 ENA RECORDS")
    print(f"{'='*90}")
    low = [r for r in enriched if r['dev_status'] == 'Developing' and r['ena_all'] < 100]
    low.sort(key=lambda x: x['country'])
    print(f"\nCount: {len(low)} countries")
    print(f"\n{'Country':<40} {'All':>6} {'Post':>6} {'Env':>6} {'Flags':>15}")
    print(f"{'─'*75}")
    for r in low:
        flags = ' '.join([f for f in [r['ldc'] and 'LDC', r['sids'] and 'SIDS', r['lldc'] and 'LLDC'] if f])
        print(f"{r['country'][:40]:<40} {r['ena_all']:>6} {r['ena_post2023']:>6} {r['ena_env']:>6} {flags:>15}")
    
    # ── Post-2023 growth leaders ──
    print(f"\n{'='*90}")
    print(f"POST-2023 GROWTH: TOP 25 BY GROWTH RATE (min 1,000 total records)")
    print(f"{'='*90}")
    growth_candidates = [r for r in enriched if r['ena_all'] >= 1000]
    growth_candidates.sort(key=lambda x: x['ena_post2023'] / x['ena_all'] if x['ena_all'] > 0 else 0, reverse=True)
    print(f"\n{'#':>3} {'Country':<30} {'All':>10} {'Post-23':>10} {'Growth%':>8} {'Dev':<10}")
    print(f"{'─'*75}")
    for i, r in enumerate(growth_candidates[:25], 1):
        g = 100 * r['ena_post2023'] / r['ena_all'] if r['ena_all'] > 0 else 0
        print(f"{i:>3} {r['country'][:30]:<30} {r['ena_all']:>10,} {r['ena_post2023']:>10,} {g:>7.1f}% {(r['dev_status'] or '?')[:10]:<10}")
    
    # ── Sub-regional breakdown ──
    print(f"\n{'='*90}")
    print(f"SUB-REGIONAL BREAKDOWN (ENA, all records)")
    print(f"{'='*90}")
    print(f"\n{'Sub-region':<35} {'Countries':>10} {'Records':>14} {'% Share':>8}")
    print(f"{'─'*70}")
    for sr in sorted(by_subregion.keys(), key=lambda x: by_subregion[x]['all'], reverse=True):
        d = by_subregion[sr]
        pct = 100 * d['all'] / ena_total_all if ena_total_all else 0
        print(f"{sr:<35} {d['countries']:>10} {d['all']:>14,} {pct:>7.1f}%")
    
    # ── Write JSON ──
    json_out = os.path.join(OUTPUT_DIR, "insdc_provenance_final_analysis.json")
    with open(json_out, 'w', encoding='utf-8') as f:
        json.dump({
            'totals': {
                'ena_all': ena_total_all,
                'ena_post2023': ena_total_post,
                'ena_env': ena_total_env,
                'ncbi_all': ncbi_total_all,
                'ncbi_post2023': ncbi_total_post,
                'ncbi_env': ncbi_total_env,
                'countries_with_data': len(enriched),
            },
            'by_region': {r: d for r, d in by_region.items()},
            'by_dev_status': {s: d for s, d in by_dev.items()},
            'by_subregion': {sr: d for sr, d in by_subregion.items()},
            'countries': enriched,
        }, f, indent=2)
    print(f"\nSaved JSON to {json_out}")

if __name__ == "__main__":
    main()
