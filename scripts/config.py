# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Project Contributors

"""
Configuration settings for MEWEnergy Solar PV + Battery Platform
Centralizes all magic numbers and configurable parameters
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv()  # fallback to cwd


# ===== APPLICATION SETTINGS =====
class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set. "
                        "Copy .env.example to .env and set a secure secret key.")

    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = False


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SECRET_KEY = 'test-secret-key-for-testing-only'


# ===== API CONFIGURATION =====
class APIConfig:
    """API endpoints and keys"""
    NREL_API_KEY = os.getenv('NREL_API_KEY')
    NREL_BASE_URL = "https://developer.nrel.gov/api"

    # OSM Nominatim
    NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
    NOMINATIM_USER_AGENT = "MEWEnergy/1.0 (contact: support@mewenergy.local)"
    NOMINATIM_RATE_LIMIT_DELAY = 1.0  # seconds

    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_STORAGE_URL = "memory://"


# ===== SOLAR SYSTEM COSTS (USD) =====
class SolarCosts:
    """Solar PV system costs"""
    # Installation costs per kW (DC nameplate capacity)
    RESIDENTIAL_COST_PER_KW = 2500.0  # $/kW
    COMMERCIAL_COST_PER_KW = 2200.0   # $/kW
    INDUSTRIAL_COST_PER_KW = 2000.0   # $/kW

    # Default system sizes (kW)
    DEFAULT_SYSTEM_SIZE = 5.0
    MIN_SYSTEM_SIZE = 0.1
    MAX_SYSTEM_SIZE = 1000.0

    # PVWatts defaults
    DEFAULT_MODULE_TYPE = 0  # 0=Standard, 1=Premium, 2=Thin film
    DEFAULT_ARRAY_TYPE = 0   # 0=Fixed open rack, 1=Fixed roof mount, etc.
    DEFAULT_LOSSES = 14      # System losses in percent
    DEFAULT_AZIMUTH = 180    # South-facing
    # Tilt defaults to latitude (set dynamically)


# ===== BATTERY COSTS (USD) =====
class BatteryCosts:
    """Battery energy storage system costs"""
    # Cost per kWh by chemistry type
    LFP_COST_PER_KWH = 450    # Lithium Iron Phosphate
    NMC_COST_PER_KWH = 550    # Nickel Manganese Cobalt
    LTO_COST_PER_KWH = 800    # Lithium Titanate

    # Battery performance parameters
    DEFAULT_DOD = 0.90                    # Depth of discharge (90%)
    DEFAULT_ROUND_TRIP_EFFICIENCY = 0.92  # Round-trip efficiency (92%)
    DEFAULT_BACKUP_RESERVE = 0.20         # Backup reserve (20%)
    DEFAULT_BATTERY_POWER = 5.0           # Power rating in kW

    # Battery lifecycle
    CYCLES_PER_YEAR = 250
    DEGRADATION_RATE = 0.02  # 2% per year
    REPLACEMENT_YEAR = 10
    REPLACEMENT_COST_FACTOR = 0.5  # 50% of original cost


# ===== FINANCIAL PARAMETERS =====
class FinancialConfig:
    """Financial analysis parameters"""
    # Federal incentives
    ITC_RATE = 0.30  # Investment Tax Credit (30% for 2022-2032)

    # Analysis timeframe
    ANALYSIS_PERIOD_YEARS = 25

    # Escalation rates
    ELECTRICITY_RATE_ESCALATION = 0.03  # 3% per year
    SREC_PRICE_ESCALATION = 0.02        # 2% per year

    # Degradation rates
    SOLAR_DEGRADATION_RATE = 0.005  # 0.5% per year

    # Default rates
    DEFAULT_ELECTRICITY_RATE = 0.30  # $/kWh
    DEFAULT_DISCOUNT_RATE = 0.05     # 5%

    # TOU (Time of Use) multipliers
    TOU_PEAK_MULTIPLIER = 1.5     # Peak rate = 1.5x standard
    TOU_OFF_PEAK_MULTIPLIER = 0.5  # Off-peak rate = 0.5x standard


# ===== SREC PRICES (USD per MWh) =====
class SRECPrices:
    """State-specific SREC prices
    Source: Conservative estimates based on market data
    Update these with live prices from SRECTrade or GATS API
    """
    PRICES = {
        "New Jersey": 220.0,
        "Massachusetts": 280.0,
        "Pennsylvania": 45.0,
        "District of Columbia": 420.0,
        "Maryland": 60.0,
        "Illinois": 70.0,
        "Ohio": 15.0,
        "Virginia": 35.0
    }
    DEFAULT_PRICE = 0.0


# ===== BUDGET RANGES (USD) =====
class BudgetRanges:
    """Investment budget categories"""
    RANGES = {
        'small': {'min': 10000, 'max': 20000, 'name': 'Entry Level'},
        'medium': {'min': 20000, 'max': 40000, 'name': 'Standard'},
        'large': {'min': 40000, 'max': 80000, 'name': 'Premium'},
        'enterprise': {'min': 80000, 'max': 150000, 'name': 'Enterprise'}
    }


# ===== UTILITY FUNCTIONS =====
def get_battery_cost(chemistry='lfp'):
    """Get battery cost per kWh by chemistry type"""
    costs = {
        'lfp': BatteryCosts.LFP_COST_PER_KWH,
        'nmc': BatteryCosts.NMC_COST_PER_KWH,
        'lto': BatteryCosts.LTO_COST_PER_KWH
    }
    return costs.get(chemistry, BatteryCosts.LFP_COST_PER_KWH)


def get_solar_cost(sector='residential'):
    """Get solar installation cost per kW by sector"""
    costs = {
        'residential': SolarCosts.RESIDENTIAL_COST_PER_KW,
        'commercial': SolarCosts.COMMERCIAL_COST_PER_KW,
        'industrial': SolarCosts.INDUSTRIAL_COST_PER_KW
    }
    return costs.get(sector, SolarCosts.RESIDENTIAL_COST_PER_KW)


def get_budget_range(budget_level='medium'):
    """Get budget range by level"""
    return BudgetRanges.RANGES.get(budget_level, BudgetRanges.RANGES['medium'])


def get_srec_price(state_name):
    """Get SREC price for given state"""
    return SRECPrices.PRICES.get(state_name, SRECPrices.DEFAULT_PRICE)


# Export config based on environment
_env = os.getenv('FLASK_ENV', 'production')
if _env == 'development':
    app_config = DevelopmentConfig
elif _env == 'testing':
    app_config = TestingConfig
else:
    app_config = ProductionConfig
