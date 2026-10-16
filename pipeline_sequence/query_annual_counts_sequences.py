#!/usr/bin/env python3
"""
Annual Per-Country ENA Query Script — SEQUENCES
================================================

Same methodology as the sample-based pipeline, but queries result=sequence
instead of result=sample. This counts individual nucleotide sequence records
rather than BioSample records.

Key differences from sample pipeline:
  - result=sequence (one record per nucleotide sequence entry, not per BioSample)
  - More conservative rate limiting (1.0s delay, 30s pause every 100 queries)
  - Output: pipeline_sequence/output/annual_counts_sequences.csv

All other methodology is identical:
  - Non-human filter: NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
  - Temporal anchor: first_public
  - Country matching: country="X" with collision exclusions
  - 378 country values (296 vocab + 82 non-vocab)
  - 20 collision exclusions
"""

import csv
import json
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime

# ── Configuration ───────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

ENA_COUNT_URL = "https://www.ebi.ac.uk/ena/portal/api/count"
ENA_DELAY = 1.0  # Conservative: 1 query per second
PAUSE_EVERY = 100  # Pause every N queries
PAUSE_DURATION = 30  # Seconds to pause

RESULT_TYPE = "sequence"  # Changed from "sample"

RUN_TIMESTAMP = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

# Non-human filter: exclude human organism, human microbiome, synthetic constructs
NON_HUMAN_FILTER = 'NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)'

# Years to query
YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]

# Date filters for each year
def year_filter(year):
    return f'first_public>={year}-01-01 AND first_public<{year+1}-01-01'

PRE_2018_FILTER = 'first_public<2018-01-01'
UNDATED_FILTER = 'NOT first_public>=1900-01-01'

# ── Collision exclusions (identical to sample pipeline) ─────────────

COLLISION_EXCLUSIONS = {
    'Guinea': ['Papua New Guinea', 'Equatorial Guinea', 'Guinea-Bissau'],
    'Korea': ['South Korea', 'North Korea'],
    'Republic of the Congo': ['Democratic Republic of the Congo'],
    'Sudan': ['South Sudan'],
    'Virgin Islands': ['British Virgin Islands'],
    'Macedonia': ['The former Yugoslav Republic of Macedonia'],
    'Micronesia': ['Micronesia, Federated States of'],
    'Samoa': ['American Samoa'],
    'Serbia': ['Serbia and Montenegro'],
    'Georgia': ['USA', 'South Georgia and the South Sandwich Islands'],
    'Mongolia': ['China'],
    'Mexico': ['USA'],
    'Jersey': ['USA'],
    'Ireland': ['United Kingdom'],
    'Jamaica': ['USA'],
    'Lebanon': ['USA'],
    'Jordan': ['USA'],
    'Columbia': ['Canada'],
    'Congo': ['Republic of the Congo', 'Democratic Republic of the Congo'],
    'Antarctic': ['Antarctica'],
    'China': ['South China Sea', 'East China Sea'],
    'Japan': ['Japan Sea', 'Sea of Japan'],
    'Greenland': ['Greenland Sea'],
}

def build_country_clause(insdc_name):
    """Build the country= clause with collision exclusions if needed."""
    clause = f'country="{insdc_name}"'
    if insdc_name in COLLISION_EXCLUSIONS:
        for longer_name in COLLISION_EXCLUSIONS[insdc_name]:
            clause += f' AND NOT country="{longer_name}"'
    return clause


# ── Non-vocab country-field values (identical to sample pipeline) ───

NON_VOCAB_COUNTRIES = [
    'United States', 'United States of America', 'US', 'U.S.', 'United_States_of_America',
    'UK', 'Britain', 'Great Britain', 'England', 'Scotland', 'Wales', 'Northern Ireland',
    'Turkiye',
    'Cote d\'Ivoire',
    'Vietnam', 'Viet_Nam',
    'Syrian Arab Republic',
    'Cambodge',
    'Sri_Lanka',
    'Lao_People\'s_Democratic_Republic',
    'The Bahamas',
    'Columbia',
    'Congo',
    'Sugadaira', 'Yakushima', 'Yakushidake', 'Iriomote', 'Teshio',
    'Tomakomai', 'Sasayama', 'Yoshidayama', 'Yona', 'Nippon',
    'Shenzhen', 'Xi\'an', 'Lijiang', 'Ailaoshan', 'Nabanhe',
    'Valencia', 'Mississippi River', 'Atacama Desert',
    'Helgoland', 'Barro Colorado Island',
    'missing', 'NULL', 'na', 'None', 'not applicable', 'not appicable',
    'not collected', 'unknown', '(no country)',
    'GAZ',
    'Antarctic',
    'Black Sea', 'Red Sea',
    'Coral Sea', 'Caspian Sea', 'Barents Sea',
    'Bering Sea', 'Caribbean Sea', 'Sargasso Sea', 'Norwegian Sea',
    'Kara Sea', 'Laptev Sea', 'East Siberian Sea', 'Chukchi Sea',
    'Beaufort Sea', 'Amundsen Sea', 'Weddell Sea',
    'Labrador Sea', 'Greenland Sea', 'Celtic Sea',
    'Japan Sea', 'Okhotsk Sea', 'Sea of Japan',
    'North Atlantic Ocean', 'South Atlantic Ocean',
    'North Pacific Ocean', 'South Pacific Ocean',
    'South China Sea', 'East China Sea',
]


