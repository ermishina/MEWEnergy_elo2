# M1 — Problem Identification and Framing

## 1. Problem statement (practitioner perspective)

As a renewable energy systems engineer working with U.S. homeowners, I have observed persistent uncertainty around whether investments in rooftop solar and residential batteries are financially justified. Many online calculators rely on simplified or generic assumptions (for example, average tariffs and static load profiles), which undermines trust in their results. This project aims to provide a transparent, data-driven decision-support capability that enables households to understand the potential cost savings and risk profile of solar PV and battery investments under realistic local conditions.

## 2. Background review of the research domain

Building on the broader market and policy review in `0_domain_study/README.md`, this analysis focuses on the interaction between residential cooling loads and rooftop PV generation:

- **Cooling and heating dominate:** More than half (≈ **52%** in 2020) of residential energy is used for space heating and air conditioning. [EIA – Energy use in homes](https://www.eia.gov/energyexplained/use-of-energy/homes.php).  
- **Peak timing and lag:** Summer building peak loads are primarily driven by air conditioning. PV reduces peak demand by ~20–60% of installed capacity, but the thermal peak typically lags the solar peak by 2–4 hours (solar noon ≈ 1 pm DST vs. building peak ≈ 3–6 pm). [NREL (Denholm et al., 2009)](https://docs.nrel.gov/docs/fy10osti/45832.pdf).  
- **Orientation for late-afternoon peaks:** In a Pecan Street field study in Austin, west-facing rooftop PV produced ~49–50% more electricity during 3–7 pm and reduced peak grid demand by ~65%, compared to ~54% for south-facing arrays. [Pecan Street](https://www.pecanstreet.org/2013/11/are-solar-panels-facing-the-wrong-direction/) and [DOE report](https://www.energy.gov/sites/default/files/2017/08/f36/Pecan_Street_Making-Electricity-Value-Proposition-Consumer.pdf).  
- **Operational measures to bridge the gap:** Pre-cooling or a small battery can shift cooling load into PV hours and flatten the late-afternoon peak. See, for example, [Naderi et al., 2022](https://www.sciencedirect.com/science/article/pii/S0378778822005114).  

Taken together, these findings motivate a modelling approach that explicitly tests the alignment between PV production, cooling loads, and storage strategies.

## 3. Group understanding of the problem domain

As a team, we understand the problem domain as an interconnected system involving:

- **Environment and climate:** Local solar resource and weather patterns drive both PV generation and cooling demand.  
- **Technology and system design:** PV orientation, capacity, inverter efficiency, and battery size determine how much demand can be shifted or covered by onsite generation.  
- **Tariffs, incentives, and policy:** Retail rates, time-of-use structures, net-metering rules, and incentives (for example, the Residential Clean Energy Credit and SREC markets) shape the economic value of each kWh generated or stored.  
- **Household behavior:** Comfort preferences, pre-cooling practices, and load-shifting behaviors influence the actual coincidence of load and generation.  

Our modelling work in this milestone therefore treats the household, utility, and policy environment as a coupled system rather than as isolated components.

## 4. Actionable research question

Grounded in this domain analysis, we formulate the following actionable research question:

> **How can open-access solar radiation data and public APIs be used to model and predict the optimal solar and battery system size for U.S. households to maximize energy cost savings and minimize payback time?**

This question guides the data requirements, model structure, and evaluation metrics for subsequent milestones.

## 5. Planning documents (group norms, learning goals, constraints, communication plan)

Planning artefacts for this project are maintained in the team’s shared collaboration space and summarized here:

- **Group norms:** Clear expectations for preparation, meeting cadence, and respectful, constructive feedback.  
- **Learning goals:** Applying public energy and solar APIs, designing reproducible data pipelines, and interpreting techno-economic models for decision support.  
- **Constraints:** Limited project duration, reliance on open data and APIs, no real-money deployment, and a strong emphasis on transparency over maximum model complexity.  
- **Communication plan:** Asynchronous coordination through course communication channels, supplemented by regular synchronous check-ins for key decisions.  

Key assumptions and decisions captured in these documents are reflected in the modelling choices described in this repository.

## 6. Milestone 1 retrospective

From Milestone 1, we draw the following lessons:

- **What worked well:** Early alignment on a concrete problem statement, a clear focus on residential solar-plus-storage, and the use of authoritative public data sources and APIs.  
- **What was challenging:** Managing the breadth of the literature and policy landscape, and balancing methodological ambition with the time and data constraints of the course.  
- **What we will change for M2:** Begin prototyping with small, representative datasets earlier, maintain tighter iteration loops between domain research and the data pipeline, and document modelling assumptions more explicitly.  

These insights inform the design and prioritization of tasks in Milestone 2.

## 7. Data sources and analytical workflow

To underpin the analytical framework of the MEWEnergy platform, we leverage three key publicly available APIs and datasets. Each one feeds a distinct part of the modelling pipeline — from geographic identification to solar resource assessment, through to system performance simulation. All are fully documented, enabling replication and transparency.

### 7.1 Geolocation – Nominatim API (OpenStreetMap Foundation)

We use Nominatim to convert a user-provided address (for example, “174 W 137th St Apt 12, New York, NY”) into precise geographic coordinates (latitude/longitude). These coordinates serve as the foundation for downstream resource and performance calculations.  
> The service supports both forward (address → coordinates) and reverse (coordinates → address) geocoding. [nominatim.org](https://nominatim.org/?utm_source=chatgpt.com)  
**Implementation note:** We call the endpoint `GET https://nominatim.openstreetmap.org/search?q=<address>&format=json`. We honour the usage policy (rate limits, user-agent identification). [operations.osmfoundation.org](https://operations.osmfoundation.org/policies/nominatim/?utm_source=chatgpt.com)  
**Role in platform:** The returned coordinates feed into both the solar resource API and the PV generation simulation, ensuring location specificity.

### 7.2 Solar resource data – NREL Solar Resource API

Once the location is known, we query the Solar Resource API to retrieve key metrics such as Global Horizontal Irradiance (GHI), Direct Normal Irradiance (DNI), and tilt-adjusted solar insolation for the given site. These inputs reflect long-term climatic averages that are pivotal for estimating solar output.  
> The endpoint is `GET /api/solar/solar_resource/v1.json?lat=<lat>&lon=<lon>&api_key=<KEY>`. [developer.nrel.gov](https://developer.nrel.gov/docs/solar/solar-resource-v1/?utm_source=chatgpt.com)  
**Implementation note:** We normalise the data into kWh/m²/day or kWh/m²/year as appropriate and use this as a baseline for generation modelling.  
**Role in platform:** Provides the environmental input layer; without it, system generation estimates would rely on generic assumptions rather than site-specific data.

### 7.3 PV simulation – PVWatts® API v8 (NREL)

With geographic and irradiance inputs available, we run a performance simulation using PVWatts v8, which estimates annual AC output (in kWh) for a defined PV system (capacity, tilt, azimuth, losses) at the chosen location.  
> Documentation: “NREL’s PVWatts® API estimates the energy production of grid-connected photovoltaic (PV) energy systems based on a few simple inputs.” [developer.nrel.gov](https://developer.nrel.gov/docs/solar/pvwatts/v8/?utm_source=chatgpt.com)  
**Implementation note:** Example call:  
`GET https://developer.nrel.gov/api/solar/pvwatts/v8.json?api_key=<KEY>&lat=<LAT>&lon=<LON>&system_capacity=5&tilt=30&azimuth=180&losses=14`  
The result includes parameters such as `ac_annual` (kWh/year), which we feed into our financial model.  
**Role in platform:** This simulation output, when combined with utility rates and incentives, enables us to compute cost savings, payback periods, and investment feasibility.

---

### 7.4 Workflow summary

1. **User input** → Address → Nominatim → (lat, lon).  
2. **Solar input** → Solar Resource API → site-specific irradiance metrics.  
3. **System simulation** → PVWatts API → expected annual yield.  
4. **Financial modelling** → Yield + utility/incentive data → savings and payback figures.  

---

### 7.5 Data quality, limitations, and documentation

- **Coverage and granularity:** NREL datasets rely on historical weather observations (for example, via the National Solar Radiation Database, NSRDB) for accuracy, but they still represent typical meteorological years rather than real-time variability. [pvwatts.nrel.gov](https://pvwatts.nrel.gov/version_8.php?utm_source=chatgpt.com)  
- **Geocoding limitations:** Nominatim is powered by community-sourced OpenStreetMap data; address matching may be imperfect in remote or newly developed areas. [OpenStreetMap](https://wiki.openstreetmap.org/wiki/Nominatim?utm_source=chatgpt.com)  
- **Modelling assumptions:** The PVWatts output uses fixed assumption blocks (module type, system losses, performance ratio) and does not capture every site-specific variable (for example, shading, maintenance, unexpected degradation). [developer.nrel.gov](https://developer.nrel.gov/docs/solar/pvwatts/v8/?utm_source=chatgpt.com)  
- **API constraints:** Rate limits apply (for example, NREL’s data download service: ~1000 requests/day, ~1 per 2 seconds for some endpoints), which influences batch processing strategies. [developer.nrel.gov](https://developer.nrel.gov/docs/solar/nsrdb/guide/?utm_source=chatgpt.com)  

Reusable API helpers and the sizing prototype live in `scripts/` (see `scripts/api.py`, `scripts/config.py`, and `scripts/README.md`). Datasets and cleaned outputs will be generated and documented in subsequent milestones; any derived files should be stored under `data/` with accompanying notes for reproducibility.
