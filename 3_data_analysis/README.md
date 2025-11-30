## M3. Data Analysis — Solar PV + Battery Sizing

This milestone tests our decision-support question with **transparent, question-first analysis** rather than complex ML. The goal is to propose feasible solar PV + battery system sizes for U.S. households using public data while clearly communicating uncertainty and reproducibility.

### Objectives and principles
- Match methods to the question and available data (PVWatts outputs, tariff data, user load assumptions); keep techniques minimal and explainable.  
- State the limits of what the analysis can answer and where the data is too weak.  
- Quantify and communicate uncertainty (weather variance, tariff coverage, simplified load shapes) and record null or undesirable results.  
- Make every step reproducible and reviewable by documenting code, assumptions, and artifacts.

### Analysis outline (to be expanded with results)
- **Data inputs:** PVWatts production estimates, utility tariffs/URDB data, user-provided load and system cost assumptions.  
- **Techniques:** scenario comparisons of PV/battery sizes, bar/line charts for annual savings and payback, sensitivity checks on key parameters.  
- **Uncertainty handling:** error bars or ranges around production and savings; explicit caveats for tariff gaps and load simplifications.  
- **Outputs:** recommended size bands, payback and bill-savings estimates, and narrative trade-offs for homeowners.

### Non-technical findings (pending insertion)
- Key takeaways: **TODO** summarize savings/payback ranges by representative ZIPs (e.g., CA/TX/FL) with uncertainty bands.  
- Visuals: **TODO** include bar/line charts for savings vs. system size and battery backup hours; note best/base/conservative scenarios.  
- Caveats: highlight tariff assumptions, TMY weather basis, and simplified load profiles.  

### Technical appendix (methods & alternatives)
- Methods: scenario tables (PV kW × battery kWh), payback computation using PVWatts `ac_annual` and utility rates; sensitivity on rate +/- and system cost +/-; battery backup hours estimated from critical load profile.  
- Alternatives considered: higher-fidelity hourly load modelling, shaded roof modelling, Monte Carlo weather perturbations — deferred due to scope/time and data availability.  
- Uncertainty quantification: ranges derived from tariff bands and ±10–20% production variability; note where data gaps require user confirmation.  

### Replication checklist
- Environment: `python -m venv .venv && source .venv/bin/activate && pip install -r scripts/requirements.txt`.  
- Data pull: use `scripts/api.py` helpers to retrieve PVWatts and utility rates for test locations.  
- Analysis artifacts: **TODO** add notebook/script path (e.g., `notebooks/03_analysis.ipynb`) and execution order; export figures to `3_reports/m4_communication/artifacts/` as needed.  
- Inputs/outputs: document expected input format (location list, system cost assumptions) and where outputs are stored (`data/processed/` or `3_reports/`).  

### Deliverables
1. Non-technical findings with visuals, confidence levels, and clear caveats.  
2. Technical appendix describing methods, rationale, known flaws, and alternative approaches.  
3. Reproducibility package: scripts/notebooks and instructions to rerun the analysis on the same data.  
4. Completed milestone survey per course requirements.  
5. Tagged commit for this milestone (for example, `m3-data-analysis`) created before the deadline.  
6. Group and individual retrospective capturing lessons and next-step adjustments.

### Replication notes (to be detailed alongside code)
- Use the project Python environment (`python -m venv .venv && source .venv/bin/activate`) and track dependencies in `requirements.txt`.  
- Keep raw data in `data/raw/` and processed outputs in `data/processed/` (both git-ignored).  
- Document commands and notebook execution order alongside any new scripts so others can fully reproduce the results end-to-end.
- The Flask sizing prototype in `scripts/` can be run locally or via Docker (see `scripts/README.md`) to regenerate scenario visuals; it requires `NREL_API_KEY` in `.env`.

