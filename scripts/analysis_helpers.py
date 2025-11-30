# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Project Contributors

"""
Helper functions for solar PV + battery analysis
Refactored from app.py to improve code maintainability and testability
"""


def generate_load_profile(avg_load_kw, sector='residential'):
    """Generate 24-hour load profile with realistic variations

    Args:
        avg_load_kw (float): Average load in kW
        sector (str): 'residential', 'commercial', or 'industrial'

    Returns:
        list: 24-hour load profile in kW

    Residential: Morning peak (7-9 AM), afternoon dip (1-3 PM), evening peak (6-9 PM), night minimum
    Commercial: Minimal at night, gradual morning ramp (6-9 AM), sustained during business hours (9 AM-5 PM),
                sharp decline after work hours
    """

    if sector in ['commercial', 'industrial']:
        # Commercial/Industrial profile - higher during business hours, minimal at night
        # Realistic hourly factors: late night minimum -> morning ramp -> peak business -> evening decline
        profile_factors = [
            0.22, 0.18, 0.15, 0.15, 0.18, 0.28,  # 0-5: Deep night minimum
            0.42, 0.75, 0.92, 1.00, 0.98, 0.95,  # 6-11: Sharp morning ramp-up to peak
            0.92, 0.88, 0.90, 0.93, 0.85, 0.68,  # 12-17: Sustained business hours with slight dip at 1-2 PM
            0.48, 0.32, 0.25, 0.22, 0.20, 0.22   # 18-23: Sharp evening decline, low night usage
        ]
    else:
        # Residential profile - morning and strong evening peaks with night minimum
        # Peak times: 7-8 AM (morning), 6-8 PM (dinner/evening)
        # Dips: 1-3 PM (midday low), 11 PM-6 AM (sleeping hours)
        profile_factors = [
            0.35, 0.30, 0.25, 0.22, 0.25, 0.38,  # 0-5: Deep night minimum, slight rise at dawn
            0.52, 0.78, 0.82, 0.72, 0.65, 0.62,  # 6-11: Morning peak (7-9 AM), then slight decline
            0.58, 0.55, 0.58, 0.65, 0.72, 0.88,  # 12-17: Afternoon - dip at noon, then gradual rise
            1.00, 0.98, 0.88, 0.72, 0.55, 0.42   # 18-23: Strong evening peak (6-7 PM), then decline
        ]

    # Normalize to match average load
    avg_factor = sum(profile_factors) / 24
    base_load = avg_load_kw / avg_factor

    return [base_load * factor for factor in profile_factors]


def calculate_battery_metrics(battery_kwh, dod, round_trip_eff, hourly_avg_kw, daily_kwh, ac_annual):
    """Calculate battery performance metrics

    Args:
        battery_kwh (float): Battery capacity in kWh
        dod (float): Depth of discharge (0-1)
        round_trip_eff (float): Round-trip efficiency (0-1)
        hourly_avg_kw (float): Average hourly load in kW
        daily_kwh (float): Daily energy consumption in kWh
        ac_annual (float): Annual solar production in kWh

    Returns:
        dict: Battery metrics including usable capacity, backup hours, etc.
    """
    # Calculate usable capacity
    usable_kwh = battery_kwh * dod
    effective_kwh = usable_kwh * round_trip_eff

    # Calculate backup duration (hours)
    backup_hours = effective_kwh / hourly_avg_kw if hourly_avg_kw > 0 else 0

    # Calculate daily cycling potential
    daily_solar_excess = max(0, (ac_annual / 365) - daily_kwh)
    daily_charge_potential = min(daily_solar_excess, effective_kwh)

    # Evening discharge calculation (sunset to midnight ~6 hours)
    evening_load = hourly_avg_kw * 6  # 6 hours of evening usage
    evening_coverage = min(1.0, effective_kwh / evening_load) if evening_load > 0 else 0

    return {
        'usable_kwh': usable_kwh,
        'effective_kwh': effective_kwh,
        'backup_hours': backup_hours,
        'daily_charge_potential': daily_charge_potential,
        'evening_coverage': evening_coverage
    }


def calculate_financial_metrics(solar_cost, battery_cost, ac_annual, electricity_rate,
                                monthly_bill, itc_rate, srec_revenue, effective_kwh,
                                time_of_use, peak_rate, off_peak_rate):
    """Calculate financial metrics for solar + battery system

    Args:
        solar_cost (float): Solar system cost in USD
        battery_cost (float): Battery cost in USD
        ac_annual (float): Annual AC production in kWh
        electricity_rate (float): Standard electricity rate in $/kWh
        monthly_bill (float): Monthly electricity bill in USD
        itc_rate (float): Investment Tax Credit rate (0-1)
        srec_revenue (float): Annual SREC revenue in USD
        effective_kwh (float): Effective battery capacity in kWh
        time_of_use (bool): Whether TOU rates apply
        peak_rate (float): Peak TOU rate in $/kWh
        off_peak_rate (float): Off-peak TOU rate in $/kWh

    Returns:
        dict: Financial metrics including costs, savings, payback
    """
    total_cost = solar_cost + battery_cost
    total_cost_after_itc = total_cost * (1 - itc_rate)

    # Solar savings
    solar_savings = min(ac_annual * electricity_rate, monthly_bill * 12)

    # Battery value
    battery_value = effective_kwh * electricity_rate * 250 if effective_kwh > 0 else 0  # 250 cycles/year

    # Energy arbitrage savings (if TOU)
    arbitrage_savings = 0
    if time_of_use and effective_kwh > 0:
        # Charge during off-peak, discharge during peak
        daily_arbitrage = effective_kwh * (peak_rate - off_peak_rate) * 0.8  # 80% efficiency
        arbitrage_savings = daily_arbitrage * 365

    # Total annual savings
    total_annual_savings = solar_savings + battery_value + arbitrage_savings + srec_revenue

    # Payback
    simple_payback = total_cost_after_itc / total_annual_savings if total_annual_savings > 0 else 999

    return {
        'total_cost': total_cost,
        'total_cost_after_itc': total_cost_after_itc,
        'solar_savings': solar_savings,
        'battery_value': battery_value,
        'arbitrage_savings': arbitrage_savings,
        'total_annual_savings': total_annual_savings,
        'simple_payback': simple_payback
    }


