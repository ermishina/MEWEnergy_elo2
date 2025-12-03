# MEWEnergy Platform for Solar PV and Battery Investments 

> Capstone: U.S. residential solar PV + battery sizing with public APIs (ELO2/CDSP)

## Slide 01 — Team & Title
- Project Title: MEWEnergy Platform for Solar PV and Battery Investments
- Group: Mariia Ermishina

## Slide 02 — Problem & Users
- U.S. homeowners face rising tariffs and outage risk; online calculators feel generic and untrustworthy.
- Users: homeowners in every states, mobile-first, limited time.
- Need: transparent, location-specific savings/payback and backup-hour guidance.

## Slide 03 — Research Question
- How can open-access solar radiation data and public APIs be used to model and predict the optimal solar and battery system size for U.S. households to maximize energy cost savings and minimize payback time?

## Slide 04 — Data & Pipeline
- Inputs: address/ZIP → Nominatim geocode → PVWatts v8 production → URDB/Utility Rates tariffs; 25D tax credit + SREC mapping (where available).
- Approach: scenario tables (PV kW × battery kWh), savings/payback estimates, uncertainty bands (TMY weather, tariff gaps, load assumptions).


## Slide 05 — Key Findings (non-technical)
- Rising residential rates + stable consumption make PV + storage economically relevant.
- Location-specific API calls improve trust vs static averages.
- Modest batteries and west/south orientations help cover late-afternoon peaks; savings/payback should be shown as ranges.
- Caveats: TMY weather basis, tariff coverage gaps, simplified load profiles.

## Slide 06 — Prototype & Next Steps
- Working Flask prototype with 6 interactive routes: calculates savings, payback, bill offset, and backup hours for different system configurations.
- Advanced features: 25-year NPV/IRR projections, battery chemistry options, time-of-use optimization, and REST API endpoint.
- Next phase (in development): mobile-first communication tool to help homeowners share ZIP-specific scenarios with neighbors/HOA.

## Slide 07 — Ask
- Review and run the prototype; validate assumptions (tariffs, load shapes, realistic load profiles).
- Provide feedback on prototype UX and uncertainty messaging approach.
- Support needed: data validation, UX review for future mobile-first deployment, and outreach channels to target homeowners.

## Slide 8 — Closing
- Goal: transparent, API-driven sizing to help homeowners decide on PV + battery with realistic savings and backup expectations.

