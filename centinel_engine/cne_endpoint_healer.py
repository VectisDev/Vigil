"""Backward-compatibility shim — use electoral_endpoint_scanner.ElectoralEndpointScanner instead."""
from centinel_engine.electoral_endpoint_scanner import (
    ElectoralEndpointScanner as CNEEndpointHealer,
    run_endpoint_healer_for_env,
    run_endpoint_healer,
    ElectoralEndpointScanner,
    EndpointRecord,
    EXPECTED_DEPARTMENTS,
    DEPARTMENT_CODE_MAP,
    PRESIDENTIAL_HINT_KEYS,
    PRESIDENTIAL_HINT_VALUES,
)

__all__ = [
    "CNEEndpointHealer",
    "ElectoralEndpointScanner",
    "run_endpoint_healer_for_env",
    "run_endpoint_healer",
    "EndpointRecord",
    "EXPECTED_DEPARTMENTS",
    "DEPARTMENT_CODE_MAP",
    "PRESIDENTIAL_HINT_KEYS",
    "PRESIDENTIAL_HINT_VALUES",
]
