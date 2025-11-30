# MEWEnergy Platform for Solar PV and Battery Investments ELO2

## M0. Project Overview

> *As an engineer who designs renewable energy systems, I have seen many U.S. homeowners struggle to decide whether it is worth investing in solar panels and batteries. Online calculators often use simple data or ignore regional utility tariffs, which can make the savings estimates seem unrealistic. My goal is to create a tool that is clear and based on facts. This will help consumers make informed decisions about energy.*


### Live sizing (API-driven) at a glance
- **Input:** user address or ZIP → geocoded to lat/lon via OpenStreetMap Nominatim.  
- **Solar resource & production:** PVWatts v8 returns `ac_annual`, `ac_monthly`, and `capacity_factor` for that location.  
- **Tariffs:** NREL Utility Rates/URDB fetch residential ¢/kWh and DG rules to price self-consumption vs export.  
- **Sizing logic:** combine production with user/system cost assumptions to propose PV kW and battery kWh bands aimed at shortest payback and backup-hours targets.  
- **Outputs in the prototype (scripts/):** savings/payback bands (best/base/conservative), bill offset %, and estimated backup hours by battery size.  
- **Comms artefact (M4):** landing page/brief will render these API-backed scenarios for homeowners.

### M0 setup & logistics (per syllabus)
- Repository setup: GitHub project board (Backlog → In Progress → Review → Done) and branch protections on `main` (PR + review required); PR template lives at `.github/pull_request_template.md`. Add the board URL and protection status here once set.
- Collaboration docs: group norms, constraints, communication plan, and learning goals stored in `planning/README.md`.
- Meeting agendas/minutes: kept in `planning/meeting_notes.md` (rolling log).
- Milestones: six course milestones defined and tracked in the repo.
- Retrospective: record M0 reflections in `planning/meeting_notes.md` under M0.
- Tag: create `m0-setup` on the final M0 commit before M1 work begins.
- Survey: complete the M0 course survey (note completion in meeting notes).

## [M1. Domain Research & Background](1_data_analysis/README.md)

This milestone consolidates our understanding of the U.S. residential solar-plus-storage domain and formalizes the research question that drives subsequent work. The full narrative, literature review, and analytical framing are documented in `0_domain_study/README.md` and `1_data_analysis/README.md`.

For Milestone 1, we provide the following deliverables:

1. A problem statement grounded in practitioner experience, based on the perspective of a renewable energy systems engineer working with U.S. homeowners (see the M0 overview and `1_data_analysis/README.md`).  
2. A background review of the research domain, including energy price trends, policy incentives, load profiles, and solar-plus-storage adoption, with references to EIA, NREL, SEIA, and related sources (`0_domain_study/README.md`).  
3. A structured summary of the group’s systems-level understanding of the problem domain, covering households, utilities, policy, and technology (`1_data_analysis/README.md`).  
4. An actionable research question that guides the modelling and data work for subsequent milestones: **How can open-access solar radiation data and public APIs be used to model and predict the optimal solar and battery system size for U.S. households to maximize energy cost savings and minimize payback time?**  
5. A set of planning artefacts (group norms, learning goals, constraints, and a communication plan) maintained in the team’s collaboration tools, with key assumptions reflected in the project documentation.  
6. A short retrospective for this milestone that captures what worked well, what was challenging, and what we will adjust going into M2 (`1_data_analysis/README.md`).  
7. A labelled Git tag (for example, `m1-domain-research`) created on the final M1 commit before the deadline to serve as the evaluation baseline.  
8. Completion of the official Milestone 1 survey by all team members in accordance with course requirements.  

---

## [M2: Data Collection](2_data_collection/README.md)

Our work is guided by a single core question:

> **How can open-access solar radiation data and public APIs be used to model and predict the optimal solar and battery system size for U.S. households to maximize energy cost savings and minimize payback time?**

This question frames the platform as a **decision-support tool for homeowners** who want to understand whether a rooftop PV plus battery investment is financially attractive under their local conditions.

### Domain Model: How We Represent the Problem

To operationalize this question, we model the investment decision using three integrated components:

1. **Environmental Factors**  
   - Solar irradiance and climate conditions for a specific location.  
   - Modeled using **NREL PVWatts® v8**, which provides annual AC energy output and performance metrics based on NSRDB TMY data.

2. **Economic & Policy Factors**  
   - Retail electricity prices and tariff structures from **OpenEI / Utility Rate Database (URDB)**.  
   - Federal incentives (e.g., **IRS Section 25D Residential Clean Energy Credit**) and state-level **SREC market values** where available.

