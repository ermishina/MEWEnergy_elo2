#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 MEWEnergy Project Contributors

"""
fetch_pvwatts.py - Fetch solar production estimates from NREL PVWatts API v8

Uses the NREL PVWatts API to estimate annual solar energy production based on
location coordinates and system parameters.

API Documentation: https://developer.nrel.gov/docs/solar/pvwatts/v8/

Usage:
    python fetch_pvwatts.py --geocode-file raw/geocode_results.json --output raw/
    python fetch_pvwatts.py --lat 42.3601 --lon -71.0942 --capacity 5.0

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
PVWATTS_URL = "https://developer.nrel.gov/api/pvwatts/v8.json"
SOLAR_RESOURCE_URL = "https://developer.nrel.gov/api/solar/solar_resource/v1.json"
RATE_LIMIT_DELAY = 0.5  # NREL allows more frequent requests than Nominatim


# Default PV system parameters (standard residential installation)
DEFAULT_PARAMS = {
    "system_capacity": 5.0,     # kW DC
    "module_type": 0,           # 0=Standard, 1=Premium, 2=Thin film
    "array_type": 0,            # 0=Fixed open rack, 1=Fixed roof mount
    "losses": 14,               # System losses (%)
    "azimuth": 180,             # South-facing (degrees)
    "tilt": None,               # Will use latitude as default
}


def fetch_pvwatts_estimate(lat: float, lon: float, system_params: dict = None, api_key: str = None) -> dict:
    """
    Fetch PVWatts solar production estimate for a single location.
    
    Args:
        lat: Latitude
        lon: Longitude
        system_params: Dict of PV system parameters (optional)
        api_key: NREL API key (optional, uses env var if not provided)
    
    Returns:
        dict with PVWatts outputs and metadata
    """
    key = api_key or NREL_API_KEY
    if not key:
        return {
            "success": False,
            "error": "NREL_API_KEY not found. Set environment variable or pass api_key parameter.",
            "outputs": None
        }
    
    params = {**DEFAULT_PARAMS, **(system_params or {})}
    
    # Use latitude as tilt if not specified
    if params["tilt"] is None:
        params["tilt"] = abs(lat)
    
    request_params = {
        "api_key": key,
        "lat": lat,
        "lon": lon,
        "system_capacity": params["system_capacity"],
        "module_type": params["module_type"],
        "array_type": params["array_type"],
        "losses": params["losses"],
        "tilt": params["tilt"],
        "azimuth": params["azimuth"]
    }
    
    try:
        response = requests.get(PVWATTS_URL, params=request_params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data and data["errors"]:
            return {
                "success": False,
                "error": "; ".join(data["errors"]),
                "outputs": None,
                "inputs": data.get("inputs", {})
            }
        
        return {
            "success": True,
            "error": None,
            "outputs": data.get("outputs", {}),
            "inputs": data.get("inputs", {}),
            "station_info": data.get("station_info", {})
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "outputs": None
        }


def fetch_solar_resource(lat: float, lon: float, api_key: str = None) -> dict:
    """
    Fetch solar resource data (GHI, DNI, etc.) for a location.
    
    Args:
        lat: Latitude
        lon: Longitude
        api_key: NREL API key
    
    Returns:
        dict with solar resource data
    """
    key = api_key or NREL_API_KEY
    if not key:
        return {"success": False, "error": "API key not found", "outputs": None}
    
    params = {"api_key": key, "lat": lat, "lon": lon}
    
    try:
        response = requests.get(SOLAR_RESOURCE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data and data["errors"]:
            return {"success": False, "error": "; ".join(data["errors"]), "outputs": None}
        
        return {
            "success": True,
            "error": None,
            "outputs": data.get("outputs", {})
        }
    
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e), "outputs": None}


def fetch_pvwatts_batch(locations: list, system_params: dict = None, output_dir: str = "raw") -> dict:
    """
    Fetch PVWatts data for multiple locations.
    
    Args:
        locations: List of dicts with 'id', 'lat', 'lon' keys
        system_params: Optional system parameters to use for all locations
        output_dir: Directory to save raw results
    
    Returns:
        dict containing all results and metadata
    """
    results = {
        "metadata": {
            "source": "NREL PVWatts API v8",
            "endpoint": PVWATTS_URL,
            "fetch_timestamp": datetime.utcnow().isoformat() + "Z",
            "system_params": {**DEFAULT_PARAMS, **(system_params or {})},
            "total_locations": len(locations),
            "successful": 0,
            "failed": 0
        },
        "data": []
    }
    
    print(f"Fetching PVWatts estimates for {len(locations)} locations...")
    
    for i, loc in enumerate(locations):
        print(f"  [{i+1}/{len(locations)}] Processing: {loc.get('id', 'unknown')} ({loc['lat']:.4f}, {loc['lon']:.4f})...")
        
        # Fetch PVWatts production estimate
        pvwatts_result = fetch_pvwatts_estimate(loc['lat'], loc['lon'], system_params)
        
        # Fetch solar resource data
        solar_result = fetch_solar_resource(loc['lat'], loc['lon'])
        
        record = {
            "id": loc.get("id", f"loc_{i+1}"),
            "lat": loc["lat"],
            "lon": loc["lon"],
            "region": loc.get("region", "Unknown"),
            "input_address": loc.get("input_address", ""),
            "pvwatts": pvwatts_result,
            "solar_resource": solar_result
        }
        
        results["data"].append(record)
        
        if pvwatts_result["success"]:
            results["metadata"]["successful"] += 1
            ac_annual = pvwatts_result["outputs"].get("ac_annual", 0)
            print(f"    ✓ Annual production: {ac_annual:,.0f} kWh")
        else:
            results["metadata"]["failed"] += 1
            print(f"    ✗ Error: {pvwatts_result['error']}")
        
        # Rate limiting
        if i < len(locations) - 1:
            time.sleep(RATE_LIMIT_DELAY)
    
    # Save raw results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_file = output_path / "pvwatts_results.json"
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
            locations.append({
                "id": record.get("id"),
                "lat": record["lat"],
                "lon": record["lon"],
                "region": record.get("region", "Unknown"),
                "input_address": record.get("input_address", "")
            })
    
    return locations


def main():
    parser = argparse.ArgumentParser(
        description="Fetch solar production estimates from NREL PVWatts API"
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
        "--capacity", type=float, default=5.0,
        help="System capacity in kW (default: 5.0)"
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
    
    system_params = {"system_capacity": args.capacity}
    
    if args.lat is not None and args.lon is not None:
        # Single location query
        locations = [{
            "id": "manual_query",
            "lat": args.lat,
            "lon": args.lon
        }]
    elif args.geocode_file:
        # Batch query from geocode results
        locations = load_locations_from_geocode(args.geocode_file)
        if not locations:
            print("Error: No valid locations found in geocode file")
            return
    else:
        print("Error: Provide either --geocode-file or both --lat and --lon")
        return
    
    fetch_pvwatts_batch(locations, system_params, args.output)


if __name__ == "__main__":
    main()