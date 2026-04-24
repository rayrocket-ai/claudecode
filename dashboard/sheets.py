"""Google Sheets sync for the master listings spreadsheet.

Auth: service account. The JSON key comes from env var GOOGLE_SERVICE_ACCOUNT_JSON
(the JSON content itself, not a path — Railway-friendly). The sheet must be
shared with the service account's client_email as Viewer.

The sync function is header-tolerant: it looks at the first row and matches any
of the common aliases below, so Ray's existing sheet should just work.
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from .models import Listing, json_dump

logger = logging.getLogger(__name__)


# ── Column alias map ───────────────────────────────────────────────────────
# Any header in the sheet that normalises (lowercase, non-alphanumeric → _) to
# one of these aliases is mapped to the canonical field.

HEADER_ALIASES: Dict[str, List[str]] = {
    "external_id": ["id", "row_id", "listing_id", "uid"],
    "mls": ["mls", "mls_number", "mlsnumber", "mls_id"],
    "address": ["address", "street", "street_address", "property_address", "property"],
    "city": ["city", "municipality", "town"],
    "province": ["province", "state", "prov"],
    "postal_code": ["postal_code", "postal", "zip", "zipcode"],
    "price": ["price", "list_price", "listing_price", "asking_price", "sale_price"],
    "bedrooms": ["bedrooms", "beds", "bed", "br"],
    "bathrooms": ["bathrooms", "baths", "bath", "ba"],
    "sqft": ["sqft", "square_feet", "sq_ft", "size", "floor_area"],
    "property_type": ["property_type", "type", "home_type", "style"],
    "listing_type": ["listing_type", "transaction_type", "for_sale_or_rent", "sale_type"],
    "status": ["status", "state", "listing_status"],
    "fb_post_id": ["fb_post_id", "facebook_post_id", "post_id"],
    "fb_post_url": ["fb_post_url", "facebook_url", "facebook_post_url", "fb_link", "video_url", "reel_url"],
    "listing_url": ["listing_url", "mls_url", "link", "url", "realtor_url"],
    "notes": ["notes", "description", "comments", "remarks"],
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _build_header_map(raw_headers: List[str]) -> Dict[int, str]:
    """Return {col_index: canonical_field} for headers we recognise."""
    mapping: Dict[int, str] = {}
    # Build reverse index: normalised_alias → canonical
    reverse: Dict[str, str] = {}
    for canonical, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            reverse[_norm(alias)] = canonical
    for i, h in enumerate(raw_headers or []):
        key = _norm(h or "")
        if key in reverse:
            mapping[i] = reverse[key]
    return mapping


# ── Value parsers ──────────────────────────────────────────────────────────

_PRICE_RE = re.compile(r"[\d,]+(?:\.\d+)?")


def _parse_price(val) -> Tuple[Optional[int], Optional[str]]:
    """Return (integer_dollars, human_label). Handles '$1,299,000' / '1299000' / '$1.3M'."""
    if val is None or val == "":
        return None, None
    s = str(val).strip()
    if not s:
        return None, None
    label = s
    # "$1.3M" / "1.3m"
    m = re.match(r"^\$?\s*([\d.]+)\s*([mMkK])$", s)
    if m:
        base = float(m.group(1))
        mul = 1_000_000 if m.group(2).lower() == "m" else 1_000
        return int(base * mul), label
    match = _PRICE_RE.search(s)
    if not match:
        return None, label
    clean = match.group(0).replace(",", "")
    try:
        return int(float(clean)), label
    except ValueError:
        return None, label


def _parse_float(val) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        return float(str(val).replace(",", "").strip())
    except ValueError:
        return None


def _parse_int(val) -> Optional[int]:
    f = _parse_float(val)
    return int(f) if f is not None else None


def _extract_fb_post_id(url_or_id: Optional[str]) -> Optional[str]:
    """Pull a post id out of a FB url like facebook.com/123/posts/456 or /videos/789."""
    if not url_or_id:
        return None
    s = str(url_or_id).strip()
    if not s:
        return None
    # If it already looks like an id (digits or pageid_postid)
    if re.fullmatch(r"\d+(_\d+)?", s):
        return s
    # Try common URL shapes
    m = re.search(r"/(?:posts|videos|reel|photos)/(\d+)", s)
    if m:
        return m.group(1)
    m = re.search(r"[?&]story_fbid=(\d+)", s)
    if m:
        return m.group(1)
    return None


# ── Google Sheets client ──────────────────────────────────────────────────

def _load_credentials():
    """Load a google.oauth2 Credentials object from GOOGLE_SERVICE_ACCOUNT_JSON env."""
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON not set. Paste the full service-account "
            "JSON as an env var."
        )
    # Accept either raw JSON or a file path
    if raw.startswith("{"):
        info = json.loads(raw)
    else:
        with open(raw, "r") as f:
            info = json.load(f)
    from google.oauth2.service_account import Credentials
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    return Credentials.from_service_account_info(info, scopes=scopes)


def fetch_sheet_rows(
    spreadsheet_id: Optional[str] = None,
    worksheet: Optional[str] = None,
) -> Tuple[List[str], List[List[str]]]:
    """Return (headers, rows) from the configured listings sheet."""
    import gspread

    spreadsheet_id = spreadsheet_id or os.getenv("LISTINGS_SHEET_ID", "").strip()
    worksheet = worksheet or os.getenv("LISTINGS_SHEET_TAB", "").strip() or None

    if not spreadsheet_id:
        raise RuntimeError("LISTINGS_SHEET_ID not set")

    creds = _load_credentials()
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(spreadsheet_id)
    ws = sh.worksheet(worksheet) if worksheet else sh.sheet1
    all_values = ws.get_all_values()
    if not all_values:
        return [], []
    headers, *rows = all_values
    return headers, rows


# ── Sync logic ─────────────────────────────────────────────────────────────

def sync_listings(db: Session) -> Dict[str, int]:
    """Pull rows from the master sheet and upsert into the listings table."""
    headers, rows = fetch_sheet_rows()
    col_map = _build_header_map(headers)
    if not col_map:
        logger.warning(f"No recognised columns in sheet headers: {headers}")

    inserted = 0
    updated = 0
    skipped = 0

    for row_idx, row in enumerate(rows, start=2):  # start=2 to match sheet row numbers
        raw: Dict[str, str] = {}
        for i, val in enumerate(row):
            if i in col_map:
                raw[col_map[i]] = val
            # keep originals too
            if i < len(headers):
                raw.setdefault(f"_col_{headers[i]}", val)

        # Skip empty rows
        if not any(raw.get(k) for k in ("address", "mls", "external_id", "listing_url")):
            skipped += 1
            continue

        price_val, price_label = _parse_price(raw.get("price"))

        external_id = (raw.get("external_id") or raw.get("mls") or "").strip()
        if not external_id:
            # Fall back to a stable synthetic id: row index + address
            external_id = f"row_{row_idx}:{(raw.get('address') or '')[:60]}"

        # Determine fb post id
        fb_post_id = (raw.get("fb_post_id") or "").strip() or _extract_fb_post_id(raw.get("fb_post_url"))

        existing = db.query(Listing).filter(Listing.external_id == external_id).first()
        fields = dict(
            external_id=external_id,
            address=(raw.get("address") or "").strip() or None,
            city=(raw.get("city") or "").strip() or None,
            province=(raw.get("province") or "ON").strip() or "ON",
            postal_code=(raw.get("postal_code") or "").strip() or None,
            price=price_val,
            price_label=price_label,
            bedrooms=_parse_float(raw.get("bedrooms")),
            bathrooms=_parse_float(raw.get("bathrooms")),
            sqft=_parse_int(raw.get("sqft")),
            property_type=(raw.get("property_type") or "").strip() or None,
            listing_type=(raw.get("listing_type") or "").strip() or None,
            status=((raw.get("status") or "active").strip().lower() or "active"),
            mls=(raw.get("mls") or "").strip() or None,
            fb_post_id=fb_post_id,
            fb_post_url=(raw.get("fb_post_url") or "").strip() or None,
            listing_url=(raw.get("listing_url") or "").strip() or None,
            notes=(raw.get("notes") or "").strip() or None,
            raw_row=json_dump({k: v for k, v in raw.items() if not k.startswith("_col_")}),
            synced_at=datetime.utcnow(),
        )

        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
            updated += 1
        else:
            db.add(Listing(**fields))
            inserted += 1

    db.commit()
    return {"inserted": inserted, "updated": updated, "skipped": skipped, "headers": headers}
