"""Pre-generation validation for deal data.

The goal: catch the mistakes that must never reach a client document — a
missing deposit, a deposit larger than the price, a closing date before the
offer date, an unparseable date — *before* a form is filled or a PDF is sent.

``validate_deal`` is a pure function (stdlib + python-dateutil only) so it can
run in the bot, in the generator, and in unit tests without any browser or API
dependencies.

Two severities:
  * **errors**   — block generation. Unambiguous, objectively-wrong data.
  * **warnings** — surfaced to the user but non-blocking. Things that are
    usually-but-not-always mistakes (e.g. an unusual postal code).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from forms.formatting import normalize_number, parse_date

__all__ = ["ValidationResult", "validate_deal", "REQUIRED_FIELDS", "FIELD_LABELS"]


# Required fields per document type. Missing → blocking error.
REQUIRED_FIELDS: dict[str, list[str]] = {
    "aps": [
        "buyer_1", "seller_1", "purchase_price",
        "property_street_number", "property_street_name", "property_city",
    ],
    "commercial_aps": [
        "buyer_1", "seller_1", "purchase_price",
        "property_street_number", "property_street_name", "property_city",
    ],
    "lease": [
        "buyer_1", "seller_1", "monthly_rent",
        "property_street_number", "property_street_name", "property_city",
    ],
    "amendment": [
        "buyer_1", "seller_1", "original_agreement_date", "amendment_description",
        "property_street_number", "property_street_name", "property_city",
    ],
    "waiver": [
        "buyer_1", "seller_1", "original_agreement_date", "condition_waived",
        "property_street_number", "property_street_name", "property_city",
    ],
    "notice": [
        "buyer_1", "seller_1",
        "property_street_number", "property_street_name", "property_city",
    ],
}

# Human-readable labels for field keys, used in messages.
FIELD_LABELS: dict[str, str] = {
    "buyer_1": "Buyer",
    "seller_1": "Seller",
    "purchase_price": "Purchase price",
    "deposit": "Deposit",
    "property_street_number": "Street number",
    "property_street_name": "Street name",
    "property_city": "City",
    "property_postal_code": "Postal code",
    "offer_date": "Offer date",
    "closing_date": "Closing date",
    "irrevocability_date": "Irrevocability date",
    "original_agreement_date": "Original agreement date",
    "amendment_description": "Amendment description",
    "amendment_date": "Amendment date",
    "condition_waived": "Condition being waived",
    "waiver_date": "Waiver date",
    "monthly_rent": "Monthly rent",
    "rent_deposit": "Rent deposit",
    "lease_start_date": "Lease start date",
    "lease_end_date": "Lease end date",
}

# Canadian postal code: A1A 1A1 (space optional). Excludes letters D,F,I,O,Q,U.
_POSTAL_RE = re.compile(
    r"^[ABCEGHJKLMNPRSTVXY]\d[ABCEGHJKLMNPRSTVWXYZ]\s?\d[ABCEGHJKLMNPRSTVWXYZ]\d$",
    re.IGNORECASE,
)


@dataclass
class ValidationResult:
    """Outcome of validating a deal. ``ok`` is True when there are no errors."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def summary(self) -> str:
        """Render a human-readable summary (used by the bot)."""
        lines: list[str] = []
        if self.errors:
            lines.append("❌ Must fix before generating:")
            lines.extend(f"  • {e}" for e in self.errors)
        if self.warnings:
            if lines:
                lines.append("")
            lines.append("⚠️ Please double-check:")
            lines.extend(f"  • {w}" for w in self.warnings)
        if not lines:
            return "✅ All checks passed."
        return "\n".join(lines)


def _label(key: str) -> str:
    return FIELD_LABELS.get(key, key.replace("_", " ").capitalize())


def validate_deal(deal_data: dict, doc_type: str = "aps") -> ValidationResult:
    """Validate collected deal data for a given document type."""
    result = ValidationResult()
    data = deal_data or {}

    _check_required(result, data, doc_type)
    price = _check_price(result, data, doc_type)
    _check_deposit(result, data, price, doc_type)
    _check_dates(result, data)
    _check_lease_terms(result, data, doc_type)
    _check_postal_code(result, data)

    return result


def _check_required(result: ValidationResult, data: dict, doc_type: str) -> None:
    required = REQUIRED_FIELDS.get(doc_type, REQUIRED_FIELDS["aps"])
    for key in required:
        value = data.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            result.add_error(f"{_label(key)} is required but missing.")


