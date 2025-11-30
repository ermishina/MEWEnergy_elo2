# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Project Contributors

"""
MEWEnergy Solar PV + Battery Platform - Improved Version
Enhanced with:
- Proper error logging
- Input validation and sanitization
- Rate limiting
- Security hardening
- Modularized code
"""

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

from api import geocode_address, solar_resource_data, pvwatts_estimate, utility_rate
from config import (app_config, get_solar_cost, get_srec_price, get_battery_cost,
                    get_budget_range, BudgetRanges, APIConfig, FinancialConfig)
from logger import setup_logger, log_api_call, log_route_access
from validators import (
    validate_address, validate_system_capacity, validate_sector,
    validate_monthly_bill, ValidationError
)
from analysis_helpers import (
    generate_load_profile, calculate_battery_metrics,
    calculate_financial_metrics, calculate_25year_projection,
    parse_advanced_budget_form
)

import os

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(app_config)

# Setup CORS (configure as needed for production)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Setup rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=APIConfig.RATELIMIT_STORAGE_URL
)

# Setup logger
logger = setup_logger('mewenergy')


# --- SREC helpers ---
def reverse_geocode_state(lat, lon):
    """Return U.S. state name for given coordinates using Nominatim reverse geocoding."""
    import requests
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {"lat": lat, "lon": lon, "format": "json", "zoom": 5, "addressdetails": 1}
    headers = {"User-Agent": APIConfig.NOMINATIM_USER_AGENT}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        js = resp.json()
        state = (js.get("address") or {}).get("state")
        logger.debug(f"Reverse geocoded ({lat}, {lon}) to state: {state}")
        return state
    except Exception as e:
        logger.error(f"Reverse geocoding failed: {e}")
        return None


@app.route('/')
@limiter.limit("30 per minute")
def index():
    """Main page with address input form"""
    log_route_access(logger, '/', 'GET', request.remote_addr)
    return render_template('index.html')


@app.route('/search', methods=['POST'])
@limiter.limit("20 per minute")
def search_address():
    """Handle address search and display solar data"""
    log_route_access(logger, '/search', 'POST', request.remote_addr)

    try:
        # Validate inputs
        address = validate_address(request.form.get('address', ''))
        system_capacity = validate_system_capacity(request.form.get('system_capacity', 5.0))
        sector = validate_sector(request.form.get('sector', 'residential'))

    except ValidationError as e:
        logger.warning(f"Validation error in /search: {e}")
        flash(str(e), 'error')
        return redirect(url_for('index'))

    # Geocode the address
    try:
        coords = geocode_address(address)
        if not coords:
            flash('Address could not be found. Please verify the address and try again.', 'error')
            return redirect(url_for('index'))

        lat, lon = coords
        logger.info(f"Geocoded address '{address}' to ({lat}, {lon})")

    except Exception as e:
        logger.error(f"Geocoding failed for address '{address}': {e}")
        flash('Error processing address. Please try again.', 'error')
        return redirect(url_for('index'))

    try:
        # Get solar resource data
        solar_data = solar_resource_data(lat, lon)
        log_api_call(logger, 'solar_resource_data', {'lat': lat, 'lon': lon}, success=True)

        # Get PVWatts estimate
        pvwatts_data = None
        try:
            pvwatts_data = pvwatts_estimate(lat, lon, system_capacity_kw=system_capacity)
            log_api_call(logger, 'pvwatts_estimate', {'lat': lat, 'lon': lon, 'capacity': system_capacity}, success=True)
        except Exception as pvwatts_error:
            logger.error(f"PVWatts API error: {pvwatts_error}")
            log_api_call(logger, 'pvwatts_estimate', {'lat': lat, 'lon': lon}, success=False, error=pvwatts_error)

        # Fetch local electricity rate
        electricity_rate = 0.30  # default fallback
        utility_meta = None
        try:
            util = utility_rate(lat, lon, sector=sector)
            if util and isinstance(util.get("rate"), (int, float)):
                electricity_rate = float(util["rate"])
            utility_meta = {"name": util.get("utility_name")} if util else None
            log_api_call(logger, 'utility_rate', {'lat': lat, 'lon': lon, 'sector': sector}, success=True)
        except Exception as utility_err:
            logger.error(f"Utility Rates API error: {utility_err}")
            log_api_call(logger, 'utility_rate', {'lat': lat, 'lon': lon}, success=False, error=utility_err)

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
        logger.error(f"Error in /search: {e}", exc_info=True)
        flash(f'Error retrieving solar data. Please try again later.', 'error')
        return redirect(url_for('index'))


