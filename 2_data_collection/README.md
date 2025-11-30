## M2. Research Question & Data Modeling

> **How can open-access solar radiation data and public APIs be used to model and predict the optimal solar and battery system size for U.S. households to maximize energy cost savings and minimize payback time?**

This question defines our analytical focus and guides the platform’s architecture and data selection strategy.

---

### 1. Non-Technical Explanation: Modeling the Domain

Our domain represents the decision-making process of a U.S. homeowner who wants to estimate whether investing in a solar PV and battery system is financially viable.  
To model this scenario, we identify **three main components**:

1. **Environmental Factors:** solar irradiance, temperature, weather patterns.  
   → Collected from *NREL’s PVWatts API* (based on NSRDB TMY data).  
2. **Economic Factors:** utility rates, incentives, and SREC market data.  
   → From *NREL Utility Rates API*, *OpenEI URDB*, and *IRS Section 25D*.  
3. **Technical Factors:** PV system capacity, inverter efficiency, battery capacity.  
   → Modeled through user input + performance parameters returned by PVWatts (`ac_annual`, `capacity_factor`, etc.).  

We use these variables to build a simplified **energy-balance model** that estimates how much grid electricity is offset by solar generation and how storage affects self-consumption.  
This model enables an estimation of **annual savings** and **payback period** using publicly available data sources.

**Possible Flaws & Limitations**
- Simplified consumption patterns (no hourly load profile data for all regions).
- Static assumptions on system degradation and efficiency.
- SREC market data not uniform across all states.
- Exclusion of installation-specific constraints (e.g., shading, tilt errors).

---

### 2. Data Sources and Documentation

| Category | API / Dataset | Provider | Description | Known Limitations |
|-----------|----------------|-----------|--------------|------------------|
| Solar Irradiance | [NREL PVWatts® v8](https://developer.nrel.gov/api/pvwatts/v8.json) | U.S. DOE / NREL | Solar generation estimate using NSRDB TMY data | Weather-year approximation (TMY) |
| Utility Rates | [OpenEI URDB](https://openei.org/services/doc/rest/util_rates/) | OpenEI | Electricity tariffs, net-metering & DG rules | Data gaps for small utilities |
| Location | [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/) | OSM Foundation | Converts address → coordinates | Requires rate-limited API usage |
| Incentives | [IRS Section 25D](https://www.irs.gov/credits-deductions/residential-clean-energy-credit) | IRS / U.S. Gov | 30 % tax credit | Federal scope only |
| SREC Markets | [SRECTrade API](https://www.srectrade.com/about) | SRECTrade | Market prices for state SREC credits | Not all states participate |

---

### 3. Data Cleaning & Structure

Raw data from the APIs will be collected as JSON files and standardized into a **relational CSV schema** with the following structure:

| Column | Description | Source |
|---------|--------------|--------|
| `latitude`, `longitude` | Coordinates for location | Nominatim |
| `ac_annual` | Annual AC energy output (kWh) | PVWatts |
| `utility_rate` | Retail price (¢/kWh) | URDB |
| `system_cost` | Estimated installed cost ($) | user input / average state cost |
| `incentive_tax_credit` | 30% cost reduction | IRS 25D |
| `srec_value` | State-level credit value ($/MWh) | SRECTrade |
| `annual_savings` | Calculated result | derived |
| `payback_period` | Calculated result | derived |

All intermediate processing (JSON → CSV → analysis-ready dataset) will be scripted in Python for full reproducibility.  
Scripts **to be added** (e.g., `fetch_pv_data.py`, `fetch_rates.py`, `clean_merge_dataset.py`) and stored alongside this repo (path TBD).