3. **Technical System Parameters**  
   - PV system size, inverter efficiency, and battery capacity from **user input**, combined with PVWatts outputs (such as `ac_annual` and `capacity_factor`).  

These elements feed into a simplified **energy-balance and financial model** that:

- Estimates how much grid consumption is offset by solar generation and storage.  
- Derives **annual bill savings**, net investment cost after incentives, and **payback period**.  
- Supports comparison of different system sizes and configurations to identify an **economically optimal solar + battery bundle** for a given household.

### Role of Data and Known Constraints

All inputs are sourced through **public, reproducible APIs** (NREL, OpenEI, IRS, SREC providers) and standardized into an analysis-ready dataset. While this creates a scalable modeling framework, it also introduces known limitations:

- Use of typical meteorological year (TMY) data rather than full historical weather.  
- Simplified household load assumptions instead of detailed hourly smart meter data.  
- Uneven availability and granularity of tariff and SREC data across utilities and states.

Despite these constraints, the model provides a **transparent, data-driven baseline** for evaluating residential solar and battery investments at scale and serves as the analytical backbone for subsequent milestones in this project.


## [M3. Data Analysis](3_data_analysis/README.md)

This milestone validates our solar PV + battery sizing question using **transparent, question-driven analysis** rather than heavy-weight ML. Methods must fit the data we have (PVWatts outputs, tariff data, user load assumptions) and stay reproducible under project constraints.

### Analytical stance 
- Frame answerable questions and state the limits of what the data can and cannot support.  
- Select **appropriate, minimal** techniques (scenario tables, bar/line charts, sensitivity checks) that align with available data and time.  
- Quantify and communicate uncertainty (weather variability, tariff gaps, load assumptions) and be ready to accept null or undesirable results.  
- Document every step so results can be replicated and critiqued.

### Milestone deliverables (see [M3. Data Analysis](3_data_analysis/README.md) for full detail)
1. **Non-technical findings** with visuals, uncertainty levels, and key caveats.  
2. **Technical write-up** explaining chosen methods, rationale, flaws, and alternative approaches.  
3. **Reproducibility package**: scripts/notebooks and documentation so others can re-run the analysis on the same data.  
4. **Milestone survey** completed per course requirements.  
5. **Tagged commit** for the milestone (e.g., `m3-data-analysis`) created before the deadline.  
6. **Retrospective** (group + individual) capturing lessons learned and adjustments for M4.

A lightweight Flask prototype that exercises the sizing logic and visual outputs lives in `scripts/` (run locally or via Docker; see `scripts/README.md`).

---

## [M4. Communicating Results](3_reports/m4_communication/strategy.md)

This milestone turns our analysis into audience-fit messaging for U.S. homeowners deciding whether rooftop solar plus a battery is worth it.

### Target audience & objectives
- Audience: mobile-first homeowners (30–65) in high-tariff or outage-prone states (CA, TX, FL) with \$120–\$300 monthly bills; time-constrained and non-technical but engaged in HOA/neighborhood groups.  
- Learning goals: see ZIP-specific savings/payback ranges that include the 25D tax credit, understand outage backup hours by battery size, and know what drives uncertainty.  
- Desired actions: run the address-based check, select an “outage-ready” preset, schedule a follow-up, and share the summary with neighbors/HOA.  
- Uncertainty framing: present best/base/conservative bands, flag tariff/load assumptions, and invite them to confirm their rate plan before acting.  

### Communication artifact
- Medium: mobile-first landing page with an embedded scenario snapshot (from `scripts/`), plus a printable 2-page brief for HOA/email/WhatsApp distribution.  
- Rationale: fits mobile sharing habits, fast to skim, localized by ZIP to build trust.  
- Assets: live in `3_reports/m4_communication/artifacts/` (built from PVWatts + URDB data and the Flask visuals).  

### M4 deliverables
1. Audience & strategy doc with personas, goals, channels, and success criteria (`3_reports/m4_communication/strategy.md`).  
2. Communication artifact aligned to the strategy (PDF/landing copy) in `3_reports/m4_communication/artifacts/`.  
3. Completed milestone survey (course requirement).  
4. Tagged commit created before the deadline (planned tag: `m4-communication`).  
5. Group and individual retrospective stored alongside the artifact.  

