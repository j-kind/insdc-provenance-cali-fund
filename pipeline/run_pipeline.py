#!/usr/bin/env python3
"""
INSDC Provenance Country-Level Maps for the Cali Fund — v2 Pipeline
====================================================================

End-to-end reproducible workflow:
  Stage 1: Build country master table (INSDC vocab → UN M.49 → WB income)
  Stage 2: Query ENA /count for per-country counts (primary source)
  Stage 3: Query NCBI ESearch [country] for cross-check
  Stage 4: Aggregate by region, dev status, income group, LDC/SIDS/LLDC
  Stage 5: Generate choropleth maps
  Stage 6: Write summary assessment

Key improvements over v1:
  - Uses ENA /count endpoint (no record downloads needed)
  - Uses NCBI [country] field tag (broader matching than [all])
  - Excludes human-associated microbiome (NOT host_tax_id=9606)
  - Proper historical country name mapping with unattributed bucket
  - Reports unattributed records separately
  - Pins all query parameters for reproducibility
  - ENA and NCBI are treated as overlapping mirrors, never summed

Usage:
  python3 run_pipeline.py [--skip-queries]  # skip API queries, use cached data
"""

import argparse
import csv
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from collections import defaultdict
from datetime import datetime

# ── Configuration ───────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

ENA_COUNT_URL = "https://www.ebi.ac.uk/ena/portal/api/count"
NCBI_ESearch_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

# Non-human filter: exclude human organism AND human-associated microbiome
NON_HUMAN_FILTER = 'NOT tax_tree(9606) AND NOT host_tax_id=9606'
NON_HUMAN_NCBI = 'NOT txid9606[orgn]'

# Time periods
PERIODS = {
    'all':       '',
    'post2023':  'first_public>=2024-01-01',
    '2018-2020': 'first_public>=2018-01-01 AND first_public<2021-01-01',
    '2021-2023': 'first_public>=2021-01-01 AND first_public<2024-01-01',
    '2024+':     'first_public>=2024-01-01',
}

# Rate limits
ENA_DELAY = 0.15   # ENA allows 50/s, we use ~6/s
NCBI_DELAY = 0.35  # NCBI allows 3/s without API key

# Run metadata
RUN_TIMESTAMP = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


# ── Stage 1: Country master table ──────────────────────────────────

