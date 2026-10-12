#!/usr/bin/env python3
"""
Annual Per-Country ENA Query Script
====================================

Queries ENA /count for annual per-country counts of non-human DSI records,
with collision exclusions, undated bucket, and synthetic construct exclusion.

Key methodology (from annual_evaluation.md):
  - Non-human filter: NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)
    (excludes human organism, human microbiome, and synthetic constructs)
  - Temporal anchor: first_public (78.5% coverage; undated bucket reported separately)
  - Country matching: country="X" with collision exclusions for 9 short names
  - Unattributed: NOT country="*" (records with no country field set)
  - result=sample (one record per BioSample, the correct grain)

Output: pipeline/output/annual_counts.csv
  Columns: insdc_country, pre_2018, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, undated, all
  Plus rows: __UNATTRIBUTED__, __ATTRIBUTED_TOTAL__ (for reconciliation)

Usage:
  python3 query_annual_counts.py
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
ENA_DELAY = 0.15  # ENA allows 50/s; we use ~6/s

RUN_TIMESTAMP = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

# Non-human filter: exclude human organism, human microbiome, synthetic constructs
NON_HUMAN_FILTER = 'NOT tax_tree(9606) AND NOT host_tax_id=9606 AND NOT tax_tree(32630)'

# Years to query
YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

# Date filters for each year
def year_filter(year):
    return f'first_public>={year}-01-01 AND first_public<{year+1}-01-01'

PRE_2018_FILTER = 'first_public<2018-01-01'
UNDATED_FILTER = 'NOT first_public>=1900-01-01'

# ── Collision exclusions ────────────────────────────────────────────
# country="X" is an ANY-TOKEN match. It matches records where X appears
# as a word-boundary-prefixed token ANYWHERE in the country field, not
# just as the leading token before the first colon.
#
# This causes two types of false matches:
# 1. Cross-country collisions: "Guinea" matches "Papua New Guinea"
# 2. Sub-national collisions: "Mexico" matches "USA: New Mexico"
#
# Both are fixed by adding AND NOT country="<absorbing name>" exclusions.

COLLISION_EXCLUSIONS = {
    # Cross-country collisions (shorter name absorbs longer name)
    'Guinea': ['Papua New Guinea', 'Equatorial Guinea', 'Guinea-Bissau'],
    'Korea': ['South Korea', 'North Korea'],
    'Republic of the Congo': ['Democratic Republic of the Congo'],
    'Sudan': ['South Sudan'],
    'Virgin Islands': ['British Virgin Islands'],
    'Macedonia': ['The former Yugoslav Republic of Macedonia'],
    'Micronesia': ['Micronesia, Federated States of'],
    'Samoa': ['American Samoa'],
    'Serbia': ['Serbia and Montenegro'],
    # Sub-national collisions (country name appears in another country's region)
    'Georgia': ['USA'],           # US state of Georgia vs country of Georgia
    'Mongolia': ['China'],        # Inner Mongolia (China) vs country of Mongolia
    'Mexico': ['USA'],            # New Mexico (US state) vs country of Mexico
    'Jersey': ['USA'],            # New Jersey (US state) vs Channel Island of Jersey
    'Ireland': ['United Kingdom'], # Northern Ireland (UK) vs Republic of Ireland
    'Jamaica': ['USA'],           # Jamaica, Queens (US) vs country of Jamaica
    'Lebanon': ['USA'],           # Lebanon, NH (US) vs country of Lebanon
    'Jordan': ['USA'],            # USA: Jordan vs country of Jordan
}

def build_country_clause(insdc_name):
    """Build the country= clause with collision exclusions if needed."""
    clause = f'country="{insdc_name}"'
    if insdc_name in COLLISION_EXCLUSIONS:
        for longer_name in COLLISION_EXCLUSIONS[insdc_name]:
            clause += f' AND NOT country="{longer_name}"'
    return clause


# ── ENA /count query ────────────────────────────────────────────────

def ena_count_get(query):
    """Query ENA /count via GET (for short queries)."""
    url = f"{ENA_COUNT_URL}?result=sample&format=json&query={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'CaliFund-DSI-Research/3.0'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
        if isinstance(data, list):
            return int(data[0]['count']) if data else 0
        return int(data.get('count', 0))

def ena_count_post(query):
    """Query ENA /count via POST (for long queries with collision exclusions)."""
    data = urllib.parse.urlencode({
        'result': 'sample',
        'format': 'json',
        'query': query,
    }).encode()
    req = urllib.request.Request(ENA_COUNT_URL, data=data, method='POST',
                                 headers={'User-Agent': 'CaliFund-DSI-Research/3.0',
                                          'Content-Type': 'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req, timeout=60) as resp:
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
                time.sleep(2 ** attempt)  # 1s, 2s backoff
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
    print("ANNUAL PER-COUNTRY ENA /count QUERIES")
    print(f"Run timestamp: {RUN_TIMESTAMP}")
    print("=" * 70)
    print(f"\n  Filter: {NON_HUMAN_FILTER}")
    print(f"  Temporal anchor: first_public")
    print(f"  Years: {YEARS[0]}–{YEARS[-1]} + pre_2018 + undated")
    print(f"  Collision exclusions: {len(COLLISION_EXCLUSIONS)} short names")

    countries = load_insdc_countries()
    print(f"  Countries: {len(countries)}")

    # Column order for output
    columns = ['insdc_country', 'pre_2018'] + [str(y) for y in YEARS] + ['undated', 'all']

    # All date slices (pre_2018, each year, undated) — "all" is computed
    date_slices = [('pre_2018', PRE_2018_FILTER)] + \
                  [(str(y), year_filter(y)) for y in YEARS] + \
                  [('undated', UNDATED_FILTER)]

    results = {}  # {country_name: {col_name: count}}
    errors = 0
    query_count = 0
    total_queries = len(countries) * len(date_slices) + len(date_slices) * 2  # +unattributed +attributed_total

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
    # Also query unattributed "all" (no date filter)
    query = f'NOT country="*" AND {NON_HUMAN_FILTER}'
    unattributed['all'] = ena_count(query)
    query_count += 1
    time.sleep(ENA_DELAY)
    print(f"    Unattributed (all): {unattributed['all']:,}")
    results['__UNATTRIBUTED__'] = unattributed

    # ── Attributed total queries (for reconciliation) ───────────────
    print(f"\n  Querying attributed total (country=\"*\") for reconciliation...")
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
    query = f'country="*" AND {NON_HUMAN_FILTER}'
    attributed['all'] = ena_count(query)
    query_count += 1
    time.sleep(ENA_DELAY)
    print(f"    Attributed total (all): {attributed['all']:,}")
    results['__ATTRIBUTED_TOTAL__'] = attributed

    # ── Per-country queries ─────────────────────────────────────────
    print(f"\n  Querying {len(countries)} countries × {len(date_slices)+1} slices...")

    for i, country_name in enumerate(countries):
        has_collision = country_name in COLLISION_EXCLUSIONS
        country_clause = build_country_clause(country_name)
        use_post = has_collision  # POST for long collision queries

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

        # "all" = no date filter
        query = f'{country_clause} AND {NON_HUMAN_FILTER}'
        country_results['all'] = ena_count(query, use_post=use_post)
        query_count += 1
        time.sleep(ENA_DELAY)

        results[country_name] = country_results

        if (i + 1) % 50 == 0:
            print(f"    {i+1}/{len(countries)} countries done ({query_count}/{total_queries} queries)")

    print(f"\n  Queries complete: {query_count} total, {errors} errors")

    # ── Write output CSV ────────────────────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    outfile = os.path.join(OUTPUT_DIR, "annual_counts.csv")
    with open(outfile, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        # Unattributed row
        row = {'insdc_country': '__UNATTRIBUTED__'}
        row.update({col: unattributed.get(col, 0) for col in columns if col != 'insdc_country'})
        writer.writerow(row)
        # Attributed total row
        row = {'insdc_country': '__ATTRIBUTED_TOTAL__'}
        row.update({col: attributed.get(col, 0) for col in columns if col != 'insdc_country'})
        writer.writerow(row)
        # Country rows
        for country_name in countries:
            row = {'insdc_country': country_name}
            cr = results.get(country_name, {})
            row.update({col: cr.get(col, 0) for col in columns if col != 'insdc_country'})
            writer.writerow(row)

    print(f"\n  Saved: {outfile}")

    # ── Reconciliation check ────────────────────────────────────────
    print(f"\n  Reconciliation check (per-year):")
    print(f"  {'Year':<10} {'Sum(countries)':>15} {'Attributed':>15} {'Diff':>10}")
    print(f"  {'-'*52}")
    for col_name in ['pre_2018'] + [str(y) for y in YEARS] + ['undated']:
        country_sum = sum(results.get(c, {}).get(col_name, 0)
                         for c in countries if results.get(c, {}).get(col_name, 0) > 0)
        attr_total = attributed.get(col_name, 0)
        diff = attr_total - country_sum
        print(f"  {col_name:<10} {country_sum:>15,} {attr_total:>15,} {diff:>10,}")
    # "all" reconciliation
    country_sum_all = sum(results.get(c, {}).get('all', 0)
                         for c in countries if results.get(c, {}).get('all', 0) > 0)
    attr_all = attributed.get('all', 0)
    diff_all = attr_all - country_sum_all
    print(f"  {'all':<10} {country_sum_all:>15,} {attr_all:>15,} {diff_all:>10,}")
    if diff_all > 0:
        print(f"  → Non-vocab orphans (attributed but not in 296-name vocab): {diff_all:,}")

    # ── Grand totals ────────────────────────────────────────────────
    total_all = unattributed.get('all', 0) + attributed.get('all', 0)
    print(f"\n  Grand totals:")
    print(f"    Total non-human (excl. microbiome + synthetic):  {total_all:,}")
    print(f"    Attributed (with country):                       {attributed.get('all', 0):,}")
    print(f"    Unattributed (no country):                       {unattributed.get('all', 0):,}")
    print(f"    Undated (no first_public, attributed):           ~{sum(results.get(c, {}).get('undated', 0) for c in countries if results.get(c, {}).get('undated', 0) > 0):,}")

    print(f"\n{'='*70}")
    print(f"DONE — Output: {outfile}")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
