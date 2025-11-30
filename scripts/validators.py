# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Project Contributors

"""
Input validation and sanitization utilities
Ensures data integrity and security across the application
"""

import re
from typing import Optional, Tuple, Union


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_address(address: str) -> str:
    """
    Validate and sanitize address input

    Args:
        address (str): User-provided address

    Returns:
        str: Sanitized address

    Raises:
        ValidationError: If address is invalid
    """
    if not address or not isinstance(address, str):
        raise ValidationError("Address must be a non-empty string")

    # Remove excessive whitespace
    address = ' '.join(address.split())

    # Check length
    if len(address) < 5:
        raise ValidationError("Address is too short (minimum 5 characters)")

    if len(address) > 200:
        raise ValidationError("Address is too long (maximum 200 characters)")

    # Remove potentially dangerous characters but keep common address characters
    # Allow: alphanumeric, spaces, commas, periods, hyphens, apostrophes, #
    sanitized = re.sub(r'[^a-zA-Z0-9\s,.\-\'#]', '', address)

    if not sanitized:
        raise ValidationError("Address contains no valid characters")

    return sanitized


def validate_system_capacity(capacity: Union[str, float, int]) -> float:
    """
    Validate solar system capacity

    Args:
        capacity: System capacity in kW

    Returns:
        float: Validated capacity

    Raises:
        ValidationError: If capacity is invalid
    """
    try:
        capacity = float(capacity)
    except (ValueError, TypeError):
        raise ValidationError("System capacity must be a valid number")

    if capacity <= 0:
        raise ValidationError("System capacity must be positive")

    if capacity < 0.1:
        raise ValidationError("System capacity too small (minimum 0.1 kW)")

    if capacity > 1000:
        raise ValidationError("System capacity too large (maximum 1000 kW)")

    return round(capacity, 2)


def validate_sector(sector: str) -> str:
    """
    Validate sector/rate class

    Args:
        sector (str): Sector type

    Returns:
        str: Validated sector

    Raises:
        ValidationError: If sector is invalid
    """
    if not sector or not isinstance(sector, str):
        raise ValidationError("Sector must be a non-empty string")

    sector = sector.lower().strip()

    valid_sectors = ['residential', 'commercial', 'industrial']
    if sector not in valid_sectors:
        raise ValidationError(f"Sector must be one of: {', '.join(valid_sectors)}")

    return sector


def validate_monthly_bill(bill: Union[str, float, int]) -> float:
    """
    Validate monthly electricity bill

    Args:
        bill: Monthly bill in USD

    Returns:
        float: Validated bill amount

    Raises:
        ValidationError: If bill is invalid
    """
    try:
        bill = float(bill)
    except (ValueError, TypeError):
        raise ValidationError("Monthly bill must be a valid number")

    if bill <= 0:
        raise ValidationError("Monthly bill must be positive")

    if bill > 100000:
        raise ValidationError("Monthly bill seems unreasonably high (maximum $100,000)")

    return round(bill, 2)


def validate_percentage(value: Union[str, float, int], name: str = "value",
                       min_val: float = 0, max_val: float = 100) -> float:
    """
    Validate percentage value

    Args:
        value: Percentage value
        name: Name of the parameter (for error messages)
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        float: Validated percentage (0-100)

    Raises:
        ValidationError: If value is invalid
    """
    try:
        value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be a valid number")

    if value < min_val or value > max_val:
        raise ValidationError(f"{name} must be between {min_val} and {max_val}")

    return round(value, 2)


def validate_battery_chemistry(chemistry: str) -> str:
    """
    Validate battery chemistry type

    Args:
        chemistry (str): Battery chemistry code

    Returns:
        str: Validated chemistry code

    Raises:
        ValidationError: If chemistry is invalid
    """
    if not chemistry or not isinstance(chemistry, str):
        raise ValidationError("Battery chemistry must be specified")

    chemistry = chemistry.lower().strip()

    valid_chemistries = ['lfp', 'nmc', 'lto']
    if chemistry not in valid_chemistries:
        raise ValidationError(f"Battery chemistry must be one of: {', '.join(valid_chemistries)}")

    return chemistry


def validate_coordinates(lat: float, lon: float) -> Tuple[float, float]:
    """
    Validate geographic coordinates

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Tuple[float, float]: Validated (latitude, longitude)

    Raises:
        ValidationError: If coordinates are invalid
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        raise ValidationError("Coordinates must be valid numbers")

    if lat < -90 or lat > 90:
        raise ValidationError("Latitude must be between -90 and 90")

    if lon < -180 or lon > 180:
        raise ValidationError("Longitude must be between -180 and 180")

    return round(lat, 6), round(lon, 6)


def validate_budget_level(level: str) -> str:
    """
    Validate budget level

    Args:
        level (str): Budget level identifier

    Returns:
        str: Validated budget level

    Raises:
        ValidationError: If level is invalid
    """
    if not level or not isinstance(level, str):
        raise ValidationError("Budget level must be specified")

    level = level.lower().strip()

    valid_levels = ['small', 'medium', 'large', 'enterprise', 'custom']
    if level not in valid_levels:
        raise ValidationError(f"Budget level must be one of: {', '.join(valid_levels)}")

    return level


def sanitize_html(text: str) -> str:
    """
    Remove HTML tags and potentially dangerous characters from text

    Args:
        text (str): Input text

    Returns:
        str: Sanitized text
    """
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove script tags and content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # Remove potentially dangerous characters
    text = text.replace('<', '&lt;').replace('>', '&gt;')

    return text.strip()


def validate_api_key(api_key: Optional[str]) -> str:
    """
    Validate API key format

    Args:
        api_key: API key string

    Returns:
        str: Validated API key

    Raises:
        ValidationError: If API key is invalid
    """
    if not api_key or not isinstance(api_key, str):
        raise ValidationError("API key is required and must be a string")

    # Basic format validation (alphanumeric and hyphens, reasonable length)
    if not re.match(r'^[a-zA-Z0-9\-_]{10,100}$', api_key):
        raise ValidationError("API key format is invalid")

    return api_key.strip()


def validate_positive_number(value: Union[str, float, int], name: str = "value",
                            max_value: Optional[float] = None) -> float:
    """
    Validate that a value is a positive number

    Args:
        value: Value to validate
        name: Parameter name for error messages
        max_value: Optional maximum value

    Returns:
        float: Validated number

    Raises:
        ValidationError: If value is invalid
    """
    try:
        value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be a valid number")

    if value <= 0:
        raise ValidationError(f"{name} must be positive")

    if max_value is not None and value > max_value:
        raise ValidationError(f"{name} must not exceed {max_value}")

    return value