# ── ENA /count query ────────────────────────────────────────────────

def ena_count_get(query):
    """Query ENA /count via GET."""
    url = f"{ENA_COUNT_URL}?result={RESULT_TYPE}&format=json&query={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'CaliFund-DSI-Research/3.0'})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
        if isinstance(data, list):
            return int(data[0]['count']) if data else 0
        return int(data.get('count', 0))

def ena_count_post(query):
    """Query ENA /count via POST (for long queries with collision exclusions)."""
    data = urllib.parse.urlencode({
        'result': RESULT_TYPE,
        'format': 'json',
        'query': query,
    }).encode()
    req = urllib.request.Request(ENA_COUNT_URL, data=data, method='POST',
                                 headers={'User-Agent': 'CaliFund-DSI-Research/3.0',
                                          'Content-Type': 'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode())
        if isinstance(result, list):
            return int(result[0]['count']) if result else 0
        return int(result.get('count', 0))

def ena_count(query, use_post=False):
    """Query ENA /count with retry on transient errors."""
    for attempt in range(3):
        try:
            if use_post:
                return ena_count_post(query)
            else:
                return ena_count_get(query)
        except Exception as e:
            if attempt < 2:
                wait = 5 * (attempt + 1)  # 5s, 10s backoff
                print(f"    Retry {attempt+1}/3 after {wait}s: {e}")
                time.sleep(wait)
                continue
            print(f"    ERROR (3 retries): {e}")
            return -1


# ── Main ────────────────────────────────────────────────────────────

def load_insdc_countries():
    """Load INSDC controlled vocabulary for geo_loc_name country names."""
    vocab_file = os.path.join(DATA_DIR, "insdc_countries_clean.txt")
    with open(vocab_file) as f:
        countries = [line.strip() for line in f if line.strip()]
    return countries

def main():
    print("=" * 70)
    print(f"ANNUAL PER-COUNTRY ENA /count QUERIES — RESULT={RESULT_TYPE.upper()}")
    print(f"Run timestamp: {RUN_TIMESTAMP}")
    print("=" * 70)
    print(f"\n  Filter: {NON_HUMAN_FILTER}")
    print(f"  Result type: {RESULT_TYPE}")
    print(f"  Temporal anchor: first_public")
    print(f"  Years: {YEARS[0]}–{YEARS[-1]} + pre_2018 + undated")
    print(f"  Rate limiting: {ENA_DELAY}s delay, {PAUSE_DURATION}s pause every {PAUSE_EVERY} queries")
    print(f"  Collision exclusions: {len(COLLISION_EXCLUSIONS)} short names")

    countries = load_insdc_countries()
    non_vocab = NON_VOCAB_COUNTRIES
    all_countries = countries + non_vocab
    print(f"  Countries (vocab): {len(countries)}")
    print(f"  Non-vocab values: {len(non_vocab)}")
    print(f"  Total to query: {len(all_countries)}")

    columns = ['country', 'pre_2018'] + [str(y) for y in YEARS] + ['undated', 'all']

    date_slices = [('pre_2018', PRE_2018_FILTER)] + \
                  [(str(y), year_filter(y)) for y in YEARS] + \
                  [('undated', UNDATED_FILTER)]

    results = {}
    errors = 0
    query_count = 0
    total_queries = len(all_countries) * (len(date_slices) + 1) + len(date_slices) * 2

    # ── Unattributed queries ────────────────────────────────────────
    print(f"\n  Querying unattributed (NOT country=\"*\")...")
    unattributed = {}
    for col_name, date_clause in date_slices:
        query = f'NOT country="*" AND {NON_HUMAN_FILTER}'
        if date_clause:
            query += f' AND {date_clause}'
        count = ena_count(query)
        unattributed[col_name] = count
        query_count += 1
        if count < 0:
            errors += 1
        time.sleep(ENA_DELAY)
        if query_count % PAUSE_EVERY == 0:
            print(f"    [{query_count}/{total_queries}] Pausing {PAUSE_DURATION}s...")
            time.sleep(PAUSE_DURATION)

    query = f'NOT country="*" AND {NON_HUMAN_FILTER}'
    unattributed['all'] = ena_count(query)
    query_count += 1
    time.sleep(ENA_DELAY)
    print(f"    Unattributed (all): {unattributed['all']:,}")
    results['__UNATTRIBUTED__'] = unattributed

    # ── Attributed total queries ────────────────────────────────────
    print(f"\n  Querying attributed total (country=\"*\")...")
    attributed = {}
    for col_name, date_clause in date_slices:
        query = f'country="*" AND {NON_HUMAN_FILTER}'
        if date_clause:
            query += f' AND {date_clause}'
        count = ena_count(query)
        attributed[col_name] = count
        query_count += 1
        if count < 0:
            errors += 1
        time.sleep(ENA_DELAY)
        if query_count % PAUSE_EVERY == 0:
            print(f"    [{query_count}/{total_queries}] Pausing {PAUSE_DURATION}s...")
            time.sleep(PAUSE_DURATION)

    query = f'country="*" AND {NON_HUMAN_FILTER}'
    attributed['all'] = ena_count(query)
    query_count += 1
    time.sleep(ENA_DELAY)
    print(f"    Attributed total (all): {attributed['all']:,}")
    results['__ATTRIBUTED_TOTAL__'] = attributed

    # ── Per-country queries ─────────────────────────────────────────
    print(f"\n  Querying {len(all_countries)} countries × {len(date_slices)+1} slices...")
    print(f"  Estimated time: ~{total_queries * ENA_DELAY / 60:.0f} minutes + pauses")

    for i, country_name in enumerate(all_countries):
        has_collision = country_name in COLLISION_EXCLUSIONS
        country_clause = build_country_clause(country_name)
        use_post = has_collision

        country_results = {}
        for col_name, date_clause in date_slices:
            query = f'{country_clause} AND {NON_HUMAN_FILTER}'
            if date_clause:
                query += f' AND {date_clause}'
            count = ena_count(query, use_post=use_post)
            country_results[col_name] = count
            query_count += 1
            if count < 0:
                errors += 1
            time.sleep(ENA_DELAY)
            if query_count % PAUSE_EVERY == 0:
                print(f"    [{query_count}/{total_queries}] Pausing {PAUSE_DURATION}s...")
                time.sleep(PAUSE_DURATION)

        query = f'{country_clause} AND {NON_HUMAN_FILTER}'
        country_results['all'] = ena_count(query, use_post=use_post)
        query_count += 1
        time.sleep(ENA_DELAY)
        if query_count % PAUSE_EVERY == 0:
            print(f"    [{query_count}/{total_queries}] Pausing {PAUSE_DURATION}s...")
            time.sleep(PAUSE_DURATION)

        results[country_name] = country_results

        if (i + 1) % 50 == 0:
            print(f"    {i+1}/{len(all_countries)} countries done ({query_count}/{total_queries} queries, {errors} errors)")

    print(f"\n  Queries complete: {query_count} total, {errors} errors")

    # ── Write output CSV ────────────────────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    outfile = os.path.join(OUTPUT_DIR, "annual_counts_sequences.csv")
    with open(outfile, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        row = {'country': '__UNATTRIBUTED__'}
        row.update({col: unattributed.get(col, 0) for col in columns if col != 'country'})
        writer.writerow(row)
        row = {'country': '__ATTRIBUTED_TOTAL__'}
        row.update({col: attributed.get(col, 0) for col in columns if col != 'country'})
        writer.writerow(row)
        for country_name in all_countries:
            row = {'country': country_name}
            cr = results.get(country_name, {})
            row.update({col: cr.get(col, 0) for col in columns if col != 'country'})
            writer.writerow(row)

    print(f"\n  Saved: {outfile}")

    # ── Reconciliation check ────────────────────────────────────────
    print(f"\n  Reconciliation check (per-year):")
    print(f"  {'Year':<10} {'Sum(countries)':>15} {'Attributed':>15} {'Diff':>10}")
    print(f"  {'-'*52}")
    for col_name in ['pre_2018'] + [str(y) for y in YEARS] + ['undated']:
        country_sum = sum(results.get(c, {}).get(col_name, 0)
                         for c in all_countries if results.get(c, {}).get(col_name, 0) > 0)
        attr_total = attributed.get(col_name, 0)
        diff = attr_total - country_sum
        print(f"  {col_name:<10} {country_sum:>15,} {attr_total:>15,} {diff:>10,}")
    country_sum_all = sum(results.get(c, {}).get('all', 0)
                         for c in all_countries if results.get(c, {}).get('all', 0) > 0)
    attr_all = attributed.get('all', 0)
    diff_all = attr_all - country_sum_all
    print(f"  {'all':<10} {country_sum_all:>15,} {attr_all:>15,} {diff_all:>10,}")

    # ── Grand totals ────────────────────────────────────────────────
    total_all = unattributed.get('all', 0) + attributed.get('all', 0)
    print(f"\n  Grand totals:")
    print(f"    Total non-human sequences:                     {total_all:,}")
    print(f"    Attributed (with country):                     {attributed.get('all', 0):,}")
    print(f"    Unattributed (no country):                     {unattributed.get('all', 0):,}")
    print(f"    Undated (no first_public, attributed):         ~{sum(results.get(c, {}).get('undated', 0) for c in all_countries if results.get(c, {}).get('undated', 0) > 0):,}")

    print(f"\n{'='*70}")
    print(f"DONE — Output: {outfile}")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
