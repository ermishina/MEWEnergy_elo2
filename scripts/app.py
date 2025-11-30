# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Project Contributors

# Standard library imports
import os
from pathlib import Path

# Third-party imports
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for

# Local application imports
from api import geocode_address, get_solar_info_by_coordinates, solar_resource_data, pvwatts_estimate, utility_rate

# Load environment variables from .env file (prefer file next to this script)
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv()  # fallback to cwd if provided

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# --- SREC helpers ---
def reverse_geocode_state(lat, lon):
    """
    Return U.S. state name for given coordinates using Nominatim reverse geocoding.

    Args:
        lat (float): Latitude coordinate
        lon (float): Longitude coordinate

    Returns:
        str or None: State name if found, None otherwise
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {"lat": lat, "lon": lon, "format": "json", "zoom": 5, "addressdetails": 1}
    headers = {"User-Agent": "MEWEnergy/1.0 (contact: support@mewenergy.local)"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        js = resp.json()
        return (js.get("address") or {}).get("state")
    except Exception:
        return None

def get_srec_price_usd_per_mwh(state_name):
    """
    Return conservative placeholder SREC price (USD/MWh) by U.S. state.
    Replace these with live prices from your chosen data source (e.g., SRECTrade/GATS/API).

    Args:
        state_name (str): Name of the U.S. state

    Returns:
        float: SREC price in USD per MWh (0.0 if state not found)
    """
    SREC_PRICE = {
        "New Jersey": 220.0,
        "Massachusetts": 280.0,
        "Pennsylvania": 45.0,
        "District of Columbia": 420.0,
        "Maryland": 60.0,
        "Illinois": 70.0,
        "Ohio": 15.0,
        "Virginia": 35.0
    }
    return SREC_PRICE.get(state_name, 0.0)

@app.route('/')
def index():
    """Main page with address input form"""
    return render_template('index.html')
# New route for budget-based analysis
@app.route('/budget-analysis', methods=['POST'])
def budget_analysis():
    """
    Compute solar system suggestion based on budget.

    Returns:
        Rendered template with budget analysis scenarios or redirect to index on error
    """
    address = request.form.get('address', '').strip()
    sector = request.form.get('sector', 'residential').lower()
    budget_level = request.form.get('budget', 'medium')  # small, medium, large
    
    # Budget definitions (USD)
    BUDGET_RANGES = {
        'small': {'min': 5000, 'max': 10000, 'name': 'Klein'},
        'medium': {'min': 10000, 'max': 20000, 'name': 'Mittel'},
        'large': {'min': 20000, 'max': 40000, 'name': 'GroÃŸ'}
    }
    
    if not address:
        flash('Bitte geben Sie eine gÃ¼ltige Adresse ein.', 'error')
        return redirect(url_for('index'))
    
    # Geocoding
    coords = geocode_address(address)
    if not coords:
        flash('Adresse konnte nicht gefunden werden.', 'error')
        return redirect(url_for('index'))
    
    lat, lon = coords
    
    # Fetch electricity rate
    electricity_rate = 0.30
    try:
        util = utility_rate(lat, lon, sector=sector)
        if util and isinstance(util.get("rate"), (int, float)):
            electricity_rate = float(util["rate"])
    except Exception as e:
        print(f"Utility Rates API error: {e}")
    
    # Cost per kW (installation)
    cost_per_kw = 2500.0
    
    # Compute possible system sizes based on budget
    budget_range = BUDGET_RANGES[budget_level]
    min_capacity_kw = budget_range['min'] / cost_per_kw
    max_capacity_kw = budget_range['max'] / cost_per_kw
    optimal_capacity_kw = (min_capacity_kw + max_capacity_kw) / 2
    
    # Simuliere verschiedene Szenarien
    scenarios = []
    
    for capacity in [min_capacity_kw, optimal_capacity_kw, max_capacity_kw]:
        try:
            pvwatts_data = pvwatts_estimate(lat, lon, system_capacity_kw=capacity)
            
            if pvwatts_data and 'outputs' in pvwatts_data:
                ac_annual = pvwatts_data['outputs'].get('ac_annual', 0)
                
                # Compute simple economics
                annual_savings = ac_annual * electricity_rate
                investment_cost = capacity * cost_per_kw
                payback_years = investment_cost / annual_savings if annual_savings > 0 else 999
                
                # 25-year projection
                projection = []
                cumulative_savings = 0
                for year in range(1, 26):
                    # Degradation: 0.5% per year
                    degradation_factor = (1 - 0.005) ** (year - 1)
                    year_production = ac_annual * degradation_factor
                    year_savings = year_production * electricity_rate * (1.03 ** (year - 1))  # 3% electricity price escalation
                    cumulative_savings += year_savings
                    
                    projection.append({
                        'year': year,
                        'production': year_production,
                        'savings': year_savings,
                        'cumulative_savings': cumulative_savings,
                        'net_profit': cumulative_savings - investment_cost
                    })
                
                scenarios.append({
                    'capacity_kw': capacity,
                    'investment': investment_cost,
                    'annual_production': ac_annual,
                    'annual_savings': annual_savings,
                    'payback_years': payback_years,
                    'total_25y_savings': cumulative_savings,
                    'net_25y_profit': cumulative_savings - investment_cost,
                    'roi_25y': ((cumulative_savings - investment_cost) / investment_cost * 100),
                    'projection': projection
                })
        
        except Exception as e:
            print(f"Error calculating scenario: {e}")
    
    return render_template('budget_analysis.html',
                          address=address,
                          lat=lat,
                          lon=lon,
                          budget_level=budget_level,
                          budget_name=BUDGET_RANGES[budget_level]['name'],
                          budget_range=budget_range,
                          scenarios=scenarios,
                          electricity_rate=electricity_rate,
                          cost_per_kw=cost_per_kw)
@app.route('/search', methods=['POST'])
def search_address():
    """
    Handle address search and display solar data.

    Returns:
        Rendered template with solar analysis results or redirect to index on error
    """
    address = request.form.get('address', '').strip()

    if not address:
        flash('Please enter a valid address.', 'error')
        return redirect(url_for('index'))

    # Geocode the address
    coords = geocode_address(address)

    if not coords:
        flash('Address could not be found. Please verify the address and try again.', 'error')
        return redirect(url_for('index'))

    lat, lon = coords

    try:
        # Get solar resource data
        solar_data = solar_resource_data(lat, lon)

        # Try to get PVWatts estimate, but continue if it fails
        pvwatts_data = None
        system_capacity = float(request.form.get('system_capacity', 5.0))
        sector = request.form.get('sector', 'residential').lower()
        if sector not in ('residential', 'commercial', 'industrial'):
            sector = 'residential'

        try:
            pvwatts_data = pvwatts_estimate(lat, lon, system_capacity_kw=system_capacity)
        except Exception as pvwatts_error:
            print(f"PVWatts API error: {pvwatts_error}")
            # Continue without PVWatts data

        # Fetch local electricity rate via NREL Utility Rates API
        electricity_rate = 0.30  # default fallback ($/kWh)
        utility_meta = None
        try:
            util = utility_rate(lat, lon, sector=sector)
            if util and isinstance(util.get("rate"), (int, float)):
                electricity_rate = float(util["rate"])  # $/kWh
            utility_meta = {"name": util.get("utility_name")} if util else None
        except Exception as utility_err:
            print(f"Utility Rates API error: {utility_err}")

        return render_template('results.html',
                             address=address,
                             lat=lat,
                             lon=lon,
                             solar_data=solar_data,
                             pvwatts_data=pvwatts_data,
                             system_capacity=system_capacity,
                             electricity_rate=electricity_rate,
                             utility_meta=utility_meta,
                             sector=sector)

    except Exception as e:
        flash(f'Error retrieving solar data: {str(e).replace("%", "%%")}', 'error')
        return redirect(url_for('index'))

@app.route('/api/search', methods=['POST'])
def api_search():
    """
    API endpoint for address search.

    Returns:
        JSON response with solar data or error message
    """
    data = request.get_json()

    if not data or 'address' not in data:
        return jsonify({'error': 'Address is required'}), 400

    address = data['address'].strip()

    if not address:
        return jsonify({'error': 'Address cannot be empty'}), 400

    # Geocode the address
    coords = geocode_address(address)

    if not coords:
        return jsonify({'error': 'Address not found'}), 404

    lat, lon = coords

    try:
        # Get solar resource data
        solar_data = solar_resource_data(lat, lon)

        # Try to get PVWatts estimate, but continue if it fails
        pvwatts_data = None
        system_capacity = data.get('system_capacity', 5.0)
        sector = str(data.get('sector', 'residential')).lower()
        if sector not in ('residential', 'commercial', 'industrial'):
            sector = 'residential'

        try:
            pvwatts_data = pvwatts_estimate(lat, lon, system_capacity_kw=system_capacity)
        except Exception as pvwatts_error:
            print(f"PVWatts API error: {pvwatts_error}")
            # Continue without PVWatts data

        # Fetch local electricity rate via NREL Utility Rates API
        electricity_rate = 0.30
        utility_meta = None
        try:
            util = utility_rate(lat, lon, sector=sector)
            if util and isinstance(util.get("rate"), (int, float)):
                electricity_rate = float(util["rate"])  # $/kWh
            utility_meta = {"name": util.get("utility_name")} if util else None
        except Exception as utility_err:
            print(f"Utility Rates API error: {utility_err}")

        return jsonify({
            'address': address,
            'coordinates': {'lat': lat, 'lon': lon},
            'solar_data': solar_data,
            'pvwatts_data': pvwatts_data,
            'electricity_rate': electricity_rate,
            'utility': utility_meta,
            'sector': sector
        })

    except Exception as e:
        return jsonify({'error': f'Error retrieving solar data: {str(e).replace("%", "%%")}'}), 500
@app.route('/advanced-budget-analysis', methods=['POST'])
def advanced_budget_analysis():
    """
    Advanced solar + battery analysis with comprehensive financial modeling.

    Performs detailed analysis including:
    - Multiple solar system sizes
    - Battery energy storage options
    - 25-year financial projections
    - NPV, IRR, and LCOE calculations
    - SREC revenue modeling (if applicable)

    Returns:
        Rendered template with comprehensive analysis results or redirect to index on error
    """
    
    # Get form data
    address = request.form.get('address', '').strip()
    sector = request.form.get('sector', 'residential').lower()
    budget_level = request.form.get('budget', 'medium')
    monthly_bill = float(request.form.get('monthly_bill', 0))
    # Discount rate removed from form - using default 5%
    discount_rate = float(request.form.get('discount_rate', 5)) / 100

    # Get selected scenario values (if user clicked "Select This")
    selected_solar_kw = request.form.get('selected_solar_kw')
    selected_battery_kwh = request.form.get('selected_battery_kwh')
    if selected_solar_kw:
        selected_solar_kw = float(selected_solar_kw)
    if selected_battery_kwh:
        selected_battery_kwh = float(selected_battery_kwh)
    
    # Battery parameters
    include_battery = request.form.get('include_battery') == 'true'
    battery_chemistry = request.form.get('battery_chemistry', 'lfp')
    battery_sizes = request.form.getlist('battery_sizes')
    battery_power = float(request.form.get('battery_power', 5))
    dod = float(request.form.get('dod', 90)) / 100
    round_trip_eff = float(request.form.get('round_trip_efficiency', 92)) / 100
    backup_reserve = float(request.form.get('backup_reserve', 20)) / 100
    
    # Advanced options - these fields were removed from form, using smart defaults
    include_itc = request.form.get('include_itc', 'true') == 'true'  # Default: True (ITC typically claimed)
    include_srec = request.form.get('include_srec', 'false') == 'true'  # Default: False (not available everywhere)
    time_of_use = request.form.get('time_of_use', 'false') == 'true'  # Default: False (standard rates)
    net_metering = request.form.get('net_metering', 'true') == 'true'  # Default: True (commonly available)
    
    if not address:
        flash('Please provide a valid installation address.', 'error')
        return redirect(url_for('index'))
    
    # Geocoding
    coords = geocode_address(address)
    if not coords:
        flash('Unable to geocode address. Please verify and retry.', 'error')
        return redirect(url_for('index'))
    
    lat, lon = coords
    state_name = reverse_geocode_state(lat, lon)
    srec_price = get_srec_price_usd_per_mwh(state_name) if include_srec else 0.0
    
    # Get utility rate
    electricity_rate = 0.30  # $/kWh default
    peak_rate = 0.45  # Peak TOU rate
    off_peak_rate = 0.15  # Off-peak TOU rate
    
    try:
        util = utility_rate(lat, lon, sector=sector)
        if util and isinstance(util.get("rate"), (int, float)):
            electricity_rate = float(util["rate"])
            if time_of_use:
                peak_rate = electricity_rate * 1.5
                off_peak_rate = electricity_rate * 0.5
    except Exception as e:
        print(f"Utility API error: {e}")
    
    # Calculate baseline consumption
    if monthly_bill <= 0:
        flash('Please provide monthly electricity cost for accurate analysis.', 'error')
        return redirect(url_for('index'))
    
    monthly_kwh = monthly_bill / electricity_rate
    annual_kwh = monthly_kwh * 12
    daily_kwh = monthly_kwh / 30
    hourly_avg_kw = daily_kwh / 24
    
    # Generate realistic load profiles based on sector
    def generate_load_profile(avg_load_kw, sector='residential'):
        """Generate 24-hour load profile with realistic variations

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
    
    # Generate hourly load profile
    hourly_load_profile = generate_load_profile(hourly_avg_kw, sector)
    
    # Budget definitions (expanded)
    BUDGET_RANGES = {
        'small': {'min': 10000, 'max': 20000, 'name': 'Entry Level'},
        'medium': {'min': 20000, 'max': 40000, 'name': 'Standard'},
        'large': {'min': 40000, 'max': 80000, 'name': 'Premium'},
        'enterprise': {'min': 80000, 'max': 150000, 'name': 'Enterprise'}
    }
    
    if budget_level == 'custom':
        budget_range = {
            'min': float(request.form.get('custom_min', 20000)),
            'max': float(request.form.get('custom_max', 40000)),
            'name': 'Custom'
        }
    else:
        budget_range = BUDGET_RANGES.get(budget_level, BUDGET_RANGES['medium'])
    
    # Battery cost structure
    BATTERY_COSTS = {
        'lfp': 450,  # $/kWh
        'nmc': 550,
        'lto': 800
    }
    
    battery_cost_per_kwh = BATTERY_COSTS.get(battery_chemistry, 450)
    solar_cost_per_kw = 2500  # $/kW
    
    # Apply incentives
    itc_rate = 0.30 if include_itc else 0
    
    # Calculate solar system sizes
    min_solar_kw = (budget_range['min'] * 0.7) / solar_cost_per_kw  # 70% for solar
    max_solar_kw = (budget_range['max'] * 0.7) / solar_cost_per_kw
    optimal_solar_kw = (min_solar_kw + max_solar_kw) / 2
    
    # Comprehensive analysis results
    analysis_results = {
        'location': {
            'address': address,
            'latitude': lat,
            'longitude': lon
        },
        'consumption': {
            'monthly_kwh': monthly_kwh,
            'annual_kwh': annual_kwh,
            'daily_kwh': daily_kwh,
            'avg_load_kw': hourly_avg_kw,
            'monthly_cost': monthly_bill,
            'hourly_profile': hourly_load_profile  # NEW: Add hourly profile
        },
        'rates': {
            'standard': electricity_rate,
            'peak': peak_rate if time_of_use else None,
            'off_peak': off_peak_rate if time_of_use else None
        },
        # Store original form parameters for scenario selection
        'form_params': {
            'address': address,
            'sector': sector,
            'budget': budget_level,
            'monthly_bill': monthly_bill,
            'discount_rate': discount_rate * 100,  # Convert back to percentage
            'include_battery': include_battery,
            'battery_chemistry': battery_chemistry,
            'battery_sizes': battery_sizes,
            'battery_power': battery_power,
            'dod': dod * 100,  # Convert back to percentage
            'round_trip_efficiency': round_trip_eff * 100,  # Convert back to percentage
            'backup_reserve': backup_reserve * 100,  # Convert back to percentage
            'include_itc': include_itc,
            'include_srec': include_srec,
            'time_of_use': time_of_use,
            'net_metering': net_metering,
            'selected_solar_kw': selected_solar_kw,  # Track selected scenario
            'selected_battery_kwh': selected_battery_kwh,
            'selected_scenario_index': -1  # Will be set after scenarios are generated
        },
        'scenarios': []
    }
    
    # Generate scenarios for different solar sizes
    for solar_capacity in [min_solar_kw, optimal_solar_kw, max_solar_kw]:
        try:
            # Get solar production data
            pvwatts_data = pvwatts_estimate(lat, lon, system_capacity_kw=solar_capacity)
            
            if not pvwatts_data or 'outputs' not in pvwatts_data:
                continue
            
            outputs = pvwatts_data['outputs']
            ac_annual = outputs.get('ac_annual', 0)
            ac_monthly = outputs.get('ac_monthly', [0]*12)
            
            # Solar-only scenario first
            solar_cost = solar_capacity * solar_cost_per_kw
            solar_cost_after_itc = solar_cost * (1 - itc_rate)
            
            scenario_base = {
                'solar_kw': solar_capacity,
                'annual_production': ac_annual,
                'monthly_production': ac_monthly,
                'self_consumption_rate': min(1.0, ac_annual / annual_kwh),
                'solar_cost': solar_cost,
                'solar_cost_after_itc': solar_cost_after_itc
            }
            
            # Add battery configurations if selected
            if include_battery and battery_sizes:
                for battery_kwh in battery_sizes:
                    battery_kwh = float(battery_kwh)
                    battery_cost = battery_kwh * battery_cost_per_kwh
                    total_cost = solar_cost + battery_cost
                    total_cost_after_itc = total_cost * (1 - itc_rate)
                    
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
                    
                    # Financial calculations
                    # Energy arbitrage savings (if TOU)
                    arbitrage_savings = 0
                    if time_of_use:
                        # Charge during off-peak, discharge during peak
                        daily_arbitrage = effective_kwh * (peak_rate - off_peak_rate) * 0.8  # 80% efficiency
                        arbitrage_savings = daily_arbitrage * 365
                    
                    # Total annual savings
                    solar_savings = min(ac_annual * electricity_rate, monthly_bill * 12)
                    battery_value = effective_kwh * electricity_rate * 250  # 250 cycles/year
                    total_annual_savings = solar_savings + battery_value + arbitrage_savings
                    
                    # SREC revenue (if applicable)
                    srec_revenue = 0
                    if include_srec:
                        # SREC revenue = MWh * state-specific SREC price
                        srec_revenue = (ac_annual / 1000) * srec_price
                        total_annual_savings += srec_revenue
                    
                    # Payback and NPV calculations
                    simple_payback = total_cost_after_itc / total_annual_savings if total_annual_savings > 0 else 999
                    
                    # 25-year cash flow analysis
                    cash_flows = [-total_cost_after_itc]  # Initial investment
                    cumulative_savings = 0
                    
                    for year in range(1, 26):
                        # Degradation factors
                        solar_degradation = (1 - 0.005) ** (year - 1)
                        battery_degradation = (1 - 0.02) ** (year - 1) if year <= 10 else 0.7  # Battery replacement at year 10
                        
                        # Annual production and savings
                        year_solar_production = ac_annual * solar_degradation
                        year_battery_capacity = effective_kwh * battery_degradation
                        
                        # Electricity rate escalation
                        escalated_rate = electricity_rate * (1.03 ** (year - 1))
                        
                        # Calculate year savings
                        year_solar_savings = year_solar_production * escalated_rate
                        year_battery_savings = year_battery_capacity * escalated_rate * 250 / 365
                        
                        # Battery replacement cost at year 10
                        if year == 10 and include_battery:
                            battery_replacement = battery_cost * 0.5  # 50% of original cost
                            cash_flows.append(-battery_replacement)
                        
                        year_total_savings = year_solar_savings + year_battery_savings
                        if include_srec:
                            year_total_savings += srec_revenue * (1.02 ** (year - 1))
                        
                        cash_flows.append(year_total_savings)
                        cumulative_savings += year_total_savings
                    
                    # Calculate NPV
                    npv = sum([cf / ((1 + discount_rate) ** i) for i, cf in enumerate(cash_flows)])
                    
                    # Calculate IRR (simplified)
                    irr = ((cumulative_savings / total_cost_after_itc) ** (1/25) - 1) * 100 if total_cost_after_itc > 0 else 0
                    
                    # Create scenario object
                    scenario = {
                        **scenario_base,
                        'battery_kwh': battery_kwh,
                        'battery_chemistry': battery_chemistry,
                        'battery_cost': battery_cost,
                        'usable_capacity': usable_kwh,
                        'effective_capacity': effective_kwh,
                        'backup_hours': backup_hours,
                        'evening_coverage_percent': evening_coverage * 100,
                        'daily_charge_potential': daily_charge_potential,
                        'total_system_cost': total_cost,
                        'total_cost_after_incentives': total_cost_after_itc,
                        'annual_savings': total_annual_savings,
                        'arbitrage_savings': arbitrage_savings,
                        'srec_revenue': srec_revenue,
                        'srec_price_usd_per_mwh': srec_price,
                        'srec_state': state_name,
                        'simple_payback_years': simple_payback,
                        'npv': npv,
                        'irr': irr,
                        'lcoe': (total_cost_after_itc / (ac_annual * 25)) if ac_annual > 0 else 0,  # $/kWh
                        'cumulative_25y_savings': cumulative_savings,
                        'net_25y_profit': cumulative_savings - total_cost_after_itc
                    }
                    
                    analysis_results['scenarios'].append(scenario)
            
            else:
                # Solar-only scenario
                solar_savings = min(ac_annual * electricity_rate, monthly_bill * 12)
                simple_payback = solar_cost_after_itc / solar_savings if solar_savings > 0 else 999

                # Calculate SREC revenue (once for consistency with battery scenarios)
                srec_revenue = 0
                if include_srec:
                    srec_revenue = (ac_annual / 1000) * srec_price

                # 25-year cash flow analysis for solar-only
                cash_flows = [-solar_cost_after_itc]  # Initial investment
                cumulative_savings = 0

                for year in range(1, 26):
                    # Solar degradation
                    solar_degradation = (1 - 0.005) ** (year - 1)
                    year_solar_production = ac_annual * solar_degradation

                    # Electricity rate escalation
                    escalated_rate = electricity_rate * (1.03 ** (year - 1))

                    # Annual savings
                    year_total_savings = year_solar_production * escalated_rate

                    # SREC revenue (if applicable)
                    if include_srec:
                        year_total_savings += srec_revenue * (1.02 ** (year - 1))

                    cash_flows.append(year_total_savings)
                    cumulative_savings += year_total_savings

                # Calculate NPV
                npv = sum([cf / ((1 + discount_rate) ** i) for i, cf in enumerate(cash_flows)])

                # Calculate IRR (simplified)
                irr = ((cumulative_savings / solar_cost_after_itc) ** (1/25) - 1) * 100 if solar_cost_after_itc > 0 else 0

                scenario = {
                    **scenario_base,
                    'battery_kwh': 0,
                    'total_system_cost': solar_cost,
                    'total_cost_after_incentives': solar_cost_after_itc,
                    'annual_savings': solar_savings,
                    'srec_revenue': srec_revenue,
                    'srec_price_usd_per_mwh': srec_price,
                    'srec_state': state_name,
                    'simple_payback_years': simple_payback,
                    'npv': npv,
                    'irr': irr,
                    'lcoe': (solar_cost_after_itc / (ac_annual * 25)) if ac_annual > 0 else 0,
                    'cumulative_25y_savings': cumulative_savings,
                    'net_25y_profit': cumulative_savings - solar_cost_after_itc
                }

                analysis_results['scenarios'].append(scenario)
        
        except Exception as e:
            print(f"Error in scenario calculation: {e}")
            continue

    # Determine which scenario is selected and update form_params
    if selected_solar_kw is not None and selected_battery_kwh is not None:
        for idx, scenario in enumerate(analysis_results['scenarios']):
            if (abs(scenario['solar_kw'] - selected_solar_kw) < 0.01 and
                abs(scenario['battery_kwh'] - selected_battery_kwh) < 0.01):
                analysis_results['form_params']['selected_scenario_index'] = idx
                break

    return render_template('advanced_budget_analysis.html', **analysis_results)
