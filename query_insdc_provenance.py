#!/usr/bin/env python3
"""
Query NCBI ESearch for per-country counts of non-human BioSample records
with geographic provenance (country attribute), across three categories:
  1. All legacy records (total)
  2. Post-2023 records (submission date 2024+)
  3. Environmentally sourced records

INSDC country names come from the controlled vocabulary at:
  https://www.insdc.org/submitting-standards/geo_loc_name-qualifier-vocabulary/

NCBI BioSample mirrors the INSDC and is the US node of the collaboration.
The country field uses the same controlled vocabulary.
"""

import urllib.request
import urllib.parse
import json
import time
import sys
import os

COUNTRY_LIST = "/tmp/insdc_countries_clean.txt"
OUTPUT_DIR = "/Users/jasminekindness/IIFB_COP17/ahteg_allocation"
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

# Rate limiting: NCBI allows 3 requests/second without API key
DELAY = 0.35

def load_countries():
    with open(COUNTRY_LIST) as f:
        return [line.strip() for line in f if line.strip()]

def esearch_count(query_term):
    """Query NCBI ESearch and return count as integer."""
    params = {
        'db': 'biosample',
        'term': query_term,
        'rettype': 'count',
        'retmode': 'json'
    }
    url = BASE_URL + '?' + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'CaliFund-DSI-Research/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return int(data['esearchresult']['count'])
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return -1

def query_category(countries, category_name, extra_term):
    """Query all countries for a given category and save results."""
    outfile = os.path.join(OUTPUT_DIR, f"insdc_counts_{category_name}.csv")
    results = []
    
    # Also get the total for this category (all countries combined)
    total_query = f"NOT txid9606[orgn] AND country[all] {extra_term}"
    total = esearch_count(total_query)
    print(f"Total for {category_name}: {total}")
    results.append(("__TOTAL__", total))
    time.sleep(DELAY)
    
    for i, country in enumerate(countries):
        # Build query: non-human AND country="X" AND [optional extra]
        query = f'NOT txid9606[orgn] AND country="{country}"[all]'
        if extra_term:
            query += f" AND {extra_term}"
        
        count = esearch_count(query)
        results.append((country, count))
        
        if (i + 1) % 50 == 0:
            print(f"  {category_name}: {i+1}/{len(countries)} countries done")
            # Save intermediate results
            with open(outfile, 'w') as f:
                f.write("country,count\n")
                for c, n in results:
                    f.write(f'"{c}",{n}\n')
        
        time.sleep(DELAY)
    
    # Save final results
    with open(outfile, 'w') as f:
        f.write("country,count\n")
        for c, n in results:
            f.write(f'"{c}",{n}\n')
    
    print(f"Saved {category_name} to {outfile}")
    return results

def main():
    countries = load_countries()
    print(f"Loaded {len(countries)} INSDC country names")
    
    # Category 1: All non-human biosamples with country provenance
    print("\n=== Category 1: All non-human records with country ===")
    cat1 = query_category(countries, "all_legacy", "")
    
    # Category 2: Post-2023 (submission date 2024+)
    print("\n=== Category 2: Post-2023 records (2024+) ===")
    cat2 = query_category(countries, "post2023", "2024[sddat]")
    
    # Category 3: Environmental samples
    print("\n=== Category 3: Environmentally sourced records ===")
    cat3 = query_category(countries, "environmental", "environmental[all]")
    
    # Summary
    print("\n=== SUMMARY ===")
    print(f"Total non-human with country: {cat1[0][1]}")
    print(f"Sum of per-country (cat1): {sum(n for _, n in cat1 if n > 0 and isinstance(n, int))}")
    print(f"Total post-2023 with country: {cat2[0][1]}")
    print(f"Sum of per-country (cat2): {sum(n for _, n in cat2 if n > 0 and isinstance(n, int))}")
    print(f"Total environmental with country: {cat3[0][1]}")
    print(f"Sum of per-country (cat3): {sum(n for _, n in cat3 if n > 0 and isinstance(n, int))}")

if __name__ == "__main__":
    main()
