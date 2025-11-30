#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 MEWEnergy Project Contributors

"""
clean_merge_dataset.py - Clean and merge raw data into analysis-ready CSV

Combines geocoding, PVWatts, and utility rate data into a single cleaned dataset
suitable for solar + battery investment analysis.

Usage:
    python clean_merge_dataset.py --raw-dir raw/ --output processed/solar_analysis_dataset.csv

Input files (from raw/):
    - geocode_results.json
    - pvwatts_results.json
    - utility_rates_results.json

Output:
    - processed/solar_analysis_dataset.csv
"""

import json
import csv
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# Financial constants for derived calculations
ITC_RATE = 0.30                    # Federal Investment Tax Credit (30%)
SOLAR_COST_PER_KW = 2500.0         # $/kW installed
BATTERY_COST_PER_KWH = 450.0       # $/kWh (LFP chemistry)
ANALYSIS_PERIOD_YEARS = 25
ELECTRICITY_ESCALATION_RATE = 0.03  # 3% annual increase
SOLAR_DEGRADATION_RATE = 0.005      # 0.5% annual degradation


# Output schema definition
OUTPUT_SCHEMA = [
    # Location identifiers
    ("id", "str", "Unique identifier for the location"),
    ("input_address", "str", "Original input address"),
    ("region", "str", "Geographic region (Northeast, West, etc.)"),
    ("latitude", "float", "Latitude in decimal degrees"),
    ("longitude", "float", "Longitude in decimal degrees"),
    ("state", "str", "U.S. state name"),
    
    # Solar resource data
    ("ghi_annual", "float", "Global Horizontal Irradiance (kWh/m²/day)"),
    ("dni_annual", "float", "Direct Normal Irradiance (kWh/m²/day)"),
    ("lat_tilt_annual", "float", "Irradiance at latitude tilt (kWh/m²/day)"),
    
    # PVWatts production estimates
    ("system_capacity_kw", "float", "PV system DC capacity (kW)"),
    ("ac_annual_kwh", "float", "Annual AC energy production (kWh)"),
    ("capacity_factor", "float", "Capacity factor (%)"),
    ("solrad_annual", "float", "Annual solar radiation (kWh/m²/day)"),
    
    # Monthly production (kWh)
    ("ac_jan", "float", "January AC production (kWh)"),
    ("ac_feb", "float", "February AC production (kWh)"),
    ("ac_mar", "float", "March AC production (kWh)"),
    ("ac_apr", "float", "April AC production (kWh)"),
    ("ac_may", "float", "May AC production (kWh)"),
    ("ac_jun", "float", "June AC production (kWh)"),
    ("ac_jul", "float", "July AC production (kWh)"),
    ("ac_aug", "float", "August AC production (kWh)"),
    ("ac_sep", "float", "September AC production (kWh)"),
    ("ac_oct", "float", "October AC production (kWh)"),
    ("ac_nov", "float", "November AC production (kWh)"),
    ("ac_dec", "float", "December AC production (kWh)"),
    
    # Utility rates
    ("electricity_rate_residential", "float", "Residential electricity rate ($/kWh)"),
    ("electricity_rate_commercial", "float", "Commercial electricity rate ($/kWh)"),
    ("utility_name", "str", "Utility company name"),
    ("srec_price_per_mwh", "float", "SREC price ($/MWh)"),
    
    # Derived financial metrics (for 5kW system)
    ("system_cost_gross", "float", "Gross system cost before incentives ($)"),
    ("system_cost_net", "float", "Net system cost after 30% ITC ($)"),
    ("annual_savings", "float", "Year 1 electricity savings ($)"),
    ("simple_payback_years", "float", "Simple payback period (years)"),
    ("annual_srec_revenue", "float", "Annual SREC revenue ($)"),
    ("lcoe", "float", "Levelized Cost of Energy ($/kWh)"),
    
    # Data quality flags
    ("data_quality_score", "int", "Data quality score (0-100)"),
    ("missing_fields", "str", "Comma-separated list of missing fields"),
]


