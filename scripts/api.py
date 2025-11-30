# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Project Contributors

import requests
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (prefer file next to this module)
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv()  # fallback to cwd if provided

# Function for geocoding (ZIP → lat/lon) via Nominatim OSM
def geocode_postcode(postcode, country="US"):
    """
    Returns (lat, lon) or None if not found.
    For Europe-wide usage, consider Nominatim with country code or another geocoding API.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "postalcode": postcode,
        "country": country,
        "format": "json",
        "limit": 1
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    res = resp.json()
    if not res:
        return None
    lat = float(res[0]["lat"])
    lon = float(res[0]["lon"])
    return lat, lon

# Function for geocoding addresses via Nominatim OSM
def geocode_address(address):
    """
    Returns (lat, lon) or None if not found.
    Takes a full address string and returns coordinates.
    Optimized for US addresses.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "countrycodes": "us",  # Restrict to US addresses
        "addressdetails": 1
    }
    headers = {
        "User-Agent": "MEWEnergy Solar Analysis Tool/1.0 (https://github.com/mewenergy; mewenergy@research.edu)"
    }

    # Rate limiting - Nominatim requires 1 request/second minimum
    # Add extra delay to be safe
    time.sleep(2)  # 2 seconds between requests to be respectful
    resp = requests.get(url, params=params, headers=headers)
    resp.raise_for_status()
    res = resp.json()
    if not res:
        return None
    lat = float(res[0]["lat"])
    lon = float(res[0]["lon"])
    return lat, lon

# Function to query PVWatts (Version 8)
# Function to query Solar Resource Data
def solar_resource_data(lat, lon, api_key=None):
    """
    Calls the NREL Solar Resource API and returns solar radiation data.
    See: https://developer.nrel.gov/docs/solar/solar-resource-v1/

    Returns:
        dict: JSON response with average solar radiation data (DNI, GHI, lat_tilt)
    """
    if api_key is None:
        api_key = os.getenv('NREL_API_KEY')
        if not api_key:
            raise ValueError("NREL_API_KEY not found in environment variables")

    url = "https://developer.nrel.gov/api/solar/solar_resource/v1.json"
    params = {
        "api_key": api_key,
        "lat": lat,
        "lon": lon
    }

    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()

def pvwatts_estimate(lat, lon, system_capacity_kw=5.0,
                     module_type=0, array_type=0,
                     tilt=None, azimuth=None,
                     losses=14, api_key=None):
    """
    Calls the PVWatts API and returns the JSON response dict.
    See documentation: GET /api/pvwatts/v8
    """
    if api_key is None:
        api_key = os.getenv('NREL_API_KEY')
        if not api_key:
            raise ValueError("NREL_API_KEY not found in environment variables")

    url = "https://developer.nrel.gov/api/pvwatts/v8.json"

    # Ensure losses is in percent format (not decimal)
    if isinstance(losses, float) and losses < 1:
        losses = losses * 100

    # Set default values for required parameters if not provided
    if tilt is None:
        tilt = lat  # Use latitude as default tilt angle (optimal for most locations)
    if azimuth is None:
        azimuth = 180  # South-facing (180 degrees) is optimal in northern hemisphere

    params = {
        "api_key": api_key,
        "lat": lat,
        "lon": lon,
        "system_capacity": system_capacity_kw,
        "module_type": module_type,
        "array_type": array_type,
        "losses": losses,
        "tilt": tilt,
        "azimuth": azimuth
    }

    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()

def utility_rate(lat, lon, sector="residential", api_key=None):
    """
    Fetches local electricity rate via NREL Utility Rates API.
    Endpoint: /api/utility_rates/v3.json

    Args:
        lat (float): Latitude
        lon (float): Longitude
        sector (str): One of 'residential', 'commercial', 'industrial'
        api_key (str|None): NREL API key (from env if None)

    Returns:
        dict: { 'rate': float|None, 'sector': str, 'utility_name': str|None, 'raw': dict }
    """
    if api_key is None:
        api_key = os.getenv('NREL_API_KEY')
        if not api_key:
            raise ValueError("NREL_API_KEY not found in environment variables")

    url = "https://developer.nrel.gov/api/utility_rates/v3.json"
    params = {
        "api_key": api_key,
        "lat": lat,
        "lon": lon,
    }

    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    outputs = data.get("outputs", {}) if isinstance(data, dict) else {}

    # Try multiple common keys; API typically returns 'residential', 'commercial', 'industrial'
    rate = None
    if isinstance(outputs, dict):
        # standard keys
        rate = outputs.get(sector)
        # fallbacks
        if rate is None:
            rate = outputs.get(f"{sector}_rate")
        if rate is None:
            # generic fallbacks sometimes observed
            for k in ("utility_rate", "residential"):  # prefer residential if present
                if k in outputs and isinstance(outputs[k], (int, float)):
                    rate = outputs[k]
                    break

    utility_name = None
    # Utility metadata locations vary; check common spots
    for key in ("utility_name", "utility", "name"):
        if key in outputs and isinstance(outputs[key], str):
            utility_name = outputs[key]
            break

    return {
        "rate": rate if isinstance(rate, (int, float)) else None,
        "sector": sector,
        "utility_name": utility_name,
        "raw": data,
    }

# Function for direct coordinate query
def get_solar_info_by_coordinates(lat, lon, api_key=None):
    """
    Retrieves solar resource data directly using coordinates.
    """
    print(f"Using coordinates: Lat {lat}, Lon {lon}")

    # Retrieve solar resource data
    print("\n=== Solar Resource Data ===")
    solar_data = solar_resource_data(lat, lon, api_key)

    if "errors" in solar_data and solar_data["errors"]:
        print("Error retrieving solar resource data:", solar_data["errors"])
        return None
    else:
        outputs = solar_data.get("outputs", {})

        # DNI (Direct Normal Irradiance)
        dni = outputs.get("avg_dni", {})
        print(f"DNI (Direct Normal Irradiance) - Annual average: {dni.get('annual', 'N/A')} kWh/m²/day")

        # GHI (Global Horizontal Irradiance)
        ghi = outputs.get("avg_ghi", {})
        print(f"GHI (Global Horizontal Irradiance) - Annual average: {ghi.get('annual', 'N/A')} kWh/m²/day")

        # Lat Tilt (Latitude Tilt)
        lat_tilt = outputs.get("avg_lat_tilt", {})
        print(f"Lat Tilt - Annual average: {lat_tilt.get('annual', 'N/A')} kWh/m²/day")

        return solar_data

def interactive_solar_query():
    """
    Interactive function to get solar data by address or coordinates
    """
    print("=== Solar Resource Data Tool ===")
    print("1. Enter address")
    print("2. Enter coordinates directly")

    choice = input("Choose option (1 or 2): ").strip()

    if choice == "1":
        address = input("Enter address: ").strip()
        if not address:
            print("No address entered")
            return

        print(f"Searching for coordinates for: {address}")
        coords = geocode_address(address)

        if coords:
            lat, lon = coords
            print(f"Found coordinates: Lat {lat}, Lon {lon}")
            get_solar_info_by_coordinates(lat, lon)
        else:
            print("Could not find coordinates for this address")

    elif choice == "2":
        try:
            lat = float(input("Enter latitude: ").strip())
            lon = float(input("Enter longitude: ").strip())
            get_solar_info_by_coordinates(lat, lon)
        except ValueError:
            print("Invalid coordinates entered")
    else:
        print("Invalid choice")

def main():
    interactive_solar_query()

if __name__ == "__main__":
    main()
