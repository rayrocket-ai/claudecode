"""Off-market status derivation.

Given a `CanonicalProperty` and its `Listing` history, compute which listing
is "current" and whether the property is on the off-market dashboard.

Rules (agreed v1):
  - A property is **on the dashboard** when its LATEST listing is Expired
    or Terminated AND no later listing is Active or Sold.
  - Sold → always hidden from the dashboard.
  - Active → hidden (even if a previous listing expired).
  - Conditional → shown with a "Conditional" badge (seller deal might
    collapse back to Active/Expired).
  - Suspended → not on the dashboard (seller paused).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Iterable

from db.models import Listing


OFF_MARKET_STATUSES = {"Expired", "Terminated"}
ACTIVE_LIKE_STATUSES = {"Active", "Conditional"}
REMOVED_STATUSES = {"Sold"}


def _listing_sort_key(lst: Listing) -> tuple[date, datetime]:
    """Sort listings chronologically. Prefer commencement_date; fall back
    to created_at. Listings without any date sort last."""
    commence = lst.commencement_date or date.min
    created = lst.created_at or datetime.min
    # Ensure datetime has no tzinfo for comparison
    if hasattr(created, "tzinfo") and created.tzinfo is not None:
        created = created.replace(tzinfo=None)
    return (commence, created)


def latest_listing(listings: Iterable[Listing]) -> Listing | None:
    """Return the most recent listing in a property's history."""
    listings = list(listings)
    if not listings:
        return None
    return max(listings, key=_listing_sort_key)


def derive_current_status(listings: Iterable[Listing]) -> str:
    """Compute the denormalized `current_status` for a CanonicalProperty."""
    latest = latest_listing(listings)
    if latest is None:
        return "Unknown"
    return latest.status or "Unknown"


def is_off_market(listings: Iterable[Listing]) -> bool:
    """True if the property should appear on the off-market dashboard."""
    latest = latest_listing(listings)
    if latest is None:
        return False
    return latest.status in OFF_MARKET_STATUSES
