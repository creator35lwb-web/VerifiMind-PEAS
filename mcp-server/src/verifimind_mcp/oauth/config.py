"""Environment-bound OAuth identity and isolation seams (T P0-8, P0-7).

Every issuer / resource / origin / collection-namespace / telemetry label is
derived from ONE allowlisted environment name. A staging service therefore
advertises, challenges, stores, labels, and mails as staging — and a token
minted in one environment is rejected by the other because the audience is
bound into the token record and re-checked at the boundary.

Two independent default-OFF flags (T P0-7):

- ``OAUTH_ISSUANCE_ENABLED`` — gates every credential- and account-mutating
  OAuth/DCR/PAT/ceremony path. While off, metadata stays readable but NO
  write, credential, or email may occur.
- ``REGISTRATION_GATE_ENABLED`` — gates MCP execution enforcement only.

"Dark" now means both are off; neither implies the other.
"""

import os
from dataclasses import dataclass
from typing import Optional

ENV_PRODUCTION = "production"
ENV_STAGING = "staging"
ENV_DEVELOPMENT = "development"
_ALLOWED_ENVIRONMENTS = (ENV_PRODUCTION, ENV_STAGING, ENV_DEVELOPMENT)

_PRODUCTION_ORIGIN = "https://verifimind.ysenseai.org"


class EnvironmentMisconfigured(RuntimeError):
    """The declared environment is not allowlisted, or its origin is missing."""


@dataclass(frozen=True)
class OAuthEnvironment:
    """Resolved identity of THIS deployment."""

    name: str
    origin: str

    @property
    def issuer(self) -> str:
        return self.origin

    @property
    def resource(self) -> str:
        """The MCP protected-resource identifier tokens are audience-bound to."""
        return f"{self.origin}/mcp"

    @property
    def prm_url(self) -> str:
        return f"{self.origin}/.well-known/oauth-protected-resource"

    @property
    def collection_prefix(self) -> str:
        """Firestore namespace. Production keeps the historical bare names so
        no live data migrates; every other environment is isolated."""
        return "" if self.name == ENV_PRODUCTION else f"{self.name}_"

    def collection(self, name: str) -> str:
        return f"{self.collection_prefix}{name}"

    def account_collection(self, name: str) -> str:
        """Namespace for USER-DATA stores (early_adopters / ea_registrations /
        feedback / trinity_history — T S157 Finding 3 made the set complete).

        Only a declared staging environment is prefixed, so production and
        local development keep the historical bare names (no migration, no
        test churn) while a staging service can never read, create, or
        tombstone a production record — the cross-environment write that
        namespacing the OAuth tables alone did not stop.
        """
        return name if self.name != ENV_STAGING else f"{self.name}_{name}"


# The ONE Cloud Run service permitted to assume production identity without an
# explicit declaration. Any other K_SERVICE must declare its environment: a
# staging revision that merely forgot one env var would otherwise silently mint
# production-audience tokens the real production boundary accepts.
PRODUCTION_SERVICE_NAME = "verifimind-mcp-server"


def _declared_environment() -> str:
    declared = os.getenv("VERIFIMIND_ENVIRONMENT", "").strip().lower()
    if declared:
        if declared not in _ALLOWED_ENVIRONMENTS:
            raise EnvironmentMisconfigured(
                f"VERIFIMIND_ENVIRONMENT must be one of {_ALLOWED_ENVIRONMENTS}"
            )
        return declared
    service = os.getenv("K_SERVICE", "").strip()
    if not service:
        return ENV_DEVELOPMENT
    if service != PRODUCTION_SERVICE_NAME:
        raise EnvironmentMisconfigured(
            "VERIFIMIND_ENVIRONMENT must be declared explicitly on any service "
            f"other than {PRODUCTION_SERVICE_NAME!r}"
        )
    return ENV_PRODUCTION


def current_environment() -> OAuthEnvironment:
    name = _declared_environment()
    origin = os.getenv("VERIFIMIND_PUBLIC_ORIGIN", "").strip().rstrip("/")
    if not origin:
        if name == ENV_PRODUCTION:
            origin = _PRODUCTION_ORIGIN
        elif name == ENV_DEVELOPMENT:
            origin = "http://localhost:8080"
        else:
            # Staging MUST declare its own origin: inheriting production's
            # issuer is exactly the isolation failure T P0-8 describes.
            raise EnvironmentMisconfigured(
                "VERIFIMIND_PUBLIC_ORIGIN is required when "
                "VERIFIMIND_ENVIRONMENT=staging"
            )
    if name != ENV_DEVELOPMENT and not origin.startswith("https://"):
        raise EnvironmentMisconfigured("public origin must be https outside development")
    return OAuthEnvironment(name=name, origin=origin)


def issuance_enabled() -> bool:
    """Credential/account mutation gate — default OFF (T P0-7)."""
    return os.getenv("OAUTH_ISSUANCE_ENABLED", "false").strip().lower() in {
        "1", "true", "yes", "on",
    }


def mail_recipient_allowed(email: str) -> bool:
    """Staging/dev mail containment: an allowlist may bound recipients so a
    non-production service can never mail arbitrary people (T P0-8).
    Empty allowlist = no restriction (production default)."""
    raw = os.getenv("MAIL_RECIPIENT_ALLOWLIST", "").strip()
    if not raw:
        return True
    allowed = {entry.strip().lower() for entry in raw.split(",") if entry.strip()}
    candidate = email.strip().lower()
    if candidate in allowed:
        return True
    domain = candidate.rpartition("@")[2]
    return bool(domain) and f"@{domain}" in allowed


def subject_hmac_key() -> Optional[str]:
    key = os.getenv("VALUE_SUBJECT_HMAC_KEY", "").strip()
    return key or None