def load_json_file(filepath: str) -> Optional[dict]:
    """Load JSON file with error handling."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load {filepath}: {e}")
        return None


def safe_get(data: dict, *keys, default=None):
    """Safely navigate nested dictionary."""
    result = data
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key, default)
        else:
            return default
    return result if result is not None else default


def to_float(value):
    """Safely convert value to float, return None if conversion fails."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def calculate_financial_metrics(ac_annual: float, rate: float, srec_price: float, 
                                system_capacity: float) -> dict:
    """Calculate derived financial metrics."""
    if not ac_annual or not rate or system_capacity <= 0:
        return {
            "system_cost_gross": None,
            "system_cost_net": None,
            "annual_savings": None,
            "simple_payback_years": None,
            "annual_srec_revenue": None,
            "lcoe": None
        }
    
    system_cost_gross = system_capacity * SOLAR_COST_PER_KW
    system_cost_net = system_cost_gross * (1 - ITC_RATE)
    annual_savings = ac_annual * rate
    
    # SREC revenue (1 SREC = 1 MWh)
    annual_srec_revenue = (ac_annual / 1000) * srec_price if srec_price else 0
    
    total_annual_value = annual_savings + annual_srec_revenue
    simple_payback_years = system_cost_net / total_annual_value if total_annual_value > 0 else 999
    
    # LCOE calculation (simplified)
    total_production_25y = sum([
        ac_annual * ((1 - SOLAR_DEGRADATION_RATE) ** year)
        for year in range(ANALYSIS_PERIOD_YEARS)
    ])
    lcoe = system_cost_net / total_production_25y if total_production_25y > 0 else None
    
    return {
        "system_cost_gross": round(system_cost_gross, 2),
        "system_cost_net": round(system_cost_net, 2),
        "annual_savings": round(annual_savings, 2),
        "simple_payback_years": round(simple_payback_years, 2),
        "annual_srec_revenue": round(annual_srec_revenue, 2),
        "lcoe": round(lcoe, 4) if lcoe else None
    }


def calculate_data_quality(record: dict) -> tuple:
    """Calculate data quality score and list missing fields."""
    critical_fields = ["latitude", "longitude", "ac_annual_kwh", "electricity_rate_residential"]
    important_fields = ["ghi_annual", "dni_annual", "system_capacity_kw", "capacity_factor"]
    
    missing = []
    score = 100
    
    for field in critical_fields:
        if record.get(field) is None:
            missing.append(field)
            score -= 20
    
    for field in important_fields:
        if record.get(field) is None:
            missing.append(field)
            score -= 5
    
    return max(0, score), ",".join(missing) if missing else ""


def merge_data_sources(geocode_data: dict, pvwatts_data: dict, rates_data: dict) -> List[dict]:
    """Merge data from all sources into unified records."""
    merged = []
    
    # Index data by ID for efficient lookup
    pvwatts_by_id = {r["id"]: r for r in pvwatts_data.get("data", [])} if pvwatts_data else {}
    rates_by_id = {r["id"]: r for r in rates_data.get("data", [])} if rates_data else {}
    
    for geo_record in geocode_data.get("data", []):
        if not geo_record.get("success"):
            continue
        
        record_id = geo_record.get("id")
        pvwatts_record = pvwatts_by_id.get(record_id, {})
        rates_record = rates_by_id.get(record_id, {})
        
        # Extract PVWatts outputs
        pv_outputs = safe_get(pvwatts_record, "pvwatts", "outputs", default={})
        pv_inputs = safe_get(pvwatts_record, "pvwatts", "inputs", default={})
        solar_outputs = safe_get(pvwatts_record, "solar_resource", "outputs", default={})
        
        # Extract monthly production
        ac_monthly_raw = pv_outputs.get("ac_monthly", [None] * 12)
        if len(ac_monthly_raw) < 12:
            ac_monthly_raw.extend([None] * (12 - len(ac_monthly_raw)))
        ac_monthly = [to_float(v) for v in ac_monthly_raw]
        
        # Extract utility rates
        res_rate_info = safe_get(rates_record, "rates", "residential", default={})
        com_rate_info = safe_get(rates_record, "rates", "commercial", default={})

        res_rate = to_float(res_rate_info.get("rate")) if res_rate_info.get("success") else None
        com_rate = to_float(com_rate_info.get("rate")) if com_rate_info.get("success") else None
        utility_name = res_rate_info.get("utility_name")

        # SREC price
        srec_price_raw = rates_record.get("srec_price", 0) or 0
        srec_price = to_float(srec_price_raw) or 0

        # System capacity
        system_capacity = to_float(pv_inputs.get("system_capacity")) or 5.0
        ac_annual = to_float(pv_outputs.get("ac_annual"))
        
        # Calculate financial metrics
        financial = calculate_financial_metrics(ac_annual, res_rate, srec_price, system_capacity)
        
        # Build merged record
        record = {
            "id": record_id,
            "input_address": geo_record.get("input_address", ""),
            "region": geo_record.get("region", "Unknown"),
            "latitude": to_float(geo_record.get("lat")),
            "longitude": to_float(geo_record.get("lon")),
            "state": rates_record.get("state", ""),

            # Solar resource
            "ghi_annual": to_float(safe_get(solar_outputs, "avg_ghi", "annual")),
            "dni_annual": to_float(safe_get(solar_outputs, "avg_dni", "annual")),
            "lat_tilt_annual": to_float(safe_get(solar_outputs, "avg_lat_tilt", "annual")),

            # PVWatts production
            "system_capacity_kw": system_capacity,
            "ac_annual_kwh": ac_annual,
            "capacity_factor": to_float(pv_outputs.get("capacity_factor")),
            "solrad_annual": to_float(pv_outputs.get("solrad_annual")),
            
            # Monthly production
            "ac_jan": ac_monthly[0],
            "ac_feb": ac_monthly[1],
            "ac_mar": ac_monthly[2],
            "ac_apr": ac_monthly[3],
            "ac_may": ac_monthly[4],
            "ac_jun": ac_monthly[5],
            "ac_jul": ac_monthly[6],
            "ac_aug": ac_monthly[7],
            "ac_sep": ac_monthly[8],
            "ac_oct": ac_monthly[9],
            "ac_nov": ac_monthly[10],
            "ac_dec": ac_monthly[11],
            
            # Rates
            "electricity_rate_residential": res_rate,
            "electricity_rate_commercial": com_rate,
            "utility_name": utility_name,
            "srec_price_per_mwh": srec_price,
            
            # Financial metrics
            **financial
        }
        
        # Calculate data quality
        quality_score, missing_fields = calculate_data_quality(record)
        record["data_quality_score"] = quality_score
        record["missing_fields"] = missing_fields
        
        merged.append(record)
    
    return merged