@app.route('/api/search', methods=['POST'])
@limiter.limit("10 per minute")
def api_search():
    """API endpoint for address search"""
    log_route_access(logger, '/api/search', 'POST', request.remote_addr)

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    try:
        # Validate inputs
        address = validate_address(data.get('address', ''))
        system_capacity = validate_system_capacity(data.get('system_capacity', 5.0))
        sector = validate_sector(data.get('sector', 'residential'))

    except ValidationError as e:
        logger.warning(f"Validation error in /api/search: {e}")
        return jsonify({'error': str(e)}), 400

    # Geocode
    try:
        coords = geocode_address(address)
        if not coords:
            return jsonify({'error': 'Address not found'}), 404

        lat, lon = coords

        # Get all data
        solar_data = solar_resource_data(lat, lon)
        pvwatts_data = pvwatts_estimate(lat, lon, system_capacity_kw=system_capacity)

        electricity_rate = 0.30
        utility_meta = None
        try:
            util = utility_rate(lat, lon, sector=sector)
            if util and isinstance(util.get("rate"), (int, float)):
                electricity_rate = float(util["rate"])
            utility_meta = {"name": util.get("utility_name")} if util else None
        except Exception:
            pass

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
        logger.error(f"Error in /api/search: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/advanced-budget-analysis', methods=['POST'])
@limiter.limit("10 per minute")
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
    log_route_access(logger, '/advanced-budget-analysis', 'POST', request.remote_addr)

    try:
        # Parse and validate form data
        params = parse_advanced_budget_form(request.form)

        # Validate address
        address = validate_address(params['address'])
        sector = validate_sector(params['sector'])
        monthly_bill = validate_monthly_bill(params['monthly_bill'])

    except ValidationError as e:
        logger.warning(f"Validation error in /advanced-budget-analysis: {e}")
        flash(str(e), 'error')
        return redirect(url_for('index'))

    # Geocoding
    try:
        coords = geocode_address(address)
        if not coords:
            flash('Unable to geocode address. Please verify and retry.', 'error')
            return redirect(url_for('index'))

        lat, lon = coords
        logger.info(f"Geocoded '{address}' to ({lat}, {lon})")

    except Exception as e:
        logger.error(f"Geocoding failed: {e}")
        flash('Error processing address. Please try again.', 'error')
        return redirect(url_for('index'))

    # Get state for SREC pricing
    state_name = reverse_geocode_state(lat, lon)
    srec_price = get_srec_price(state_name) if params['include_srec'] else 0.0

    # Get utility rate
    electricity_rate = FinancialConfig.DEFAULT_ELECTRICITY_RATE
    try:
        util = utility_rate(lat, lon, sector=sector)
        if util and isinstance(util.get("rate"), (int, float)):
            electricity_rate = float(util["rate"])
        log_api_call(logger, 'utility_rate', {'lat': lat, 'lon': lon}, success=True)
    except Exception as e:
        logger.error(f"Utility API error: {e}")
        log_api_call(logger, 'utility_rate', {'lat': lat, 'lon': lon}, success=False, error=e)

    # Calculate baseline consumption
    monthly_kwh = monthly_bill / electricity_rate
    annual_kwh = monthly_kwh * 12
    daily_kwh = monthly_kwh / 30
    hourly_avg_kw = daily_kwh / 24

    # Generate hourly load profile
    hourly_load_profile = generate_load_profile(hourly_avg_kw, sector)

    # Budget configuration
    if params['budget_level'] == 'custom':
        budget_range = {
            'min': float(request.form.get('custom_min', 20000)),
            'max': float(request.form.get('custom_max', 40000)),
            'name': 'Custom'
        }
    else:
        budget_range = get_budget_range(params['budget_level'])

    # Get costs
    solar_cost_per_kw = get_solar_cost(sector)
    battery_cost_per_kwh = get_battery_cost(params['battery_chemistry'])

    # Calculate solar system sizes
    min_solar_kw = (budget_range['min'] * 0.7) / solar_cost_per_kw
    max_solar_kw = (budget_range['max'] * 0.7) / solar_cost_per_kw
    optimal_solar_kw = (min_solar_kw + max_solar_kw) / 2

    # TOU rates
    peak_rate = electricity_rate * FinancialConfig.TOU_PEAK_MULTIPLIER if params['time_of_use'] else electricity_rate
    off_peak_rate = electricity_rate * FinancialConfig.TOU_OFF_PEAK_MULTIPLIER if params['time_of_use'] else electricity_rate

    # Analysis results structure
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
            'hourly_profile': hourly_load_profile
        },
        'rates': {
            'standard': electricity_rate,
            'peak': peak_rate if params['time_of_use'] else None,
            'off_peak': off_peak_rate if params['time_of_use'] else None
        },
        'form_params': {
            'address': address,
            'sector': sector,
            'budget': params['budget_level'],
            'monthly_bill': monthly_bill,
            'discount_rate': params['discount_rate'] * 100,
            'include_battery': params['include_battery'],
            'battery_chemistry': params['battery_chemistry'],
            'battery_sizes': params['battery_sizes'],
            'battery_power': params['battery_power'],
            'dod': params['dod'] * 100,
            'round_trip_efficiency': params['round_trip_eff'] * 100,
            'backup_reserve': params['backup_reserve'] * 100,
            'include_itc': params['include_itc'],
            'include_srec': params['include_srec'],
            'time_of_use': params['time_of_use'],
            'net_metering': params['net_metering'],
            'selected_solar_kw': params['selected_solar_kw'],
            'selected_battery_kwh': params['selected_battery_kwh'],
            'selected_scenario_index': -1
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

            # Solar cost
            solar_cost = solar_capacity * solar_cost_per_kw

            scenario_base = {
                'solar_kw': solar_capacity,
                'annual_production': ac_annual,
                'monthly_production': ac_monthly,
                'self_consumption_rate': min(1.0, ac_annual / annual_kwh),
                'solar_cost': solar_cost,
                'solar_cost_after_itc': solar_cost * (1 - (FinancialConfig.ITC_RATE if params['include_itc'] else 0))
            }

            # Add battery configurations if selected
            if params['include_battery'] and params['battery_sizes']:
                for battery_kwh_str in params['battery_sizes']:
                    battery_kwh = float(battery_kwh_str)

                    # Calculate battery metrics
                    battery_metrics = calculate_battery_metrics(
                        battery_kwh, params['dod'], params['round_trip_eff'],
                        hourly_avg_kw, daily_kwh, ac_annual
                    )

                    battery_cost = battery_kwh * battery_cost_per_kwh

                    # Calculate financial metrics
                    financial_metrics = calculate_financial_metrics(
                        solar_cost, battery_cost, ac_annual, electricity_rate,
                        monthly_bill, FinancialConfig.ITC_RATE if params['include_itc'] else 0,
                        srec_price * (ac_annual / 1000), battery_metrics['effective_kwh'],
                        params['time_of_use'], peak_rate, off_peak_rate
                    )

                    # Calculate 25-year projection
                    projection = calculate_25year_projection(
                        ac_annual, battery_metrics['effective_kwh'],
                        financial_metrics['total_cost_after_itc'],
                        electricity_rate, srec_price * (ac_annual / 1000),
                        params['include_battery'], battery_cost, params['discount_rate']
                    )

                    # Create scenario
                    scenario = {
                        **scenario_base,
                        'battery_kwh': battery_kwh,
                        'battery_chemistry': params['battery_chemistry'],
                        'battery_cost': battery_cost,
                        'usable_capacity': battery_metrics['usable_kwh'],
                        'effective_capacity': battery_metrics['effective_kwh'],
                        'backup_hours': battery_metrics['backup_hours'],
                        'evening_coverage_percent': battery_metrics['evening_coverage'] * 100,
                        'daily_charge_potential': battery_metrics['daily_charge_potential'],
                        'total_system_cost': financial_metrics['total_cost'],
                        'total_cost_after_incentives': financial_metrics['total_cost_after_itc'],
                        'annual_savings': financial_metrics['total_annual_savings'],
                        'arbitrage_savings': financial_metrics['arbitrage_savings'],
                        'srec_revenue': srec_price * (ac_annual / 1000) if params['include_srec'] else 0,
                        'srec_price_usd_per_mwh': srec_price,
                        'srec_state': state_name,
                        'simple_payback_years': financial_metrics['simple_payback'],
                        'npv': projection['npv'],
                        'irr': projection['irr'],
                        'lcoe': projection['lcoe'],
                        'cumulative_25y_savings': projection['cumulative_25y_savings'],
                        'net_25y_profit': projection['net_25y_profit']
                    }

                    analysis_results['scenarios'].append(scenario)

            else:
                # Solar-only scenario
                solar_cost_after_itc = solar_cost * (1 - (FinancialConfig.ITC_RATE if params['include_itc'] else 0))
                solar_savings = min(ac_annual * electricity_rate, monthly_bill * 12)

                srec_revenue = srec_price * (ac_annual / 1000) if params['include_srec'] else 0

                projection = calculate_25year_projection(
                    ac_annual, 0, solar_cost_after_itc,
                    electricity_rate, srec_revenue,
                    False, 0, params['discount_rate']
                )

                scenario = {
                    **scenario_base,
                    'battery_kwh': 0,
                    'total_system_cost': solar_cost,
                    'total_cost_after_incentives': solar_cost_after_itc,
                    'annual_savings': solar_savings + srec_revenue,
                    'srec_revenue': srec_revenue,
                    'srec_price_usd_per_mwh': srec_price,
                    'srec_state': state_name,
                    'simple_payback_years': solar_cost_after_itc / (solar_savings + srec_revenue) if (solar_savings + srec_revenue) > 0 else 999,
                    'npv': projection['npv'],
                    'irr': projection['irr'],
                    'lcoe': projection['lcoe'],
                    'cumulative_25y_savings': projection['cumulative_25y_savings'],
                    'net_25y_profit': projection['net_25y_profit']
                }

                analysis_results['scenarios'].append(scenario)

            log_api_call(logger, 'pvwatts_estimate', {'lat': lat, 'lon': lon, 'capacity': solar_capacity}, success=True)

        except Exception as e:
            logger.error(f"Error in scenario calculation: {e}", exc_info=True)
            log_api_call(logger, 'pvwatts_estimate', {'lat': lat, 'lon': lon}, success=False, error=e)
            continue

    # Determine selected scenario
    if params['selected_solar_kw'] is not None and params['selected_battery_kwh'] is not None:
        for idx, scenario in enumerate(analysis_results['scenarios']):
            if (abs(scenario['solar_kw'] - params['selected_solar_kw']) < 0.01 and
                abs(scenario['battery_kwh'] - params['selected_battery_kwh']) < 0.01):
                analysis_results['form_params']['selected_scenario_index'] = idx
                break

    logger.info(f"Advanced analysis complete: {len(analysis_results['scenarios'])} scenarios generated")

    return render_template('advanced_budget_analysis.html', **analysis_results)


@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded"""
    logger.warning(f"Rate limit exceeded from {request.remote_addr}")
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429


@app.errorhandler(500)
def internal_error_handler(e):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {e}", exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(404)
def not_found_handler(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found'}), 404


if __name__ == '__main__':
    logger.info("Starting MEWEnergy Flask application...")
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
    logger.info(f"Debug mode: {app.config['DEBUG']}")

    app.run(
        debug=app.config['DEBUG'],
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000))
    )