def calculate_25year_projection(ac_annual, effective_kwh, total_cost_after_itc,
                                electricity_rate, srec_revenue, include_battery,
                                battery_cost, discount_rate):
    """Calculate 25-year cash flow projection

    Args:
        ac_annual (float): Annual solar production in kWh
        effective_kwh (float): Effective battery capacity in kWh
        total_cost_after_itc (float): Total system cost after ITC
        electricity_rate (float): Base electricity rate in $/kWh
        srec_revenue (float): Annual SREC revenue in USD
        include_battery (bool): Whether battery is included
        battery_cost (float): Battery replacement cost in USD
        discount_rate (float): Discount rate for NPV (0-1)

    Returns:
        dict: NPV, IRR, LCOE, cumulative savings, cash flows
    """
    cash_flows = [-total_cost_after_itc]  # Initial investment
    cumulative_savings = 0

    for year in range(1, 26):
        # Degradation factors
        solar_degradation = (1 - 0.005) ** (year - 1)  # 0.5% per year
        battery_degradation = (1 - 0.02) ** (year - 1) if year <= 10 else 0.7  # Battery replacement at year 10

        # Annual production and savings
        year_solar_production = ac_annual * solar_degradation
        year_battery_capacity = effective_kwh * battery_degradation if effective_kwh > 0 else 0

        # Electricity rate escalation (3% per year)
        escalated_rate = electricity_rate * (1.03 ** (year - 1))

        # Calculate year savings
        year_solar_savings = year_solar_production * escalated_rate
        year_battery_savings = year_battery_capacity * escalated_rate * 250 / 365 if year_battery_capacity > 0 else 0

        # Battery replacement cost at year 10
        year_cost = 0
        if year == 10 and include_battery:
            year_cost = battery_cost * 0.5  # 50% of original cost

        year_total_savings = year_solar_savings + year_battery_savings
        if srec_revenue > 0:
            year_total_savings += srec_revenue * (1.02 ** (year - 1))  # 2% escalation

        cash_flows.append(year_total_savings - year_cost)
        cumulative_savings += year_total_savings

    # Calculate NPV
    npv = sum([cf / ((1 + discount_rate) ** i) for i, cf in enumerate(cash_flows)])

    # Calculate IRR (simplified)
    irr = ((cumulative_savings / total_cost_after_itc) ** (1/25) - 1) * 100 if total_cost_after_itc > 0 else 0

    # Calculate LCOE
    lcoe = (total_cost_after_itc / (ac_annual * 25)) if ac_annual > 0 else 0

    return {
        'npv': npv,
        'irr': irr,
        'lcoe': lcoe,
        'cumulative_25y_savings': cumulative_savings,
        'net_25y_profit': cumulative_savings - total_cost_after_itc,
        'cash_flows': cash_flows
    }


def parse_advanced_budget_form(request_form):
    """Parse and validate advanced budget analysis form data

    Args:
        request_form: Flask request.form object

    Returns:
        dict: Parsed and validated form parameters
    """
    params = {
        'address': request_form.get('address', '').strip(),
        'sector': request_form.get('sector', 'residential').lower(),
        'budget_level': request_form.get('budget', 'medium'),
        'monthly_bill': float(request_form.get('monthly_bill', 0)),
        'discount_rate': float(request_form.get('discount_rate', 5)) / 100,
        'selected_solar_kw': request_form.get('selected_solar_kw'),
        'selected_battery_kwh': request_form.get('selected_battery_kwh'),
        'include_battery': request_form.get('include_battery') == 'true',
        'battery_chemistry': request_form.get('battery_chemistry', 'lfp'),
        'battery_sizes': request_form.getlist('battery_sizes'),
        'battery_power': float(request_form.get('battery_power', 5)),
        'dod': float(request_form.get('dod', 90)) / 100,
        'round_trip_eff': float(request_form.get('round_trip_efficiency', 92)) / 100,
        'backup_reserve': float(request_form.get('backup_reserve', 20)) / 100,
        'include_itc': request_form.get('include_itc') == 'true',
        'include_srec': request_form.get('include_srec') == 'true',
        'time_of_use': request_form.get('time_of_use') == 'true',
        'net_metering': request_form.get('net_metering') == 'true'
    }

    # Convert selected values to float if present
    if params['selected_solar_kw']:
        params['selected_solar_kw'] = float(params['selected_solar_kw'])
    if params['selected_battery_kwh']:
        params['selected_battery_kwh'] = float(params['selected_battery_kwh'])

    return params