def write_csv(records: List[dict], output_path: str):
    """Write merged records to CSV file."""
    if not records:
        print("Warning: No records to write")
        return
    
    # Get column names from schema
    columns = [col[0] for col in OUTPUT_SCHEMA]
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)
    
    print(f"Written {len(records)} records to {output_path}")


def write_schema_documentation(output_dir: str):
    """Write schema documentation file."""
    schema_file = Path(output_dir) / "schema.md"
    
    with open(schema_file, 'w') as f:
        f.write("# Solar Analysis Dataset Schema\n\n")
        f.write("Generated: " + datetime.utcnow().isoformat() + "Z\n\n")
        f.write("| Column | Type | Description |\n")
        f.write("|--------|------|-------------|\n")
        for name, dtype, desc in OUTPUT_SCHEMA:
            f.write(f"| `{name}` | {dtype} | {desc} |\n")
    
    print(f"Schema documentation written to {schema_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Clean and merge raw data into analysis-ready CSV"
    )
    parser.add_argument(
        "--raw-dir", "-r", default="raw",
        help="Directory containing raw JSON files (default: raw)"
    )
    parser.add_argument(
        "--output", "-o", default="processed/solar_analysis_dataset.csv",
        help="Output CSV file path (default: processed/solar_analysis_dataset.csv)"
    )
    parser.add_argument(
        "--write-schema", action="store_true",
        help="Write schema documentation to processed/ directory"
    )
    
    args = parser.parse_args()
    raw_dir = Path(args.raw_dir)
    
    # Load raw data files
    print("Loading raw data files...")
    geocode_data = load_json_file(raw_dir / "geocode_results.json")
    pvwatts_data = load_json_file(raw_dir / "pvwatts_results.json")
    rates_data = load_json_file(raw_dir / "utility_rates_results.json")
    
    if not geocode_data:
        print("Error: geocode_results.json is required")
        return
    
    # Merge data sources
    print("\nMerging data sources...")
    merged_records = merge_data_sources(geocode_data, pvwatts_data, rates_data)
    
    # Write output
    write_csv(merged_records, args.output)
    
    if args.write_schema:
        output_dir = str(Path(args.output).parent)
        write_schema_documentation(output_dir)
    
    # Summary statistics
    print("\n=== Summary ===")
    print(f"Total records: {len(merged_records)}")
    if merged_records:
        quality_scores = [r["data_quality_score"] for r in merged_records]
        print(f"Avg data quality score: {sum(quality_scores)/len(quality_scores):.1f}/100")
        
        ac_values = [r["ac_annual_kwh"] for r in merged_records if r["ac_annual_kwh"]]
        if ac_values:
            print(f"AC Annual (kWh): min={min(ac_values):,.0f}, max={max(ac_values):,.0f}, avg={sum(ac_values)/len(ac_values):,.0f}")


if __name__ == "__main__":
    main()