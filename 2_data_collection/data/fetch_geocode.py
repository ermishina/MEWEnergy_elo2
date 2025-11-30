#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 MEWEnergy Project Contributors

"""
fetch_geocode.py - Geocode addresses to latitude/longitude coordinates

Uses OpenStreetMap Nominatim API to convert addresses to geographic coordinates.
Results are saved to raw/geocode_results.json

Usage:
    python fetch_geocode.py [--addresses-file ADDRESSES_FILE] [--output OUTPUT_DIR]

Example:
    python fetch_geocode.py --addresses-file sample_addresses.txt --output raw/
"""

import requests
import json
import time
import argparse
import os
from datetime import datetime
from pathlib import Path


# Nominatim API configuration
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_USER_AGENT = "MEWEnergy/1.0 (MIT Emerging Talent CDSP Project)"
RATE_LIMIT_DELAY = 1.1  # Nominatim requires at least 1 second between requests


# Sample addresses for demonstration (covering different US regions/climates)
SAMPLE_ADDRESSES = [
    {"id": "MA_001", "address": "77 Holworthy St Boston MA 02121", "region": "Northeast"},
    {"id": "CA_001", "address": "2257 E Tyler Ave, Fresno, CA 93701", "region": "West"},
    {"id": "TX_001", "address": "908 Jewell St, Austin, TX 78704", "region": "South"},
    {"id": "FL_001", "address": "400 Biscayne Boulevard, Miami, FL 33132", "region": "Southeast"},
    {"id": "AZ_001", "address": "100 North Central Avenue, Phoenix, AZ 85004", "region": "Southwest"},
    {"id": "IL_001", "address": "233 South Wacker Drive, Chicago, IL 60606", "region": "Midwest"},
    {"id": "CO_001", "address": "1144 15th Street, Denver, CO 80202", "region": "Mountain"},
    {"id": "WA_001", "address": "400 Broad Street, Seattle, WA 98109", "region": "Pacific Northwest"},
    {"id": "NJ_001", "address": "1 Main St, Newark, NJ 07102", "region": "Northeast"},
    {"id": "DC_001", "address": "1600 Pennsylvania Ave NW, Washington, DC 20500", "region": "Mid-Atlantic"},
    {"id": "PA_001", "address": "1234 Market St, Philadelphia, PA 19107", "region": "Northeast"}
]


def geocode_address(address: str, country_code: str = "us") -> dict:
    """
    Geocode a single address using Nominatim API.
    
    Args:
        address: Full address string to geocode
        country_code: ISO country code to restrict search (default: "us")
    
    Returns:
        dict with keys: lat, lon, display_name, success, error (if any)
    """
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "countrycodes": country_code,
        "addressdetails": 1
    }
    headers = {"User-Agent": NOMINATIM_USER_AGENT}
    
    try:
        response = requests.get(NOMINATIM_BASE_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json()
        
        if results:
            result = results[0]
            return {
                "lat": float(result["lat"]),
                "lon": float(result["lon"]),
                "display_name": result.get("display_name", ""),
                "address_details": result.get("address", {}),
                "success": True,
                "error": None
            }
        else:
            return {
                "lat": None,
                "lon": None,
                "display_name": None,
                "address_details": {},
                "success": False,
                "error": "Address not found"
            }
    
    except requests.exceptions.RequestException as e:
        return {
            "lat": None,
            "lon": None,
            "display_name": None,
            "address_details": {},
            "success": False,
            "error": str(e)
        }


def fetch_geocode_data(addresses: list, output_dir: str = "raw") -> dict:
    """
    Fetch geocoding data for multiple addresses.
    
    Args:
        addresses: List of dicts with 'id' and 'address' keys
        output_dir: Directory to save raw results
    
    Returns:
        dict containing all geocoding results and metadata
    """
    results = {
        "metadata": {
            "source": "OpenStreetMap Nominatim API",
            "endpoint": NOMINATIM_BASE_URL,
            "fetch_timestamp": datetime.utcnow().isoformat() + "Z",
            "total_addresses": len(addresses),
            "successful": 0,
            "failed": 0
        },
        "data": []
    }
    
    print(f"Geocoding {len(addresses)} addresses...")
    
    for i, addr_info in enumerate(addresses):
        print(f"  [{i+1}/{len(addresses)}] Processing: {addr_info['address'][:50]}...")
        
        geocode_result = geocode_address(addr_info["address"])
        
        record = {
            "id": addr_info.get("id", f"addr_{i+1}"),
            "input_address": addr_info["address"],
            "region": addr_info.get("region", "Unknown"),
            **geocode_result
        }
        
        results["data"].append(record)
        
        if geocode_result["success"]:
            results["metadata"]["successful"] += 1
            print(f"    ✓ Found: ({geocode_result['lat']:.4f}, {geocode_result['lon']:.4f})")
        else:
            results["metadata"]["failed"] += 1
            print(f"    ✗ Error: {geocode_result['error']}")
        
        # Rate limiting
        if i < len(addresses) - 1:
            time.sleep(RATE_LIMIT_DELAY)
    
    # Save raw results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_file = output_path / "geocode_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    print(f"Success rate: {results['metadata']['successful']}/{results['metadata']['total_addresses']}")
    
    return results


def load_addresses_from_file(filepath: str) -> list:
    """Load addresses from a text file (one address per line)."""
    addresses = []
    with open(filepath, 'r') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if line and not line.startswith('#'):
                addresses.append({
                    "id": f"addr_{i+1:03d}",
                    "address": line,
                    "region": "Unknown"
                })
    return addresses


def main():
    parser = argparse.ArgumentParser(
        description="Geocode addresses using OpenStreetMap Nominatim API"
    )
    parser.add_argument(
        "--addresses-file", "-f",
        help="Path to file containing addresses (one per line)"
    )
    parser.add_argument(
        "--output", "-o",
        default="raw",
        help="Output directory for raw data (default: raw)"
    )
    parser.add_argument(
        "--use-samples",
        action="store_true",
        help="Use built-in sample addresses for demonstration"
    )
    
    args = parser.parse_args()
    
    if args.addresses_file:
        addresses = load_addresses_from_file(args.addresses_file)
    elif args.use_samples:
        addresses = SAMPLE_ADDRESSES
    else:
        print("Using built-in sample addresses. Use --addresses-file to specify custom addresses.")
        addresses = SAMPLE_ADDRESSES
    
    fetch_geocode_data(addresses, args.output)


if __name__ == "__main__":
    main()