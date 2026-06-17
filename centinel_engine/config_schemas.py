"""Pydantic schemas for YAML configuration validation.

Centralises schema definitions for known config files so misconfigurations
are caught at load time instead of producing silent runtime failures.

When ``load_config()`` is invoked with a known file name (e.g. ``proxies.yaml``),
the parsed YAML is validated against the matching schema. Unknown files
pass through unvalidated to preserve backward compatibility.

Why this matters for a hostile environment:
    Configuration is a primary attack vector. An attacker who can rewrite
    ``config/prod/proxies.yaml`` could disable proxy rotation, redirect traffic,
    or weaken circuit-breaker thresholds. Strict schema validation forces
    every config change to declare its intent explicitly, surfacing
    suspicious values (e.g. a 0-second timeout) at boot rather than during
    an active election.

ponytail: Phase 4a — consolidated 4 schemas (ProxyConfigSchema, CNEEndpointSchema,
HealingSchema, EndpointsConfigSchema) into 2 (PipelineNetworkConfig,
PipelineEndpointsConfig). SecurityConfig deferred until TLS fingerprints and
Ed25519 signing keys are extracted from their hardcoded locations and managed
as validated config — see electoral_authority_healer._CertPinningAdapter.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator

_LOGGER = logging.getLogger(__name__)


class PipelineNetworkConfig(BaseModel):
    """Validated schema for ``config/<env>/proxies.yaml``.

    Bilingual: Esquema validado para ``config/<env>/proxies.yaml``.
    """

    mode: str = Field(default="direct")
    rotation_strategy: str = Field(default="round_robin")
    rotation_every_n: int = Field(default=1, ge=1)
    proxy_timeout_seconds: float = Field(default=15.0, gt=0.0, le=300.0)
    test_url: str = Field(default="https://httpbin.org/ip")
    proxies: List[str] = Field(default_factory=list)

    @field_validator("mode")
    @classmethod
    def _mode_allowed(cls, value: str) -> str:
        allowed = {"direct", "rotate", "proxy_list"}
        if value not in allowed:
            raise ValueError(f"mode must be one of {sorted(allowed)}, got {value!r}")
        return value

    @field_validator("rotation_strategy")
    @classmethod
    def _strategy_allowed(cls, value: str) -> str:
        allowed = {"round_robin", "random"}
        if value not in allowed:
            raise ValueError(f"rotation_strategy must be one of {sorted(allowed)}, got {value!r}")
        return value

    @field_validator("test_url")
    @classmethod
    def _test_url_https(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("test_url must start with http:// or https://")
        return value


class PipelineEndpointsConfig(BaseModel):
    """Validated schema for ``config/<env>/endpoints.yaml``.

    Bilingual: Esquema validado para ``config/<env>/endpoints.yaml``.

    Inlines the former CNEEndpointSchema (cne.*) and HealingSchema (healing.*)
    as nested sub-models, keeping the same two-level YAML structure.
    """

    class _CNEConfig(BaseModel):
        """CNE endpoint sub-config / Sub-config de endpoints CNE."""

        main_url: str = Field(...)
        presidential_endpoints: List[str] = Field(default_factory=list)
        config_sha256: str = Field(default="")

        @field_validator("main_url")
        @classmethod
        def _main_url_https(cls, value: str) -> str:
            if not value.startswith("https://"):
                raise ValueError(
                    "cne.main_url must use https:// — plain HTTP is a tampering risk"
                )
            return value

    class _HealingConfig(BaseModel):
        """Healing sub-config / Sub-config de healing."""

        interval_minutes: int = Field(default=30, ge=1)
        last_successful_scan: Optional[str] = None
        consecutive_failures: int = Field(default=0, ge=0)
        animal_mode: str = Field(default="normal")
        safe_mode_active: bool = False
        trusted_for_production: bool = False
        last_trusted_scan: Optional[str] = None
        last_untrusted_reason: Optional[str] = None

    cne: _CNEConfig
    healing: _HealingConfig = Field(default_factory=_HealingConfig)


# Backward-compat aliases — callers still using the old names won't break.
# ponytail: remove aliases once all callers import PipelineNetworkConfig /
# PipelineEndpointsConfig directly.
ProxyConfigSchema = PipelineNetworkConfig
EndpointsConfigSchema = PipelineEndpointsConfig

_SCHEMA_REGISTRY: Dict[str, type[BaseModel]] = {
    "proxies.yaml": PipelineNetworkConfig,
    "endpoints.yaml": PipelineEndpointsConfig,
}


def validate_known_config(file_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Validate ``payload`` against the schema registered for ``file_name``.

    Returns the validated payload as a plain dict (so downstream callers
    keep their existing dict-based access patterns). Files without a
    registered schema pass through unchanged.

    Bilingual: Valida ``payload`` contra el esquema registrado para ``file_name``.
    Retorna dict plano para compatibilidad con código existente.

    Raises:
        ValueError: When validation fails, with a detailed message
            identifying the offending field and constraint.
    """
    schema_cls = _SCHEMA_REGISTRY.get(file_name)
    if schema_cls is None:
        return payload
    try:
        validated = schema_cls.model_validate(payload)
    except ValidationError as exc:
        _LOGGER.error("config_schema_validation_failed file=%s errors=%s", file_name, exc.errors())
        raise ValueError(
            f"Config schema validation failed for {file_name}: {exc.errors()}"
        ) from exc
    return validated.model_dump(mode="json")
