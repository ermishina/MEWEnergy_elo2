#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 MEWEnergy Project Contributors

"""
fetch_rates.py - Fetch utility electricity rates from NREL Utility Rates API

Uses the NREL Utility Rates API v3 to retrieve local electricity rates for
residential, commercial, and industrial sectors.

API Documentation: https://developer.nrel.gov/docs/electricity/utility-rates-v3/

Usage:
    python fetch_rates.py --geocode-file raw/geocode_results.json --output raw/
    python fetch_rates.py --lat 42.3601 --lon -71.0942 --sector residential

Environment:
    NREL_API_KEY: Your NREL API key (get one at https://developer.nrel.gov/signup/)
"""

import requests
import json
import time
import argparse
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# NREL API Configuration
NREL_API_KEY = os.getenv('NREL_API_KEY')
UTILITY_RATES_URL = "https://developer.nrel.gov/api/utility_rates/v3.json"
RATE_LIMIT_DELAY = 0.5


# SREC prices by state (USD per MWh) - conservative estimates
SREC_PRICES = {
    "Massachusetts": 280.0,
    "New Jersey": 220.0,
    "Pennsylvania": 45.0,
    "District of Columbia": 420.0,
    "Maryland": 60.0,
    "Illinois": 70.0,
    "Ohio": 15.0,
    "Virginia": 35.0,
    "Delaware": 40.0,
    "Rhode Island": 300.0,
}

# State abbreviation to full name mapping
STATE_ABBREV = {
    "MA": "Massachusetts", "NJ": "New Jersey", "PA": "Pennsylvania",
    "DC": "District of Columbia", "MD": "Maryland", "IL": "Illinois",
    "OH": "Ohio", "VA": "Virginia", "DE": "Delaware", "RI": "Rhode Island",
    "CA": "California", "TX": "Texas", "FL": "Florida", "AZ": "Arizona",
    "CO": "Colorado", "WA": "Washington", "NY": "New York", "GA": "Georgia",
}


