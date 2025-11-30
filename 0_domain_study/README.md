# M1. Domain Research & Background

## 1. Introduction
The U.S. residential energy landscape is undergoing rapid change as electricity prices continue to rise due to infrastructure modernization, inflationary pressures, and fuel price volatility. This section provides a data-driven overview of national consumption trends, price developments, and the growing importance of distributed solar PV and battery systems.

## 2. U.S. Energy Context and Market Overview
According to the [*Electric Power Monthly Tables 5.3 & 5.6.A (2024)*](https://www.eia.gov/electricity/monthly/)  , the *average U.S. household* consumed approximately **10,500 kWh of electricity per year** in 2023 — roughly 875 kWh per month — a figure that has remained relatively stable since 2010 despite improvements in appliance efficiency. However, the [*Average Monthly Bill – Residential Customers (2024)*](https://www.eia.gov/electricity/sales_revenue_price/)   has risen from **$115 in 2020 to $153 in 2024**, reflecting both higher retail rates and increasing use of air conditioning and electric heating.  
Average **residential electricity prices** climbed from **13.6 ¢/kWh in 2020 to 16.7 ¢/kWh in 2024**, with forecasts suggesting continued growth toward **18 ¢/kWh by 2026** as utilities modernize grids and recover infrastructure investments. [*Solar Market Insight 2024 Year-in-Review*](https://www.seia.org/research-resources/solar-market-insight-report-2024-year-review).  
These upward trends place financial pressure on homeowners and underscore the economic value of distributed solar PV and battery storage systems, which can significantly offset grid consumption and stabilize long-term energy costs.

### Residential Energy Sources (Fuel Mix)

**Electricity and natural gas are the most‑used energy sources in U.S. homes.** In 2020, retail **electricity** purchases accounted for about **44%** of total residential end‑use energy consumption, and **natural gas**—used in about **58–61% of homes**—accounted for about **43%**. **Petroleum fuels** (heating oil, kerosene, LPG/propane) made up about **8%**, and **renewables** (wood, solar, geothermal) about **5%** of residential energy end use. Taken together, **fossil fuels account for just over half (~51%) of residential end‑use energy** (natural gas ~43% + petroleum ~8% in 2020). 

*Sources:* U.S. Energy Information Administration — *Energy use in homes* (https://www.eia.gov/energyexplained/use-of-energy/homes.php) and *Today in Energy: The majority of U.S. households used natural gas in 2020* (https://www.eia.gov/todayinenergy/detail.php?id=55940).



### Data and Modeling Approach

The platform converts user-provided **addresses or ZIP codes** into geographic coordinates using **OpenStreetMap Nominatim**, ensuring compliance with its open-data usage policy by providing a custom User-Agent and request throttling. It then queries **NREL’s PVWatts® v8 API**, which uses **NSRDB 2020 Typical Meteorological Year (TMY)** weather data to estimate site-specific solar irradiance and energy production outputs such as `ac_annual` and `ac_monthly`. These outputs form the foundation of the project’s savings, payback, and SREC (Solar Renewable Energy Credit) calculations.



### SREC Revenue Integration

In states with established SREC programs, homeowners earn **1 SREC for every 1 MWh (1,000 kWh)** of solar electricity produced. These credits can be sold for additional income through state markets or aggregators. The application estimates potential SREC revenue using a state-to-price mapping table that can be expanded with real market data from APIs such as **SRECTrade** or **PJM GATS**.
## 3. Policy and Incentive Landscape
The **Inflation Reduction Act (IRA, 2022)** extended and enhanced the federal *Residential Clean Energy Credit (Section 25D)*, allowing homeowners to deduct **30% of qualified solar and battery system costs** from their federal taxes through 2032. In addition, many states offer *Solar Renewable Energy Credits (SRECs)*, which provide homeowners additional income for every 1,000 kWh of solar electricity generated. These incentives have accelerated adoption, especially in states with high retail rates like California, New York, and Massachusetts.

## 4. Economic and Social Impact
Rising energy costs disproportionately affect lower-income households, increasing the so-called *energy burden*. According to EIA’s 2024 data, U.S. residential energy expenditure as a share of income has risen by nearly 10% since 2020. Distributed solar PV adoption not only provides a hedge against future rate increases but also promotes local energy resilience and contributes to carbon emission reduction.
### Economic Framework

Local utility tariffs are retrieved through **NREL’s Utility Rates API** and **OpenEI’s Utility Rate Database (URDB)**. While the former provides average annual rates by sector, URDB adds depth with time-of-use structures and **Distributed Generation (DG) rules**, including *Net Metering*, *Net Billing*, and *Buy-All-Sell-All* mechanisms. Federal incentives are modeled using the **IRS Residential Clean Energy Credit (Section 25D)**, offering a **30 % tax credit** for qualified solar and battery storage systems placed in service between 2022 and 2032 (claimed via **IRS Form 5695**).


## 5. Technological and Data Context
Publicly available datasets and APIs (e.g., NREL’s PVWatts, OpenEI Utility Rate Database, SRECTrade) allow modeling of both technical performance and financial feasibility. However, many consumer-facing calculators oversimplify these datasets, using static assumptions. The MEWEnergy platform addresses this gap through a transparent, API-driven architecture that integrates geographic, solar, and economic data to produce personalized recommendations.

## 6. Summary and Relevance to Research Question
The continuous rise in U.S. residential electricity costs, combined with strong policy support for renewables, creates a compelling environment for data-driven decision tools. The MEWEnergy platform responds to this by enabling homeowners to simulate and evaluate solar PV and battery investments with real-world data. This analysis directly informs the project’s core research question:

> **How can open-access solar radiation data and public APIs be used to model and predict the optimal solar and battery system size for U.S. households to maximize energy cost savings and minimize payback time?**