def _check_price(result: ValidationResult, data: dict, doc_type: str) -> float:
    """Validate the purchase price. Returns the parsed amount (0.0 if absent)."""
    # Leases and amendments may legitimately have no purchase price.
    price_required = doc_type in ("aps", "commercial_aps")
    raw = data.get("purchase_price")

    if raw is None or (isinstance(raw, str) and not raw.strip()):
        if price_required:
            # Already reported by _check_required; avoid duplicate noise.
            pass
        return 0.0

    price = normalize_number(raw)
    if price <= 0:
        result.add_error(
            f"Purchase price '{raw}' is not a valid positive amount."
        )
    elif price < 1000:
        result.add_warning(
            f"Purchase price (${price:,.2f}) looks unusually low — please confirm."
        )
    return price


def _check_deposit(
    result: ValidationResult, data: dict, price: float, doc_type: str
) -> None:
    raw = data.get("deposit")
    has_deposit = not (raw is None or (isinstance(raw, str) and not raw.strip()))

    if not has_deposit:
        if doc_type in ("aps", "commercial_aps"):
            result.add_warning(
                "No deposit specified — an Agreement of Purchase and Sale "
                "normally requires one."
            )
        return

    deposit = normalize_number(raw)
    if deposit <= 0:
        result.add_error(f"Deposit '{raw}' is not a valid positive amount.")
        return

    if price > 0 and deposit > price:
        result.add_error(
            f"Deposit (${deposit:,.2f}) is greater than the purchase price "
            f"(${price:,.2f})."
        )
    elif price > 0 and deposit < price * 0.01:
        result.add_warning(
            f"Deposit (${deposit:,.2f}) is less than 1% of the purchase price "
            f"— please confirm this is correct."
        )


def _check_dates(result: ValidationResult, data: dict) -> None:
    parsed: dict[str, object] = {}
    for key in (
        "offer_date", "closing_date", "irrevocability_date",
        "original_agreement_date", "amendment_date", "waiver_date",
        "lease_start_date", "lease_end_date",
    ):
        raw = data.get(key)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            continue
        dt = parse_date(raw)
        if dt is None:
            result.add_error(
                f"{_label(key)} '{raw}' is not a recognizable date."
            )
        else:
            parsed[key] = dt

    offer = parsed.get("offer_date")
    closing = parsed.get("closing_date")
    irrev = parsed.get("irrevocability_date")

    if offer and closing and closing < offer:
        result.add_error(
            "Closing date is before the offer date."
        )
    if offer and irrev and irrev < offer:
        result.add_error(
            "Irrevocability date is before the offer date."
        )
    if closing and irrev and irrev > closing:
        result.add_warning(
            "Irrevocability date is after the closing date — please confirm."
        )

    start = parsed.get("lease_start_date")
    end = parsed.get("lease_end_date")
    if start and end and end <= start:
        result.add_error(
            "Lease end date must be after the lease start date."
        )


def _check_lease_terms(result: ValidationResult, data: dict, doc_type: str) -> None:
    """Lease-specific amount checks (rent, deposit)."""
    if doc_type != "lease":
        return

    raw_rent = data.get("monthly_rent")
    has_rent = not (raw_rent is None or (isinstance(raw_rent, str) and not raw_rent.strip()))
    rent = 0.0
    if has_rent:
        rent = normalize_number(raw_rent)
        if rent <= 0:
            result.add_error(
                f"Monthly rent '{raw_rent}' is not a valid positive amount."
            )

    raw_dep = data.get("rent_deposit")
    has_dep = not (raw_dep is None or (isinstance(raw_dep, str) and not raw_dep.strip()))
    if has_dep:
        dep = normalize_number(raw_dep)
        if dep <= 0:
            result.add_error(
                f"Rent deposit '{raw_dep}' is not a valid positive amount."
            )
        elif rent > 0 and dep > rent * 3:
            result.add_warning(
                f"Rent deposit (${dep:,.2f}) is more than 3 months' rent — "
                f"Ontario convention is first and last month. Please confirm."
            )


def _check_postal_code(result: ValidationResult, data: dict) -> None:
    raw = data.get("property_postal_code")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return
    if not _POSTAL_RE.match(str(raw).strip()):
        result.add_warning(
            f"Postal code '{raw}' doesn't look like a valid Canadian "
            f"postal code (e.g. M5V 2T6)."
        )