@app.route('/size', methods=['POST'])
def size_estimate():
    """
    Quick sizing based on address and monthly bill (USD).

    Returns:
        Rendered template with system sizing recommendations or redirect to index on error
    """
    address = request.form.get('address', '').strip()
    sector = request.form.get('sector', 'residential').lower()
    if sector not in ('residential', 'commercial', 'industrial'):
        sector = 'residential'

    if not address:
        flash('Please enter a valid address for sizing.', 'error')
        return redirect(url_for('index'))

    try:
        monthly_bill = request.form.get('monthly_bill', '').strip()
        monthly_bill = float(monthly_bill) if monthly_bill else None
    except ValueError:
        monthly_bill = None

    # Fixed installation cost assumption: $2.5/watt = $2500/kW
    cost_per_kw = 2500.0

    if monthly_bill is None or monthly_bill <= 0:
        flash('Please provide a positive monthly electricity bill.', 'error')
        return redirect(url_for('index'))

    # Geocode
    coords = geocode_address(address)
    if not coords:
        flash('Address could not be found. Please verify the address and try again.', 'error')
        return redirect(url_for('index'))

    lat, lon = coords

    # Utility rate
    electricity_rate = 0.30
    utility_meta = None
    try:
        util = utility_rate(lat, lon, sector=sector)
        if util and isinstance(util.get("rate"), (int, float)):
            electricity_rate = float(util["rate"])  # $/kWh
        utility_meta = {"name": util.get("utility_name")} if util else None
    except Exception as utility_err:
        print(f"Utility Rates API error: {utility_err}")

    # Estimate consumption
    monthly_kwh = monthly_bill / electricity_rate if electricity_rate > 0 else None
    annual_kwh = monthly_kwh * 12 if monthly_kwh is not None else None

    # Determine recommended capacity by scaling 1 kW baseline
    recommended_capacity = None
    expected = None
    try:
        base = pvwatts_estimate(lat, lon, system_capacity_kw=1.0)
        ac_monthly_base = (base.get('outputs') or {}).get('ac_monthly') if isinstance(base, dict) else None
        if annual_kwh and ac_monthly_base:
            annual_per_kw = sum(ac_monthly_base)
            if annual_per_kw > 0:
                recommended_capacity = annual_kwh / annual_per_kw
                expected = pvwatts_estimate(lat, lon, system_capacity_kw=recommended_capacity)
    except Exception as e:
        print(f"Sizing PVWatts error: {e}")

    # Economics
    expected_ac_annual = None
    if expected and isinstance(expected.get('outputs'), dict):
        expected_ac_annual = expected['outputs'].get('ac_annual')

    annual_offset_kwh = None
    if expected_ac_annual and annual_kwh:
        annual_offset_kwh = min(expected_ac_annual, annual_kwh)

    annual_savings_usd = None
    if electricity_rate and annual_offset_kwh is not None:
        annual_savings_usd = electricity_rate * annual_offset_kwh

    investment_cost_usd = None
    if cost_per_kw and recommended_capacity:
        investment_cost_usd = cost_per_kw * recommended_capacity

    payback_years = None
    roi = None
    if investment_cost_usd and annual_savings_usd and annual_savings_usd > 0:
        payback_years = investment_cost_usd / annual_savings_usd
        roi = annual_savings_usd / investment_cost_usd

    return render_template('sizing.html',
                           address=address,
                           lat=lat,
                           lon=lon,
                           sector=sector,
                           electricity_rate=electricity_rate,
                           utility_meta=utility_meta,
                           monthly_bill=monthly_bill,
                           monthly_kwh=monthly_kwh,
                           annual_kwh=annual_kwh,
                           recommended_capacity=recommended_capacity,
                           expected=expected,
                           cost_per_kw=cost_per_kw,
                           annual_offset_kwh=annual_offset_kwh,
                           annual_savings_usd=annual_savings_usd,
                           investment_cost_usd=investment_cost_usd,
                           payback_years=payback_years,
                           roi=roi)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