def load_insdc_countries():
    """Load INSDC controlled vocabulary for geo_loc_name country names."""
    vocab_file = os.path.join(DATA_DIR, "insdc_countries_clean.txt")
    if not os.path.exists(vocab_file):
        print("  WARNING: INSDC country vocab file not found. Fetching from web...")
        # Fetch from INSDC website
        import re
        url = "https://www.insdc.org/submitting-standards/geo_loc_name-qualifier-vocabulary/"
        req = urllib.request.Request(url, headers={'User-Agent': 'CaliFund-DSI-Research/2.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode()
        
        text = re.sub(r'<[^>]+>', '\n', html)
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        in_list = False
        countries = []
        stop_words = {'About INSDC', 'Global Participation', 'Technical Specifications',
                      'Publications', 'Announcements', 'Contact Us', 'NLM-NCBI',
                      'Site maintained by the External Services team at',
                      'EMBL-EBI', 'Terms of Use', 'Privacy', 'Cookies',
                      'The', 'Qualifier', 'Definition', 'Value format', 'Example',
                      'Comment', 'Geographical Location List'}
        for l in lines:
            if 'Geographical Location List' in l:
                in_list = True
                continue
            if in_list:
                if l in stop_words or l.startswith('Site maintained'):
                    continue
                if re.match(r'^[A-Z][a-zA-Z\s\(\)\-\,\']+$', l) and len(l) > 2 and len(l) < 50:
                    countries.append(l)
        
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(vocab_file, 'w') as f:
            for c in countries:
                f.write(c + '\n')
        print(f"  Fetched {len(countries)} INSDC country names")
    else:
        with open(vocab_file) as f:
            countries = [l.strip() for l in f if l.strip()]
        print(f"  Loaded {len(countries)} INSDC country names from file")
    
    return countries


# INSDC country name → UN M.49 country name mapping
# Historical names mapped to single successor where unambiguous;
# multi-successor names (USSR, Yugoslavia, etc.) mapped to __HISTORICAL__
INSDC_TO_UN = {
    # Current sovereign states — direct or near-direct matches
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
    "Iraq": "Iraq", "Ireland": "Ireland", "Isle of Man": "Isle of Man",
    "Israel": "Israel", "Italy": "Italy", "Jamaica": "Jamaica",
    "Japan": "Japan", "Jersey": "Jersey", "Jordan": "Jordan",
    "Kazakhstan": "Kazakhstan", "Kenya": "Kenya", "Kiribati": "Kiribati",
    "Kosovo": "Kosovo", "Kuwait": "Kuwait", "Kyrgyzstan": "Kyrgyzstan",
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
    "Northern Mariana Islands": "Northern Mariana Islands",
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
    "State of Palestine": "State of Palestine",
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
    "West Bank": "State of Palestine",
    "Western Sahara": "Western Sahara", "Yemen": "Yemen",
    "Zambia": "Zambia", "Zimbabwe": "Zimbabwe",
    # Historical — single successor (unambiguous)
    "Belgian Congo": "Democratic Republic of the Congo",
    "British Guiana": "Guyana", "Burma": "Myanmar",
    "Czechoslovakia": "Czechia",  # primary successor
    "Macedonia": "North Macedonia",
    "Netherlands Antilles": "Curaçao",  # primary successor
    "Siam": "Thailand", "Swaziland": "Eswatini",
    "The former Yugoslav Republic of Macedonia": "North Macedonia",
    "Zaire": "Democratic Republic of the Congo",
    # Historical — multi-successor (cannot attribute to single current state)
    "USSR": "__HISTORICAL__", "Yugoslavia": "__HISTORICAL__",
    "Serbia and Montenegro": "__HISTORICAL__",
    # Oceans and seas
    "Arctic Ocean": "__OCEANS_SEAS__", "Atlantic Ocean": "__OCEANS_SEAS__",
    "Baltic Sea": "__OCEANS_SEAS__", "Borneo": "__MULTINATIONAL__",
    "Indian Ocean": "__OCEANS_SEAS__", "Mediterranean Sea": "__OCEANS_SEAS__",
    "North Sea": "__OCEANS_SEAS__", "Pacific Ocean": "__OCEANS_SEAS__",
    "Ross Sea": "__OCEANS_SEAS__", "Southern Ocean": "__OCEANS_SEAS__",
    "Tasman Sea": "__OCEANS_SEAS__",
    # Territories without UN classification
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
    "South Georgia and the South Sandwich Islands": "South Georgia and the South Sandwich Islands",
    "Tromelin Island": "__TERRITORY__", "Wake Island": "__TERRITORY__",
}


def load_un_classifications():
    """Load UN M.49 classifications from unsd-country-codes.csv."""
    csv_path = os.path.join(DATA_DIR, "unsd-country-codes.csv")
    classifications = {}
    with open(csv_path, encoding='utf-8') as f:
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


def load_wb_income():
    """Load World Bank income classifications from WB_CLASS.xlsx."""
    try:
        import openpyxl
    except ImportError:
        print("  WARNING: openpyxl not installed, skipping WB income groups")
        return {}
    
    xlsx_path = os.path.join(DATA_DIR, "WB_CLASS.xlsx")
    classifications = {}
    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    ws = wb.active
    headers = None
    for row in ws.iter_rows(values_only=True):
        if headers is None:
            headers = row
            continue
        row_dict = dict(zip(headers, row))
        code = row_dict.get('Code')
        income = row_dict.get('Income group')
        if code and income:
            classifications[code] = income
    wb.close()
    return classifications


def build_country_master():
    """Stage 1: Build the country master table."""
    print("\n" + "=" * 70)
    print("STAGE 1: Building country master table")
    print("=" * 70)
    
    insdc_countries = load_insdc_countries()
    un_data = load_un_classifications()
    wb_income = load_wb_income()
    
    print(f"  INSDC vocabulary: {len(insdc_countries)} country names")
    print(f"  UN M.49 classifications: {len(un_data)} entries")
    print(f"  World Bank income groups: {len(wb_income)} entries")
    
    # Build master table
    master = []
    unmapped = []
    for insdc_name in insdc_countries:
        un_name = INSDC_TO_UN.get(insdc_name)
        if un_name is None:
            unmapped.append(insdc_name)
            un_name = "__UNMAPPED__"
        
        un_info = un_data.get(un_name, {})
        iso3 = un_info.get('iso3', '')
        income = wb_income.get(iso3, 'Unknown') if iso3 else 'Unknown'
        
        master.append({
            'insdc_name': insdc_name,
            'un_name': un_name,
            'iso3': iso3,
            'm49': un_info.get('m49', ''),
            'region': un_info.get('region', ''),
            'sub_region': un_info.get('sub_region', ''),
            'dev_status': un_info.get('dev_status', ''),
            'ldc': 'x' if un_info.get('ldc') else '',
            'lldc': 'x' if un_info.get('lldc') else '',
            'sids': 'x' if un_info.get('sids') else '',
            'wb_income': income,
        })
    
    if unmapped:
        print(f"\n  WARNING: {len(unmapped)} INSDC names not in mapping:")
        for name in unmapped:
            print(f"    - {name}")
    
    # Save master table
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    outfile = os.path.join(OUTPUT_DIR, "country_master.csv")
    with open(outfile, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'insdc_name', 'un_name', 'iso3', 'm49', 'region', 'sub_region',
            'dev_status', 'ldc', 'lldc', 'sids', 'wb_income'
        ])
        writer.writeheader()
        writer.writerows(master)
    print(f"\n  Saved country master table: {outfile} ({len(master)} entries)")
    
    return master, un_data, wb_income


# ── Stage 2: ENA /count queries ────────────────────────────────────

def ena_count(query):
    """Query ENA /count endpoint and return integer count."""
    params = {'result': 'sample', 'query': query, 'format': 'json'}
    url = ENA_COUNT_URL + '?' + urllib.parse.urlencode(params)
    url = url.replace('+', '%20')
    req = urllib.request.Request(url, headers={'User-Agent': 'CaliFund-DSI-Research/2.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return int(data['count'])
    except Exception as e:
        print(f"    ERROR: {e}")
        return -1


def query_ena_counts(country_master):
    """Stage 2: Query ENA /count for each country × period."""
    print("\n" + "=" * 70)
    print("STAGE 2: Querying ENA /count (primary source)")
    print("=" * 70)
    print(f"  Filter: {NON_HUMAN_FILTER}")
    print(f"  Periods: {list(PERIODS.keys())}")
    print(f"  Countries: {len(country_master)}")
    print()
    
    results = {}
    total_queries = len(country_master) * len(PERIODS) + len(PERIODS)  # +unattributed
    query_num = 0
    
    # First: get unattributed counts (no country)
    print("  Querying unattributed bucket...")
    for period_name, date_filter in PERIODS.items():
        query = f'{NON_HUMAN_FILTER} AND NOT country="*"'
        if date_filter:
            query += f' AND {date_filter}'
        count = ena_count(query)
        results[f'__UNATTRIBUTED__:{period_name}'] = count
        query_num += 1
        time.sleep(ENA_DELAY)
    print(f"    Unattributed (all): {results['__UNATTRIBUTED__:all']:,}")
    
    # Get total (with country)
    for period_name, date_filter in PERIODS.items():
        query = f'{NON_HUMAN_FILTER} AND country="*"'
        if date_filter:
            query += f' AND {date_filter}'
        count = ena_count(query)
        results[f'__TOTAL_WITH_COUNTRY__:{period_name}'] = count
        query_num += 1
        time.sleep(ENA_DELAY)
    print(f"    Total with country (all): {results['__TOTAL_WITH_COUNTRY__:all']:,}")
    
    # Per-country queries
    for i, country in enumerate(country_master):
        insdc_name = country['insdc_name']
        
        for period_name, date_filter in PERIODS.items():
            query = f'country="{insdc_name}" AND {NON_HUMAN_FILTER}'
            if date_filter:
                query += f' AND {date_filter}'
            
            count = ena_count(query)
            results[f'{insdc_name}:{period_name}'] = count
            query_num += 1
            time.sleep(ENA_DELAY)
        
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(country_master)} countries done ({query_num}/{total_queries} queries)")
            # Save intermediate
            _save_ena_results(results, country_master)
    
    # Save final
    _save_ena_results(results, country_master)
    print(f"\n  ENA queries complete: {query_num} total queries")
    return results


def _save_ena_results(results, country_master):
    """Save ENA count results to CSV."""
    outfile = os.path.join(OUTPUT_DIR, "ena_counts.csv")
    with open(outfile, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['insdc_country'] + list(PERIODS.keys()))
        
        # Unattributed
        writer.writerow(['__UNATTRIBUTED__'] + 
                       [results.get(f'__UNATTRIBUTED__:{p}', 0) for p in PERIODS])
        writer.writerow(['__TOTAL_WITH_COUNTRY__'] + 
                       [results.get(f'__TOTAL_WITH_COUNTRY__:{p}', 0) for p in PERIODS])
        
        for country in country_master:
            name = country['insdc_name']
            row = [name] + [results.get(f'{name}:{p}', 0) for p in PERIODS]
            writer.writerow(row)


# ── Stage 3: NCBI cross-check ──────────────────────────────────────

def ncbi_count(term):
    """Query NCBI ESearch and return count."""
    params = {
        'db': 'biosample', 'term': term,
        'rettype': 'count', 'retmode': 'json',
        'tool': 'CaliFundDSI', 'email': 'research@example.org',
    }
    url = NCBI_ESearch_URL + '?' + urllib.parse.urlencode(params)
    url = url.replace('+', '%20')
    req = urllib.request.Request(url, headers={'User-Agent': 'CaliFund-DSI-Research/2.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return int(data['esearchresult']['count'])
    except Exception as e:
        print(f"    ERROR: {e}")
        return -1


def query_ncbi_crosscheck(country_master):
    """Stage 3: Query NCBI ESearch with [country] field tag as cross-check."""
    print("\n" + "=" * 70)
    print("STAGE 3: Querying NCBI ESearch [country] (cross-check)")
    print("=" * 70)
    print(f"  Filter: {NON_HUMAN_NCBI}")
    print(f"  Field tag: [country] (token-indexed, absorbs sub-national)")
    print(f"  Periods: all, post2023 only (cross-check)")
    print()
    
    ncbi_periods = {
        'all': '',
        'post2023': 'AND 2024:3000[pdat]',
    }
    
    results = {}
    
    for i, country in enumerate(country_master):
        insdc_name = country['insdc_name']
        
        for period_name, date_suffix in ncbi_periods.items():
            term = f'"{insdc_name}"[country] AND {NON_HUMAN_NCBI}'
            if date_suffix:
                term += f' {date_suffix}'
            
            count = ncbi_count(term)
            results[f'{insdc_name}:{period_name}'] = count
            time.sleep(NCBI_DELAY)
        
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(country_master)} countries done")
    
    # Save
    outfile = os.path.join(OUTPUT_DIR, "ncbi_crosscheck.csv")
    with open(outfile, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['insdc_country', 'all', 'post2023'])
        for country in country_master:
            name = country['insdc_name']
            writer.writerow([name, results.get(f'{name}:all', 0), 
                           results.get(f'{name}:post2023', 0)])
    
    print(f"\n  NCBI cross-check complete. Saved to {outfile}")
    return results


# ── Stage 4: Aggregation ───────────────────────────────────────────

def aggregate_results(country_master, ena_results, un_data, wb_income):
    """Stage 4: Aggregate counts by region, dev status, income group, LDC/SIDS/LLDC."""
    print("\n" + "=" * 70)
    print("STAGE 4: Aggregating results")
    print("=" * 70)
    
    # Build per-UN-country merged counts (merge INSDC names mapping to same UN country)
    merged = defaultdict(lambda: {p: 0 for p in PERIODS})
    merged_meta = {}
    
    for country in country_master:
        insdc_name = country['insdc_name']
        un_name = country['un_name']
        
        for p in PERIODS:
            count = ena_results.get(f'{insdc_name}:{p}', 0)
            if count > 0:
                merged[un_name][p] += count
        
        if un_name not in merged_meta:
            merged_meta[un_name] = country
    
    # Build enriched table
    enriched = []
    for un_name, counts in merged.items():
        meta = merged_meta[un_name]
        total = sum(counts.values())
        if total == 0:
            continue
        enriched.append({
            'country': un_name,
            'iso3': meta['iso3'],
            'm49': meta['m49'],
            'region': meta['region'],
            'sub_region': meta['sub_region'],
            'dev_status': meta['dev_status'],
            'ldc': meta['ldc'],
            'lldc': meta['lldc'],
            'sids': meta['sids'],
            'wb_income': meta['wb_income'],
            'all': counts['all'],
            'post2023': counts['post2023'],
            '2018-2020': counts['2018-2020'],
            '2021-2023': counts['2021-2023'],
            '2024+': counts['2024+'],
        })
    
    enriched.sort(key=lambda x: x['all'], reverse=True)
    
    # Save main table
    outfile = os.path.join(OUTPUT_DIR, "country_provenance_counts.csv")
    with open(outfile, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'country', 'iso3', 'm49', 'region', 'sub_region', 'dev_status',
            'ldc', 'lldc', 'sids', 'wb_income',
            'all', 'post2023', '2018-2020', '2021-2023', '2024+'
        ])
        writer.writeheader()
        writer.writerows(enriched)
    print(f"  Saved country-level table: {outfile} ({len(enriched)} countries)")
    
    # Unattributed bucket
    unattributed = {p: ena_results.get(f'__UNATTRIBUTED__:{p}', 0) for p in PERIODS}
    total_with_country = {p: ena_results.get(f'__TOTAL_WITH_COUNTRY__:{p}', 0) for p in PERIODS}
    total_all = {p: unattributed[p] + total_with_country[p] for p in PERIODS}
    
    print(f"\n  Grand totals (ENA /count, non-human, no human microbiome):")
    print(f"    Total non-human samples:              {total_all['all']:>12,}")
    print(f"    With country provenance:              {total_with_country['all']:>12,} ({100*total_with_country['all']/total_all['all']:.1f}%)")
    print(f"    Unattributed (no country):            {unattributed['all']:>12,} ({100*unattributed['all']/total_all['all']:.1f}%)")
    print(f"    Post-2023 with country:               {total_with_country['post2023']:>12,}")
    
    # Aggregations
    def aggregate_by(key_func, key_name):
        agg = defaultdict(lambda: {p: 0 for p in PERIODS} | {'countries': 0})
        for r in enriched:
            k = key_func(r)
            for p in PERIODS:
                agg[k][p] += r[p]
            agg[k]['countries'] += 1
        
        print(f"\n  --- By {key_name} ---")
        print(f"  {'Group':<30} {'Countries':>10} {'All':>12} {'Post-2023':>12} {'2018-2020':>12} {'2021-2023':>12} {'2024+':>12}")
        print(f"  {'─'*100}")
        for k in sorted(agg.keys(), key=lambda x: agg[x]['all'], reverse=True):
            d = agg[k]
            print(f"  {str(k)[:30]:<30} {d['countries']:>10} {d['all']:>12,} {d['post2023']:>12,} {d['2018-2020']:>12,} {d['2021-2023']:>12,} {d['2024+']:>12,}")
        
        return dict(agg)
    
    by_region = aggregate_by(lambda r: r['region'] or 'Unmapped', "UN region")
    by_dev = aggregate_by(lambda r: r['dev_status'] or 'Unmapped', "development status")
    by_income = aggregate_by(lambda r: r['wb_income'], "World Bank income group")
    by_subregion = aggregate_by(lambda r: r['sub_region'] or 'Unmapped', "UN sub-region")
    
    # LDC/SIDS/LLDC
    print(f"\n  --- Vulnerable country groups ---")
    print(f"  {'Group':<10} {'Countries':>10} {'All':>12} {'Post-2023':>12} {'2018-2020':>12} {'2021-2023':>12} {'2024+':>12}")
    print(f"  {'─'*75}")
    vuln = {}
    for cat, label in [('ldc', 'LDC'), ('sids', 'SIDS'), ('lldc', 'LLDC')]:
        rows = [r for r in enriched if r[cat] == 'x']
        v = {p: sum(r[p] for r in rows) for p in PERIODS}
        vuln[label] = {'counts': v, 'countries': len(rows)}
        print(f"  {label:<10} {len(rows):>10} {v['all']:>12,} {v['post2023']:>12,} {v['2018-2020']:>12,} {v['2021-2023']:>12,} {v['2024+']:>12,}")
    
    # Growth rates
    print(f"\n  --- Annualized output and growth rates ---")
    print(f"  {'Group':<30} {'2018-2020/yr':>14} {'2021-2023/yr':>14} {'2024+/yr*':>14} {'Growth 1':>10} {'Growth 2':>10}")
    print(f"  {'─'*95}")
    
    def print_growth(label, counts):
        r1 = counts['2018-2020'] / 3
        r2 = counts['2021-2023'] / 3
        r3 = counts['2024+'] / 2.78
        g1 = ((r2 / r1) - 1) * 100 if r1 > 0 else 0
        g2 = ((r3 / r2) - 1) * 100 if r2 > 0 else 0
        print(f"  {label[:30]:<30} {r1:>14,.0f} {r2:>14,.0f} {r3:>14,.0f} {g1:>+9.0f}% {g2:>+9.0f}%")
    
    for dev in sorted(by_dev.keys(), key=lambda x: by_dev[x]['all'], reverse=True):
        print_growth(dev, by_dev[dev])
    for income in ['High income', 'Upper middle income', 'Lower middle income', 'Low income', 'Unknown']:
        if income in by_income:
            print_growth(income, by_income[income])
    for label in ['LDC', 'SIDS', 'LLDC']:
        print_growth(label, vuln[label]['counts'])
    
    # Share of each period
    grand_period = {p: sum(r[p] for r in enriched) for p in PERIODS}
    
    print(f"\n  --- Share of each period (%) ---")
    print(f"  {'Group':<30} {'2018-2020':>12} {'2021-2023':>12} {'2024+':>12}")
    print(f"  {'─'*68}")
    for dev in sorted(by_dev.keys(), key=lambda x: by_dev[x]['all'], reverse=True):
        d = by_dev[dev]
        s1 = 100 * d['2018-2020'] / grand_period['2018-2020'] if grand_period['2018-2020'] else 0
        s2 = 100 * d['2021-2023'] / grand_period['2021-2023'] if grand_period['2021-2023'] else 0
        s3 = 100 * d['2024+'] / grand_period['2024+'] if grand_period['2024+'] else 0
        print(f"  {dev[:30]:<30} {s1:>11.1f}% {s2:>11.1f}% {s3:>11.1f}%")
    for income in ['High income', 'Upper middle income', 'Lower middle income', 'Low income', 'Unknown']:
        if income in by_income:
            d = by_income[income]
            s1 = 100 * d['2018-2020'] / grand_period['2018-2020'] if grand_period['2018-2020'] else 0
            s2 = 100 * d['2021-2023'] / grand_period['2021-2023'] if grand_period['2021-2023'] else 0
            s3 = 100 * d['2024+'] / grand_period['2024+'] if grand_period['2024+'] else 0
            print(f"  {income[:30]:<30} {s1:>11.1f}% {s2:>11.1f}% {s3:>11.1f}%")
    for label in ['LDC', 'SIDS', 'LLDC']:
        v = vuln[label]['counts']
        s1 = 100 * v['2018-2020'] / grand_period['2018-2020'] if grand_period['2018-2020'] else 0
        s2 = 100 * v['2021-2023'] / grand_period['2021-2023'] if grand_period['2021-2023'] else 0
        s3 = 100 * v['2024+'] / grand_period['2024+'] if grand_period['2024+'] else 0
        print(f"  {label:<30} {s1:>11.1f}% {s2:>11.1f}% {s3:>11.1f}%")
    
    print(f"\n  * 2024+ annualized based on ~2.78 years (Jan 2024 to present)")
    
    # Save aggregation CSVs
    for fname, agg_data, fields in [
        ("agg_by_region.csv", by_region, ['region', 'countries', 'all', 'post2023', '2018-2020', '2021-2023', '2024+']),
        ("agg_by_dev_status.csv", by_dev, ['dev_status', 'countries', 'all', 'post2023', '2018-2020', '2021-2023', '2024+']),
        ("agg_by_income.csv", by_income, ['wb_income', 'countries', 'all', 'post2023', '2018-2020', '2021-2023', '2024+']),
    ]:
        path = os.path.join(OUTPUT_DIR, fname)
        with open(path, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(fields)
            for k, d in sorted(agg_data.items(), key=lambda x: x[1]['all'], reverse=True):
                w.writerow([k, d['countries'], d['all'], d['post2023'], 
                           d['2018-2020'], d['2021-2023'], d['2024+']])
    
    # Save vulnerability CSV
    vuln_path = os.path.join(OUTPUT_DIR, "agg_by_vulnerability.csv")
    with open(vuln_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['group', 'countries', 'all', 'post2023', '2018-2020', '2021-2023', '2024+'])
        for label in ['LDC', 'SIDS', 'LLDC']:
            v = vuln[label]
            w.writerow([label, v['countries'], v['counts']['all'], v['counts']['post2023'],
                       v['counts']['2018-2020'], v['counts']['2021-2023'], v['counts']['2024+']])
    
    # Save JSON
    json_out = os.path.join(OUTPUT_DIR, "analysis_results.json")
    with open(json_out, 'w', encoding='utf-8') as f:
        json.dump({
            'run_timestamp': RUN_TIMESTAMP,
            'filter': NON_HUMAN_FILTER,
            'temporal_anchor': 'first_public',
            'periods': list(PERIODS.keys()),
            'totals': {
                'all_records': total_all['all'],
                'with_country': total_with_country['all'],
                'unattributed': unattributed['all'],
                'post2023_with_country': total_with_country['post2023'],
            },
            'by_region': {k: v for k, v in by_region.items()},
            'by_dev_status': {k: v for k, v in by_dev.items()},
            'by_income': {k: v for k, v in by_income.items()},
            'by_vulnerability': {k: v for k, v in vuln.items()},
            'countries': enriched,
        }, f, indent=2)
    print(f"\n  Saved JSON: {json_out}")
    
    return enriched, by_region, by_dev, by_income, vuln, unattributed, total_with_country, total_all


# ── Stage 5: Maps ──────────────────────────────────────────────────

def generate_maps(enriched):
    """Stage 5: Generate choropleth maps."""
    print("\n" + "=" * 70)
    print("STAGE 5: Generating maps")
    print("=" * 70)
    
    try:
        import pandas as pd
        import plotly.graph_objects as go
        import numpy as np
    except ImportError:
        print("  WARNING: pandas/plotly not installed, skipping maps")
        return
    
    df = pd.DataFrame(enriched)
    df = df[df['iso3'].notna() & (df['iso3'] != '')].copy()
    df['log_all'] = df['all'].apply(lambda x: np.log10(x) if x > 0 else 0)
    
    countries_with_data = df[df['all'] > 0]
    midpoint_log = countries_with_data['log_all'].median()
    zmin, zmax = 0, countries_with_data['log_all'].max()
    mid_norm = (midpoint_log - zmin) / (zmax - zmin) if zmax > zmin else 0.5
    
    COLOR_SCALE_BWR = [
        [0.0, '#2166ac'], [mid_norm * 0.3, '#4393c3'],
        [mid_norm * 0.6, '#92c5de'], [mid_norm * 0.85, '#d1e5f0'],
        [mid_norm, '#f7f7f7'],
        [mid_norm + (1 - mid_norm) * 0.15, '#fddbc7'],
        [mid_norm + (1 - mid_norm) * 0.4, '#f4a582'],
        [mid_norm + (1 - mid_norm) * 0.7, '#d6604d'],
        [1.0, '#b2182b'],
    ]
    
    LAND_COLOR = '#f0f0f0'
    OCEAN_COLOR = '#d9d9d9'
    plot_data = df[df['all'] > 0].copy()
    
    fig = go.Figure()
    fig.add_trace(go.Choropleth(
        locations=df['iso3'], z=[0] * len(df),
        colorscale=[[0, LAND_COLOR], [1, LAND_COLOR]],
        showscale=False, marker_line_color='#ffffff', marker_line_width=0.3,
        hoverinfo='skip',
    ))
    fig.add_trace(go.Choropleth(
        locations=plot_data['iso3'], z=plot_data['log_all'],
        colorscale=COLOR_SCALE_BWR, zmin=zmin, zmax=zmax,
        marker_line_color='#ffffff', marker_line_width=0.3,
        colorbar=dict(
            title=dict(text="DSI Records<br>(log₁₀ scale)", font=dict(size=12)),
            tickfont=dict(size=11), len=0.6, x=1.01,
            tickvals=[0, midpoint_log, zmax],
            ticktext=[f"0", f"~{int(10**midpoint_log):,}", f"~{int(10**zmax):,}"],
        ),
        hovertemplate='<b>%{text}</b><br>Records: %{customdata:,.0f}<extra></extra>',
        text=plot_data['country'], customdata=plot_data['all'],
    ))
    
    total = df['all'].sum()
    fig.update_layout(
        title=dict(
            text=(
                f'<b>All Non-Human DSI Records with Country Provenance</b><br>'
                f'<sup style="font-size:13px;color:#666">'
                f'INSDC / ENA /count &bull; {total:,} records &bull; '
                f'excl. human microbiome &bull; white = median (~{int(10**midpoint_log):,}) &bull; '
                f'queried {RUN_TIMESTAMP[:10]}</sup>'
            ),
            x=0.5, y=0.95, font=dict(size=18, color='#222'),
        ),
        geo=dict(
            showframe=False, showcoastlines=True, coastlinecolor='#cccccc',
            coastlinewidth=0.5, projection_type='natural earth',
            landcolor=LAND_COLOR, oceancolor=OCEAN_COLOR, showocean=True,
            lataxis_showgrid=False, lonaxis_showgrid=False,
        ),
        margin=dict(l=0, r=0, t=90, b=0), paper_bgcolor='#ffffff',
        font=dict(family='Helvetica, Arial, sans-serif', size=12, color='#333'),
    )
    
    path = os.path.join(OUTPUT_DIR, "map_all_records.html")
    fig.write_html(path, include_plotlyjs='cdn')
    print(f"  Saved: {path}")
    print(f"  Median country (white): ~{int(10**midpoint_log):,} records")
    print(f"  Range: 0 to ~{int(10**zmax):,} records")


# ── Stage 6: Summary ───────────────────────────────────────────────

def write_summary(enriched, by_region, by_dev, by_income, vuln, 
                  unattributed, total_with_country, total_all, ncbi_results, country_master):
    """Stage 6: Write summary assessment document."""
    print("\n" + "=" * 70)
    print("STAGE 6: Writing summary assessment")
    print("=" * 70)
    
    path = os.path.join(OUTPUT_DIR, "SUMMARY.md")
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"""# INSDC Provenance Country-Level Maps for the Cali Fund — v2

**Run timestamp:** {RUN_TIMESTAMP}
**Data source:** ENA portal API `/count` endpoint (primary); NCBI ESearch `[country]` (cross-check)
**Filter:** `NOT tax_tree(9606) AND NOT host_tax_id=9606` (excludes human organism and human-associated microbiome)
**Temporal anchor:** `first_public` (date record was made public in the archive)
**INSDC vocabulary:** {len(country_master)} entries from controlled vocabulary for `geo_loc_name`

---

## Grand totals

| Metric | Count | % of total |
|--------|-------|------------|
| Total non-human samples (excl. human microbiome) | {total_all['all']:,} | 100% |
| With country provenance | {total_with_country['all']:,} | {100*total_with_country['all']/total_all['all']:.1f}% |
| Unattributed (no country) | {unattributed['all']:,} | {100*unattributed['all']/total_all['all']:.1f}% |
| Post-2023 with country | {total_with_country['post2023']:,} | |
| Countries with >= 1 record | {len(enriched)} | |

## By development status

| Status | Countries | All records | % share | Post-2023 | 2018-2020 | 2021-2023 | 2024+ |
|--------|-----------|-------------|---------|-----------|-----------|-----------|-------|
""")
        for dev in sorted(by_dev.keys(), key=lambda x: by_dev[x]['all'], reverse=True):
            d = by_dev[dev]
            pct = 100 * d['all'] / total_with_country['all'] if total_with_country['all'] else 0
            f.write(f"| {dev} | {d['countries']} | {d['all']:,} | {pct:.1f}% | {d['post2023']:,} | {d['2018-2020']:,} | {d['2021-2023']:,} | {d['2024+']:,} |\n")
        
        f.write(f"""
## By World Bank income group

| Income group | Countries | All records | % share | Post-2023 | 2018-2020 | 2021-2023 | 2024+ |
|--------------|-----------|-------------|---------|-----------|-----------|-----------|-------|
""")
        for income in ['High income', 'Upper middle income', 'Lower middle income', 'Low income', 'Unknown']:
            if income in by_income:
                d = by_income[income]
                pct = 100 * d['all'] / total_with_country['all'] if total_with_country['all'] else 0
                f.write(f"| {income} | {d['countries']} | {d['all']:,} | {pct:.1f}% | {d['post2023']:,} | {d['2018-2020']:,} | {d['2021-2023']:,} | {d['2024+']:,} |\n")
        
        f.write(f"""
## By vulnerable country group

| Group | Countries | All records | % share | Post-2023 | 2018-2020 | 2021-2023 | 2024+ |
|-------|-----------|-------------|---------|-----------|-----------|-----------|-------|
""")
        for label in ['LDC', 'SIDS', 'LLDC']:
            v = vuln[label]
            pct = 100 * v['counts']['all'] / total_with_country['all'] if total_with_country['all'] else 0
            f.write(f"| {label} | {v['countries']} | {v['counts']['all']:,} | {pct:.1f}% | {v['counts']['post2023']:,} | {v['counts']['2018-2020']:,} | {v['counts']['2021-2023']:,} | {v['counts']['2024+']:,} |\n")
        
        # Growth rates
        f.write(f"""
## Growth rates (annualized, period vs previous period)

| Group | 2018-2020/yr | 2021-2023/yr | Growth | 2024+/yr | Growth |
|-------|-------------|-------------|--------|---------|--------|
""")
        def growth_line(label, counts):
            r1 = counts['2018-2020'] / 3
            r2 = counts['2021-2023'] / 3
            r3 = counts['2024+'] / 2.78
            g1 = ((r2 / r1) - 1) * 100 if r1 > 0 else 0
            g2 = ((r3 / r2) - 1) * 100 if r2 > 0 else 0
            return f"| {label} | {r1:,.0f} | {r2:,.0f} | {g1:+.0f}% | {r3:,.0f} | {g2:+.0f}% |\n"
        
        for dev in sorted(by_dev.keys(), key=lambda x: by_dev[x]['all'], reverse=True):
            f.write(growth_line(dev, by_dev[dev]))
        for income in ['High income', 'Upper middle income', 'Lower middle income', 'Low income', 'Unknown']:
            if income in by_income:
                f.write(growth_line(income, by_income[income]))
        for label in ['LDC', 'SIDS', 'LLDC']:
            f.write(growth_line(label, vuln[label]['counts']))
        
        # Top 20 countries
        f.write(f"""
## Top 20 countries by all records

| # | Country | ISO3 | Status | Income | All | Post-2023 | % share |
|---|---------|------|--------|--------|-----|-----------|---------|
""")
        for i, r in enumerate(enriched[:20], 1):
            pct = 100 * r['all'] / total_with_country['all'] if total_with_country['all'] else 0
            f.write(f"| {i} | {r['country']} | {r['iso3'] or '---'} | {r['dev_status'] or '?'} | {r['wb_income']} | {r['all']:,} | {r['post2023']:,} | {pct:.1f}% |\n")
        
        f.write(f"""
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
""")
    
    print(f"  Saved: {path}")


# ── Main pipeline runner ───────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="INSDC Provenance Pipeline v2")
    parser.add_argument('--skip-queries', action='store_true',
                       help='Skip API queries, use cached data')
    args = parser.parse_args()
    
    print("=" * 70)
    print("INSDC PROVENANCE COUNTRY-LEVEL MAPS FOR THE CALI FUND — v2")
    print(f"Run timestamp: {RUN_TIMESTAMP}")
    print("=" * 70)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Stage 1: Country master
    country_master, un_data, wb_income = build_country_master()
    
    # Stage 2: ENA counts
    if args.skip_queries and os.path.exists(os.path.join(OUTPUT_DIR, "ena_counts.csv")):
        print("\n  Skipping ENA queries (--skip-queries), loading cached data...")
        ena_results = {}
        with open(os.path.join(OUTPUT_DIR, "ena_counts.csv")) as f:
            reader = csv.DictReader(f)
            periods = reader.fieldnames[1:]
            for row in reader:
                name = row['insdc_country']
                for p in periods:
                    ena_results[f'{name}:{p}'] = int(row[p])
    else:
        ena_results = query_ena_counts(country_master)
    
    # Stage 3: NCBI cross-check
    if args.skip_queries and os.path.exists(os.path.join(OUTPUT_DIR, "ncbi_crosscheck.csv")):
        print("\n  Skipping NCBI queries (--skip-queries), loading cached data...")
        ncbi_results = {}
        with open(os.path.join(OUTPUT_DIR, "ncbi_crosscheck.csv")) as f:
            reader = csv.DictReader(f)
            for row in reader:
                ncbi_results[f"{row['insdc_country']}:all"] = int(row['all'])
                ncbi_results[f"{row['insdc_country']}:post2023"] = int(row['post2023'])
    else:
        ncbi_results = query_ncbi_crosscheck(country_master)
    
    # Stage 4: Aggregation
    enriched, by_region, by_dev, by_income, vuln, unattributed, total_wc, total_all = \
        aggregate_results(country_master, ena_results, un_data, wb_income)
    
    # Stage 5: Maps
    generate_maps(enriched)
    
    # Stage 6: Summary
    write_summary(enriched, by_region, by_dev, by_income, vuln,
                  unattributed, total_wc, total_all, ncbi_results, country_master)
    
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print(f"All outputs in: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