### Analytical backbone for the artifact
- Retrieve **solar resource and performance data** via the official U.S. Government API:  
  **[NREL PVWatts® API (v8)](https://developer.nrel.gov/api/pvwatts/v8.json)**.  
- Automatically obtain **geographical coordinates** from a given address using  
  **[OpenStreetMap Nominatim API](https://nominatim.openstreetmap.org/search)**.  
- Estimate **annual electricity generation** and **system efficiency** based on real-world irradiance data.  
- Compute **financial feasibility metrics**: system cost, savings, and payback period.  
- Provide **data visualization** for consumers to explore scenarios interactively.  

---

## [M5. Final Presentation](5_final_presentation/README.md)
- Deliverable: 2.5-minute pitch covering research question, findings, and communication strategy; link to deck/video will live in `5_final_presentation/`.
- Tag: planned `m5-final-presentation` before submission.
- Survey & retrospectives: per syllabus; individual and group notes to be stored alongside the deck.

---

## 5. Methodology Overview

The platform integrates data collection, processing, and analysis in the following workflow:

| Step | Description | API / Data Source |
|------|--------------|-------------------|
| **1. Geocoding** | Convert user-entered address to latitude and longitude. | [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/search) |
| **2. Solar Data Retrieval** | Query U.S. Government solar datasets for irradiance and production estimates. | [NREL PVWatts API v8](https://developer.nrel.gov/api/pvwatts/v8.json) |
| **3. Data Modeling** | Calculate optimal PV system and battery configuration based on consumption and cost data. | Internal algorithms |
| **4. Financial Analysis** | Compute annual savings, ROI, and payback period. | User input + cost model |
| **5. Visualization** | Present results clearly for non-technical users. | Web-based dashboard |

This open, API-driven architecture allows scalability and reproducibility for various U.S. locations.

---

## 6. Expected Impact

By bridging **publicly available U.S. energy data** and **consumer decision tools**, the project aims to:
- Help households reduce **energy bills** and **carbon footprint**.  
- Increase **awareness** of renewable energy economics.  
- Demonstrate **data science applications** for sustainability and smart energy systems.

---

## 7. Repository Structure

```
.
├── 0_domain_study/
├── 1_data_analysis/
├── 2_data_collection/
├── 3_data_analysis/
├── 3_reports/
│   └── m4_communication/
│       ├── artifacts/
│       └── strategy.md
├── 5_final_presentation/
├── planning/
│   ├── README.md
│   └── meeting_notes.md
├── data/
│   ├── README.md
│   ├── raw/        # git-ignored placeholder
│   └── processed/  # git-ignored placeholder
├── .github/
│   └── pull_request_template.md
├── scripts/
│   ├── app.py
│   ├── api.py
│   ├── templates/
│   ├── static/
│   ├── Dockerfile
│   └── docker-compose.yml
├── README.md
└── .env.example
```

## 8. Data Sources and References

**Geocoding & Coordinates**
- [OpenStreetMap Nominatim API](https://nominatim.openstreetmap.org/): free geocoding service used for address-to-coordinate conversion. Compliance with rate limits and usage policy is maintained.

**Solar Resource & Production**
- [NREL PVWatts® API (v8)](https://developer.nrel.gov/api/pvwatts/v8.json): primary data source for solar energy modeling and irradiance estimation.
- [NREL Solar Resource Data API (v1)](https://developer.nrel.gov/api/solar/solar_resource/v1.json): supplementary irradiance data (GHI, DNI, tilt-at-latitude).

**Tariffs & Export Credits**
- [NREL Utility Rates API (v3)](https://developer.nrel.gov/docs/electricity/utility-rates-v3/): provides annual average electricity rates by sector.
- [OpenEI Utility Rate Database (URDB)](https://openei.org/services/doc/rest/util_rates/): includes time-of-use structures and *dgrules* for distributed generation (Net Metering, Net Billing, Buy‑All‑Sell‑All).

**Federal Incentives**
- [IRS Residential Clean Energy Credit (Section 25D)](https://www.irs.gov/credits-deductions/residential-clean-energy-credit): 30 % credit for solar + battery systems (2022–2032); claimable via Form 5695.

**SREC Programs**
- [EPA State Solar REC Markets](https://www.epa.gov/greenpower/solar-renewable-energy-certificates-srecs): definition 1 SREC = 1 MWh.
- [Solar United Neighbors Guide](https://www.solarunitedneighbors.org/learn-the-issues/solar-renewable-energy-credits-srecs/): consumer overview and current state programs.

**Market & Statistical Data**
- [EIA Electric Power Monthly](https://www.eia.gov/electricity/monthly/): national and state‑level retail electricity prices (Tables 5.3 & 5.6.A).
- [SEIA Solar Market Insight 2024](https://www.seia.org/research-resources/solar-market-insight-report-2024-year-review): annual capacity additions and market trends.

---

## 9. License

This project is released under the **MIT License** — open for educational and non-commercial use.
