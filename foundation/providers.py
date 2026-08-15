"""P3 provider boundary for insurance quotation integrations.

No insurer credentials are stored here. Providers are adapters behind one
stable contract so the CRM is independent of any insurer/PBPartners API.
"""

import os
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class ProviderQuoteResult:
    provider: str
    status: str
    quote_reference: str | None = None
    premium: int | None = None
    currency: str = "INR"
    checkout_url: str | None = None
    raw: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None

    def as_dict(self):
        return asdict(self)


class ProviderAdapter:
    name = "base"

    def quote(self, payload: dict[str, Any]) -> ProviderQuoteResult:
        raise NotImplementedError


class ConfiguredLinkProvider(ProviderAdapter):
    """Safe provider placeholder for environments without an approved API.

    It never pretends a quote was generated. It returns a controlled
    'not_configured' result and optionally exposes a public/partner URL.
    """

    env_url = ""

    def quote(self, payload):
        url = os.getenv(self.env_url) if self.env_url else None
        return ProviderQuoteResult(
            provider=self.name,
            status="not_configured",
            checkout_url=url,
            raw={"message": "Provider API credentials/configuration are not configured."},
            error_code="PROVIDER_NOT_CONFIGURED",
            error_message="Live provider quotation is not enabled in this environment.",
        )


class PBPartnersProvider(ConfiguredLinkProvider):
    name = "pbpartners"
    env_url = "PBPARTNERS_QUOTE_URL"


class InsurerProvider(ConfiguredLinkProvider):
    def __init__(self, name: str, env_url: str):
        self.name = name
        self.env_url = env_url


PROVIDERS = {
    "pbpartners": PBPartnersProvider(),
    "tata_aig": InsurerProvider("tata_aig", "TATA_AIG_QUOTE_URL"),
    "chola": InsurerProvider("chola", "CHOLA_QUOTE_URL"),
    "bajaj_allianz": InsurerProvider("bajaj_allianz", "BAJAJ_ALLIANZ_QUOTE_URL"),
    "hdfc_ergo": InsurerProvider("hdfc_ergo", "HDFC_ERGO_QUOTE_URL"),
    "icici_lombard": InsurerProvider("icici_lombard", "ICICI_LOMBARD_QUOTE_URL"),
}


def provider(name: str | None):
    key = (name or "pbpartners").strip().lower()
    return PROVIDERS.get(key)


def available_providers():
    return sorted(PROVIDERS.keys())
