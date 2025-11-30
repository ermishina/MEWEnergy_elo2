# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Project Contributors

"""
Swagger/OpenAPI specification for MEWEnergy API
Provides API documentation accessible at /api/docs
"""

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "MEWEnergy Solar PV + Battery API",
        "description": "REST API for solar PV system sizing and financial analysis",
        "version": "1.0.0",
        "contact": {
            "name": "MEWEnergy Team",
            "email": "support@mewenergy.local"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    },
    "host": "localhost:5000",  # Update for production
    "basePath": "/api",
    "schemes": ["http", "https"],
    "consumes": ["application/json"],
    "produces": ["application/json"],
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs/"
}

# API endpoint specifications
api_specs = {
    "/api/search": {
        "post": {
            "tags": ["Solar Analysis"],
            "summary": "Analyze solar potential for an address",
            "description": "Geocode an address and retrieve solar resource data, PVWatts estimates, and utility rates",
            "parameters": [
                {
                    "in": "body",
                    "name": "body",
                    "description": "Address and system parameters",
                    "required": True,
                    "schema": {
                        "type": "object",
                        "required": ["address"],
                        "properties": {
                            "address": {
                                "type": "string",
                                "example": "77 Massachusetts Avenue, Cambridge, MA 02139",
                                "description": "Full installation address"
                            },
                            "system_capacity": {
                                "type": "number",
                                "example": 5.0,
                                "description": "Solar system capacity in kW (DC)",
                                "default": 5.0,
                                "minimum": 0.1,
                                "maximum": 1000.0
                            },
                            "sector": {
                                "type": "string",
                                "enum": ["residential", "commercial", "industrial"],
                                "example": "residential",
                                "description": "Utility rate schedule classification",
                                "default": "residential"
                            }
                        }
                    }
                }
            ],
            "responses": {
                "200": {
                    "description": "Successful analysis",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "address": {"type": "string"},
                            "coordinates": {
                                "type": "object",
                                "properties": {
                                    "lat": {"type": "number"},
                                    "lon": {"type": "number"}
                                }
                            },
                            "solar_data": {
                                "type": "object",
                                "description": "NREL Solar Resource Data"
                            },
                            "pvwatts_data": {
                                "type": "object",
                                "description": "NREL PVWatts production estimates"
                            },
                            "electricity_rate": {
                                "type": "number",
                                "description": "Utility electricity rate in $/kWh"
                            },
                            "utility": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"}
                                }
                            },
                            "sector": {"type": "string"}
                        }
                    }
                },
                "400": {
                    "description": "Invalid input",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"}
                        }
                    }
                },
                "404": {
                    "description": "Address not found",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"}
                        }
                    }
                },
                "429": {
                    "description": "Rate limit exceeded",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"}
                        }
                    }
                },
                "500": {
                    "description": "Internal server error",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"}
                        }
                    }
                }
            }
        }
    }
}
