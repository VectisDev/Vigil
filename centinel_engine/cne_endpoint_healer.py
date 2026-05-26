"""Backward-compatibility shim — imports from electoral_authority_healer.

New code should import directly from centinel_engine.electoral_authority_healer.
"""

from centinel_engine.electoral_authority_healer import (  # noqa: F401
    CNEEndpointHealer,
    ElectoralAuthorityHealer,
    run_endpoint_healer,
    run_endpoint_healer_for_env,
    EXPECTED_DEPARTMENTS,
    DEPARTMENT_CODE_MAP,
)
