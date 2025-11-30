# Data Documentation

> **2_data_collection/data/** — MEWEnergy Solar Analysis Dataset

---

## Overview

This directory contains all data collection scripts, raw API responses, and processed datasets for the solar PV investment analysis platform.

---

## Data Sources

### 1. OpenStreetMap Nominatim API (Geocoding)

| Property | Value |
|----------|-------|
| **Endpoint** | `https://nominatim.openstreetmap.org/search` |
| **Purpose** | Convert street addresses to latitude/longitude coordinates |
| **Authentication** | None (public API) |
| **Rate Limit** | 1 request per second (enforced) |
| **Documentation** | [Nominatim API](https://nominatim.org/release-docs/latest/api/Search/) |

**Parameters Used:**
```
q           = Full address string
format      = json
limit       = 1
countrycodes = us
addressdetails = 1
```

**User-Agent Header:** `MEWEnergy/1.0 (MIT Emerging Talent CDSP Project)`

---

### 2. NREL PVWatts API v8 (Solar Production)

| Property | Value |
|----------|-------|
| **Endpoint** | `https://developer.nrel.gov/api/pvwatts/v8.json` |
| **Purpose** | Estimate annual solar energy production for a given location and system |
| **Authentication** | API key required (`NREL_API_KEY` environment variable) |
| **Rate Limit** | ~1,000 requests/hour |
| **Documentation** | [PVWatts API v8](https://developer.nrel.gov/docs/solar/pvwatts/v8/) |

**Parameters Used:**
```
api_key         = NREL API key
lat             = Latitude
lon             = Longitude
system_capacity = 5.0 (kW DC)
module_type     = 0 (Standard)
array_type      = 0 (Fixed open rack)
losses          = 14 (%)
tilt            = latitude (degrees)
azimuth         = 180 (south-facing)
```

---

### 3. NREL Solar Resource Data API v1

| Property | Value |
|----------|-------|
| **Endpoint** | `https://developer.nrel.gov/api/solar/solar_resource/v1.json` |
| **Purpose** | Retrieve irradiance data (GHI, DNI, tilt) for a location |
| **Authentication** | API key required |
| **Documentation** | [Solar Resource Data API](https://developer.nrel.gov/docs/solar/solar-resource-v1/) |

**Parameters Used:**
```
api_key = NREL API key
lat     = Latitude
lon     = Longitude
```

---

### 4. NREL Utility Rates API v3

| Property | Value |
|----------|-------|
| **Endpoint** | `https://developer.nrel.gov/api/utility_rates/v3.json` |
| **Purpose** | Retrieve local electricity rates by sector |
| **Authentication** | API key required |
| **Documentation** | [Utility Rates API v3](https://developer.nrel.gov/docs/electricity/utility-rates-v3/) |

**Parameters Used:**
```
api_key = NREL API key
lat     = Latitude
lon     = Longitude
```

---

### 5. Static Reference Data

| Data | Source | Update Frequency |
|------|--------|------------------|
| **SREC Prices** | [SRECTrade](https://www.srectrade.com/), EPA | Quarterly (manual update) |
| **ITC Rate** | [IRS Section 25D](https://www.irs.gov/credits-deductions/residential-clean-energy-credit) | Annual (currently 30% through 2032) |
| **Installation Costs** | SEIA/NREL benchmarks | Annual |

---

## Dataset Schema

### Processed Output: `solar_analysis_dataset.csv`

| Column | Type | Units | Description |
|--------|------|-------|-------------|
| `id` | string | — | Unique identifier for the location |
| `input_address` | string | — | Original input address |
| `region` | string | — | Geographic region (Northeast, West, etc.) |
| `latitude` | float | degrees | Latitude in decimal degrees |
| `longitude` | float | degrees | Longitude in decimal degrees |
| `state` | string | — | U.S. state name |
| `ghi_annual` | float | kWh/m²/day | Global Horizontal Irradiance (annual average) |
| `dni_annual` | float | kWh/m²/day | Direct Normal Irradiance (annual average) |
| `lat_tilt_annual` | float | kWh/m²/day | Irradiance at latitude tilt (annual average) |
| `system_capacity_kw` | float | kW | PV system DC capacity |
| `ac_annual_kwh` | float | kWh | Annual AC energy production |
| `capacity_factor` | float | % | Capacity factor |
| `solrad_annual` | float | kWh/m²/day | Annual solar radiation on array |
| `ac_jan` through `ac_dec` | float | kWh | Monthly AC production |
| `electricity_rate_residential` | float | $/kWh | Residential electricity rate |
| `electricity_rate_commercial` | float | $/kWh | Commercial electricity rate |
| `utility_name` | string | — | Utility company name |
| `srec_price_per_mwh` | float | $/MWh | State SREC price (0 if no program) |
| `system_cost_gross` | float | $ | Gross system cost before incentives |
| `system_cost_net` | float | $ | Net system cost after 30% ITC |
| `annual_savings` | float | $ | Year 1 electricity savings |
| `simple_payback_years` | float | years | Simple payback period |
| `annual_srec_revenue` | float | $ | Annual SREC revenue |
| `lcoe` | float | $/kWh | Levelized Cost of Energy |
| `data_quality_score` | int | 0-100 | Data quality score |
| `missing_fields` | string | — | Comma-separated list of missing fields |

---

## Known Data Flaws and Limitations

### API-Related Issues

| Issue | Impact | Mitigation |
|-------|--------|------------|
| **TMY Weather Data** | PVWatts uses Typical Meteorological Year data, not recent actuals | Results represent 30-year averages; actual production varies ±10-15% |
| **Utility Rate Gaps** | ~15% of U.S. utilities missing from URDB | Default to state average or $0.15/kWh fallback |
| **Geocoding Ambiguity** | Some addresses return multiple matches | Use first (highest confidence) result; manual review if critical |
| **SREC Price Staleness** | SREC prices change quarterly | Use conservative estimates; flag for manual update |

### Model Simplifications

| Simplification | Reality | Impact |
|----------------|---------|--------|
| **No shading analysis** | Trees, buildings block sunlight | Production estimates are optimistic upper bounds |
| **Fixed tilt = latitude** | Optimal tilt varies by season | ~5% production difference vs. optimal |
| **14% system losses** | Actual losses vary 10-20% | Minor impact on relative comparisons |
| **South-facing assumption** | Roofs vary in orientation | East/West facing reduces production 15-20% |
| **No degradation in Year 1** | Panels degrade ~0.5%/year | Minimal impact on payback estimates |

### Data Quality Considerations

- **Score 100**: All critical fields present and validated
- **Score 80-99**: Minor fields missing (e.g., utility name)
- **Score 60-79**: Some financial calculations limited
- **Score < 60**: Major data gaps; use with caution

---

## Directory Structure

```
data/
├── README.md                      # This file
├── fetch_geocode.py               # Geocode addresses → lat/lon
├── fetch_pvwatts.py               # Fetch PVWatts production estimates
├── fetch_rates.py                 # Fetch utility electricity rates
├── clean_merge_dataset.py         # Merge raw → processed CSV
├── generate_visualizations.py     # Create analysis charts
│
├── raw/                           # Raw API responses (JSON)
│   ├── geocode_results.json       # Nominatim responses
│   ├── pvwatts_results.json       # PVWatts responses
│   └── utility_rates_results.json # Utility Rates responses
│
└── processed/                     # Analysis-ready data
    └── solar_analysis_dataset.csv # Main dataset
```

---

## Recreation Steps

### Prerequisites

1. Python 3.8+ with pip
2. NREL API key (free at https://developer.nrel.gov/signup/)

### Installation

```bash
# Install dependencies
pip install requests python-dotenv

# Set up environment
# Create .env with NREL_API_KEY or export it
printf "NREL_API_KEY=YOUR_KEY" > .env
```

### Full Pipeline Execution

```bash
# Step 1: Geocode sample addresses
python fetch_geocode.py --use-samples --output raw/
# Output: raw/geocode_results.json

# Step 2: Fetch PVWatts estimates for geocoded locations
python fetch_pvwatts.py --geocode-file raw/geocode_results.json --output raw/
# Output: raw/pvwatts_results.json

# Step 3: Fetch utility rates
python fetch_rates.py --geocode-file raw/geocode_results.json --all-sectors --output raw/
# Output: raw/utility_rates_results.json

# Step 4: Clean and merge into analysis-ready CSV
python clean_merge_dataset.py --raw-dir raw/ --output processed/solar_analysis_dataset.csv
# Output: processed/solar_analysis_dataset.csv

# Step 5: (Optional) Generate visualizations
python generate_visualizations.py
# Output: ../visualizations/*.png

# (Optional) Open the processed CSV for inspection or export visuals
python generate_visualizations.py
open visualizations/
```

### Using Custom Addresses

Create a text file with one address per line:

```text
# addresses.txt
123 Main Street, Boston, MA 02101
456 Oak Avenue, Los Angeles, CA 90001
789 Elm Street, Houston, TX 77001
```

Then run:

```bash
python fetch_geocode.py --addresses-file addresses.txt --output raw/
```

---

## Sample Data Summary

Current dataset contains **8 sample locations** across diverse U.S. regions:

| ID | Region | State | AC Annual (kWh) | Elec. Rate ($/kWh) | Payback (years) |
|----|--------|-------|-----------------|--------------------|--------------------|
| MA_001 | Northeast | Massachusetts | 6,127 | $0.285 | 6.0 |
| CA_001 | West | California | 7,235 | $0.325 | 5.4 |
| TX_001 | South | Texas | 7,856 | $0.123 | 11.4 |
| FL_001 | Southeast | Florida | 7,424 | $0.146 | 9.4 |
| AZ_001 | Southwest | Arizona | 8,568 | $0.129 | 10.1 |
| IL_001 | Midwest | Illinois | 6,235 | $0.157 | 10.1 |
| CO_001 | Mountain | Colorado | 7,457 | $0.138 | 10.0 |
| WA_001 | Pacific NW | Washington | 5,678 | $0.112 | 13.8 |

**Key Insight**: High-rate states (MA, CA) have faster payback despite lower production than sunny states (AZ, TX) with low rates.
---

*Last updated: June 2025 | MEWEnergy Team*
