## M2. Data Collection and Modeling

> **Research question:** How can open-access solar radiation data and public APIs be used to model and predict the optimal solar and battery system size for U.S. households to maximize energy cost savings and minimize payback time?

This milestone captures how we model the domain, which data we collect, and how to reproduce the prepared dataset.

---

### 1) Domain model (non-technical)
- **Environmental:** solar irradiance and production from NREL PVWatts v8 (NSRDB TMY) and Solar Resource data.  
- **Economic:** retail tariffs and DG rules from OpenEI URDB / NREL Utility Rates; incentives via IRS Section 25D; optional SREC price table.  
- **Technical:** PV DC capacity, tilt = latitude, south-facing azimuth, 14% losses; battery capacity captured in later milestones.  
These inputs drive an energy-balance and financial model to estimate bill offset, annual savings, and payback.

**Known limitations:** simplified load profiles (no smart-meter detail), TMY weather averages, uneven URDB coverage, no shading analysis, and static system cost assumptions.

---

### 2) Data sources
| Category | API / dataset | Notes |
| --- | --- | --- |
| Geocoding | OpenStreetMap Nominatim | `fetch_geocode.py`; rate-limit friendly. |
| Solar production | NREL PVWatts v8 | `fetch_pvwatts.py`; requires `NREL_API_KEY`. |
| Solar resource | NREL Solar Resource v1 | Included in PVWatts pulls for irradiance context. |
| Utility rates | NREL Utility Rates v3 / URDB | `fetch_rates.py`; fills residential/commercial prices. |
| Incentives/SREC | IRS 25D (30% ITC), SRECTrade table | SREC values manual/CSV lookup in pipeline. |

---

### 3) Pipeline and folder structure (`2_data_collection/data/`)
- **Scripts:** `fetch_geocode.py`, `fetch_pvwatts.py`, `fetch_rates.py`, `clean_merge_dataset.py`, `generate_visualizations.py`.  
- **Raw pulls:** `data/raw/` (`geocode_results.json`, `pvwatts_results.json`, `utility_rates_results.json`).  
- **Processed dataset:** `data/processed/solar_analysis_dataset.csv` (8 sample locations with production, tariffs, savings, and payback).  
- **Visuals:** `data/visualizations/` (irradiance, rates, geographic maps, SREC pricing).  
- **Config:** `data/.env` (set `NREL_API_KEY`).

**Reproduction (from `2_data_collection/data/`):**
```bash
pip install -r ../../scripts/requirements.txt  # or minimal: requests python-dotenv

# Add your API key (either export or create a .env with NREL_API_KEY=...)
export NREL_API_KEY=...
# or: printf \"NREL_API_KEY=YOUR_KEY\" > .env

python fetch_geocode.py --use-samples --output raw/
python fetch_pvwatts.py --geocode-file raw/geocode_results.json --output raw/
python fetch_rates.py --geocode-file raw/geocode_results.json --output raw/
python clean_merge_dataset.py --raw-dir raw/ --output processed/solar_analysis_dataset.csv
python generate_visualizations.py  # writes to visualizations/
```

---

### 4) Dataset snapshot (processed)
- File: `2_data_collection/data/processed/solar_analysis_dataset.csv`  
- Rows: 8 sample U.S. locations; Columns include `ac_annual_kwh`, `capacity_factor`, monthly `ac_*`, `electricity_rate_residential`, `utility_name`, `srec_price_per_mwh`, `system_cost_net`, `annual_savings`, `simple_payback_years`, `data_quality_score`.  
- Key insight: high-rate states (MA, CA) show faster payback despite lower production than sunnier low-rate states (AZ, TX).

---

### 4b) Why this is good for the analysis
- **Geographic policy variation:** Visuals show solar incentives vary widely; most states rely only on the 30% federal ITC, while a few SREC states add extra revenue.  
- **Economic impact examples:**  
  - Massachusetts (6,627 kWh/yr): 6.627 MWh × $280/MWh ≈ $1,856/yr SREC revenue (~$46.4k over 25 years), making MA competitive despite lower solar resource.  
  - Illinois (6,423 kWh/yr): 6.423 MWh × $70/MWh ≈ $450/yr (~$11.25k over 25 years); meaningful but less dramatic.  
- **Real-world takeaway:** SREC availability is the exception, so most U.S. homeowners cannot rely on it—supporting the research focus on geographic optimization.

---

### 5) Artifacts for reuse
- Visuals for analysis/communication: see `data/visualizations/*.png` and `loadprofile.png`.  
- Clean dataset for M3/M4: `processed/solar_analysis_dataset.csv` with schema documented in `data/README.md`.

---

