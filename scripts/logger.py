# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Project Contributors

"""
Logging configuration for MEWEnergy Solar PV + Battery Platform
Provides structured logging with different handlers for different environments
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import os


def setup_logger(name='mewenergy', level=None, log_file=None):
    """
    Configure and return a logger instance

    Args:
        name (str): Logger name
        level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (str): Path to log file (optional)

    Returns:
        logging.Logger: Configured logger instance
    """
    # Determine log level
    if level is None:
        level = os.getenv('LOG_LEVEL', 'INFO').upper()

    log_level = getattr(logging, level, logging.INFO)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # File handler (if log_file specified or in production)
    if log_file or os.getenv('FLASK_ENV') == 'production':
        if log_file is None:
            log_dir = Path(__file__).parent / 'logs'
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / 'mewenergy.log'

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    # Error file handler (always log errors to separate file in production)
    if os.getenv('FLASK_ENV') == 'production':
        log_dir = Path(__file__).parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        error_file = log_dir / 'errors.log'

        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)

    return logger


def log_api_call(logger, api_name, params, success=True, error=None):
    """
    Log API calls with standardized format

    Args:
        logger: Logger instance
        api_name (str): Name of the API
        params (dict): API parameters
        success (bool): Whether the call succeeded
        error (Exception): Error object if call failed
    """
    if success:
        logger.info(f"API call successful: {api_name}", extra={
            'api': api_name,
            'params': params,
            'status': 'success'
        })
    else:
        logger.error(f"API call failed: {api_name}", extra={
            'api': api_name,
            'params': params,
            'status': 'failed',
            'error': str(error)
        }, exc_info=error)


def log_route_access(logger, route, method, ip_address, params=None):
    """
    Log route access for monitoring and security

    Args:
        logger: Logger instance
        route (str): Route path
        method (str): HTTP method
        ip_address (str): Client IP address
        params (dict): Request parameters
    """
    logger.info(f"Route accessed: {method} {route}", extra={
        'route': route,
        'method': method,
        'ip': ip_address,
        'params': params
    })


def log_calculation(logger, calculation_type, inputs, outputs, duration=None):
    """
    Log calculations for debugging and validation

    Args:
        logger: Logger instance
        calculation_type (str): Type of calculation
        inputs (dict): Input parameters
        outputs (dict): Calculation results
        duration (float): Execution time in seconds
    """
    extra_data = {
        'calculation': calculation_type,
        'inputs': inputs,
        'outputs': outputs
    }
    if duration is not None:
        extra_data['duration_seconds'] = duration

    logger.debug(f"Calculation completed: {calculation_type}", extra=extra_data)


# Create default logger instance
default_logger = setup_logger()


# Convenience functions using default logger
def debug(msg, *args, **kwargs):
    """Log debug message"""
    default_logger.debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """Log info message"""
    default_logger.info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    """Log warning message"""
    default_logger.warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    """Log error message"""
    default_logger.error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    """Log critical message"""
    default_logger.critical(msg, *args, **kwargs)