def fetch_utility_rate(lat: float, lon: float, sector: str = "residential", api_key: str = None) -> dict:
    """
    Fetch utility electricity rate for a location.
    
    Args:
        lat: Latitude
        lon: Longitude
        sector: Rate sector ('residential', 'commercial', 'industrial')
        api_key: NREL API key
    
    Returns:
        dict with utility rate information
    """
    key = api_key or NREL_API_KEY
    if not key:
        return {
            "success": False,
            "error": "NREL_API_KEY not found",
            "rate": None
        }
    
    params = {"api_key": key, "lat": lat, "lon": lon}
    
    try:
        response = requests.get(UTILITY_RATES_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data and data["errors"]:
            return {
                "success": False,
                "error": "; ".join(data["errors"]),
                "rate": None
            }
        
        outputs = data.get("outputs", {})
        
        # Extract rate based on sector
        rate = None
        rate_key_options = [
            sector,                    # e.g., "residential"
            f"{sector}_rate",          # e.g., "residential_rate"
            "utility_rate",            # fallback
        ]
        
        for key in rate_key_options:
            if key in outputs and isinstance(outputs[key], (int, float)):
                rate = float(outputs[key])
                break
        
        # Get utility name
        utility_name = None
        for key in ["utility_name", "utility", "name"]:
            if key in outputs and isinstance(outputs[key], str):
                utility_name = outputs[key]
                break
        
        return {
            "success": True,
            "error": None,
            "rate": rate,
            "sector": sector,
            "utility_name": utility_name,
            "raw_outputs": outputs
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "rate": None
        }


def get_srec_price(state_name: str) -> float:
    """Get SREC price for a state (returns 0 if no SREC program)."""
    return SREC_PRICES.get(state_name, 0.0)


def fetch_rates_batch(locations: list, sectors: list = None, output_dir: str = "raw") -> dict:
    """
    Fetch utility rates for multiple locations.
    
    Args:
        locations: List of dicts with 'id', 'lat', 'lon' keys
        sectors: List of sectors to query (default: ['residential'])
        output_dir: Directory to save raw results
    
    Returns:
        dict containing all results and metadata
    """
    if sectors is None:
        sectors = ["residential"]
    
    results = {
        "metadata": {
            "source": "NREL Utility Rates API v3",
            "endpoint": UTILITY_RATES_URL,
            "fetch_timestamp": datetime.utcnow().isoformat() + "Z",
            "sectors_queried": sectors,
            "total_locations": len(locations),
            "successful": 0,
            "failed": 0
        },
        "srec_prices": SREC_PRICES,
        "data": []
    }
    
    print(f"Fetching utility rates for {len(locations)} locations...")
    
    for i, loc in enumerate(locations):
        print(f"  [{i+1}/{len(locations)}] Processing: {loc.get('id', 'unknown')}...")
        
        record = {
            "id": loc.get("id", f"loc_{i+1}"),
            "lat": loc["lat"],
            "lon": loc["lon"],
            "region": loc.get("region", "Unknown"),
            "input_address": loc.get("input_address", ""),
            "rates": {},
            "srec_price": 0.0,
            "state": None
        }
        
        # Get state from address details if available
        state_abbrev = loc.get("state_abbrev")
        state_name = loc.get("state_name")
        
        if state_abbrev and state_abbrev in STATE_ABBREV:
            state_name = STATE_ABBREV[state_abbrev]
        
        if state_name:
            record["state"] = state_name
            record["srec_price"] = get_srec_price(state_name)
        
        # Fetch rates for each sector
        any_success = False
        for sector in sectors:
            rate_result = fetch_utility_rate(loc['lat'], loc['lon'], sector)
            record["rates"][sector] = rate_result
            
            if rate_result["success"]:
                any_success = True
                print(f"    ✓ {sector}: ${rate_result['rate']:.3f}/kWh" if rate_result['rate'] else f"    ✓ {sector}: rate not available")
            else:
                print(f"    ✗ {sector}: {rate_result['error']}")
        
        results["data"].append(record)
        
        if any_success:
            results["metadata"]["successful"] += 1
        else:
            results["metadata"]["failed"] += 1
        
        # Rate limiting
        if i < len(locations) - 1:
            time.sleep(RATE_LIMIT_DELAY)
    
    # Save raw results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_file = output_path / "utility_rates_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    print(f"Success rate: {results['metadata']['successful']}/{results['metadata']['total_locations']}")
    
    return results


def load_locations_from_geocode(filepath: str) -> list:
    """Load locations from geocode results JSON file."""
    with open(filepath, 'r') as f:
        geocode_data = json.load(f)
    
    locations = []
    for record in geocode_data.get("data", []):
        if record.get("success") and record.get("lat") and record.get("lon"):
            # Try to extract state from address details
            address_details = record.get("address_details", {})
            state = address_details.get("state")
            
            locations.append({
                "id": record.get("id"),
                "lat": record["lat"],
                "lon": record["lon"],
                "region": record.get("region", "Unknown"),
                "input_address": record.get("input_address", ""),
                "state_name": state
            })
    
    return locations


def main():
    parser = argparse.ArgumentParser(
        description="Fetch utility electricity rates from NREL Utility Rates API"
    )
    parser.add_argument(
        "--geocode-file", "-g",
        help="Path to geocode_results.json from fetch_geocode.py"
    )
    parser.add_argument(
        "--lat", type=float,
        help="Latitude for single location query"
    )
    parser.add_argument(
        "--lon", type=float,
        help="Longitude for single location query"
    )
    parser.add_argument(
        "--sector", default="residential",
        choices=["residential", "commercial", "industrial"],
        help="Utility rate sector (default: residential)"
    )
    parser.add_argument(
        "--all-sectors", action="store_true",
        help="Query all sectors (residential, commercial, industrial)"
    )
    parser.add_argument(
        "--output", "-o", default="raw",
        help="Output directory for raw data (default: raw)"
    )
    parser.add_argument(
        "--api-key", "-k",
        help="NREL API key (overrides NREL_API_KEY env var)"
    )
    
    args = parser.parse_args()
    
    if args.api_key:
        global NREL_API_KEY
        NREL_API_KEY = args.api_key
    
    sectors = ["residential", "commercial", "industrial"] if args.all_sectors else [args.sector]
    
    if args.lat is not None and args.lon is not None:
        locations = [{"id": "manual_query", "lat": args.lat, "lon": args.lon}]
    elif args.geocode_file:
        locations = load_locations_from_geocode(args.geocode_file)
        if not locations:
            print("Error: No valid locations found in geocode file")
            return
    else:
        print("Error: Provide either --geocode-file or both --lat and --lon")
        return
    
    fetch_rates_batch(locations, sectors, args.output)


if __name__ == "__main__":
    main()