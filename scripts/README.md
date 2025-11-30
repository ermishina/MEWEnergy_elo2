# Solar PV + Battery Sizing Prototype (Flask)

This folder contains the web prototype used to explore solar sizing scenarios. It calls public APIs (OSM Nominatim, NREL PVWatts, NREL Utility Rates) and renders interactive results for the M3 milestone.

## Quickstart (local)
1) `cd scripts`  
2) `python -m venv .venv && source .venv/bin/activate`  
3) `pip install -r requirements.txt`  
4) `cp .env.example .env` and set `NREL_API_KEY` (required) and `SECRET_KEY`.  
5) `python app.py` and open http://localhost:5000

## Quickstart (Docker)
1) `cd scripts`  
2) `cp .env.example .env` and fill in `NREL_API_KEY` + `SECRET_KEY`.  
3) `docker compose up --build` then visit http://localhost:5001

## Notes
- **NREL_API_KEY is mandatory** for PVWatts and Utility Rates calls. Obtain a free key at https://developer.nrel.gov/.  
- The app uses OSM Nominatim; keep requests low-rate and include a real User-Agent if you change the code.  
- Data files for analysis should live under `data/raw/` and `data/processed/` at the repo root (both are git-ignored).
