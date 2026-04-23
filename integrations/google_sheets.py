"""Read the Higgsfield tracking sheet where each row is a house video.

Each row is expected to provide at minimum:
    - address (street address of the house)
    - video_url (link to the Higgsfield-generated tour video)

Optional columns used by the automation for state tracking:
    - status (pending / processing / done / error)
    - final_video_url (populated once the voiceover-edited video is uploaded)

Two back-ends are supported and selected automatically based on settings:

1. Service-account (read/write):
     GOOGLE_SHEETS_CREDENTIALS_PATH -> JSON key path
     HIGGSFIELD_SHEET_ID            -> spreadsheet id
     HIGGSFIELD_WORKSHEET_NAME      -> tab name
   Requires `gspread` + `google-auth`.

2. Public CSV export (read-only):
     GOOGLE_SHEETS_CSV_URL -> "Publish to web" CSV URL
"""

from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class HouseVideoRow:
    """One row of the Higgsfield tracking sheet."""

    row_number: int  # 1-based index in the worksheet (header = 1)
    address: str
    video_url: str
    status: str = ""
    final_video_url: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_pending(self) -> bool:
        return self.status.strip().lower() in ("", "pending", "queued", "new")


class HiggsfieldSheet:
    """Abstracts reading/writing the Higgsfield tracking sheet."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._backend: str = self._pick_backend()
        self._worksheet: Any = None  # gspread Worksheet lazily loaded

    def _pick_backend(self) -> str:
        if self.settings.google_sheets_credentials_path and self.settings.higgsfield_sheet_id:
            return "gspread"
        if self.settings.google_sheets_csv_url:
            return "csv"
        raise ValueError(
            "Google Sheets not configured. Set GOOGLE_SHEETS_CREDENTIALS_PATH + "
            "HIGGSFIELD_SHEET_ID, or GOOGLE_SHEETS_CSV_URL, in .env."
        )

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------
    async def fetch_rows(self, *, only_pending: bool = True) -> list[HouseVideoRow]:
        """Return rows from the sheet, optionally filtered to pending ones."""
        if self._backend == "gspread":
            rows = await self._fetch_via_gspread()
        else:
            rows = await self._fetch_via_csv()

        if only_pending:
            rows = [r for r in rows if r.is_pending and r.address and r.video_url]
        return rows

    async def _fetch_via_csv(self) -> list[HouseVideoRow]:
        url = self.settings.google_sheets_csv_url
        logger.info("Fetching Higgsfield sheet via CSV export")
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        return self._parse_csv(resp.text)

    async def _fetch_via_gspread(self) -> list[HouseVideoRow]:
        ws = self._ensure_worksheet()
        # gspread is synchronous; offload to default executor so we don't block
        import asyncio

        records = await asyncio.to_thread(ws.get_all_records)
        return self._rows_from_records(records)

    def _parse_csv(self, text: str) -> list[HouseVideoRow]:
        reader = csv.DictReader(io.StringIO(text))
        records = [dict(r) for r in reader]
        return self._rows_from_records(records)

    def _rows_from_records(self, records: list[dict[str, Any]]) -> list[HouseVideoRow]:
        s = self.settings
        addr_key = _norm(s.higgsfield_address_column)
        video_key = _norm(s.higgsfield_video_url_column)
        status_key = _norm(s.higgsfield_status_column)
        output_key = _norm(s.higgsfield_output_column)

        rows: list[HouseVideoRow] = []
        for idx, record in enumerate(records, start=2):  # row 1 is header
            normalized = {_norm(k): ("" if v is None else str(v).strip()) for k, v in record.items()}
            address = normalized.get(addr_key, "")
            video_url = normalized.get(video_key, "")
            if not address and not video_url:
                continue
            rows.append(
                HouseVideoRow(
                    row_number=idx,
                    address=address,
                    video_url=video_url,
                    status=normalized.get(status_key, ""),
                    final_video_url=normalized.get(output_key, ""),
                    raw=normalized,
                )
            )
        logger.info("Loaded %d rows from Higgsfield sheet (%s backend)", len(rows), self._backend)
        return rows

    # ------------------------------------------------------------------
    # Writing (service-account backend only)
    # ------------------------------------------------------------------
    async def update_row(
        self,
        row: HouseVideoRow,
        *,
        status: str | None = None,
        final_video_url: str | None = None,
    ) -> None:
        """Write status / final_video_url back to the sheet.

        No-op (with a log warning) when using the CSV backend, since published
        CSV exports are read-only.
        """
        if self._backend != "gspread":
            logger.warning(
                "Skipping sheet update for row %d — CSV backend is read-only",
                row.row_number,
            )
            return

        ws = self._ensure_worksheet()
        import asyncio

        updates: list[tuple[str, str]] = []
        if status is not None:
            col = self._column_for(self.settings.higgsfield_status_column)
            if col:
                updates.append((f"{col}{row.row_number}", status))
        if final_video_url is not None:
            col = self._column_for(self.settings.higgsfield_output_column)
            if col:
                updates.append((f"{col}{row.row_number}", final_video_url))

        if not updates:
            return

        def _apply() -> None:
            for cell_addr, value in updates:
                ws.update_acell(cell_addr, value)

        await asyncio.to_thread(_apply)
        logger.info("Updated row %d: %s", row.row_number, dict(updates))

    # ------------------------------------------------------------------
    # gspread plumbing
    # ------------------------------------------------------------------
    def _ensure_worksheet(self) -> Any:
        if self._worksheet is not None:
            return self._worksheet
        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except ImportError as exc:
            raise RuntimeError(
                "gspread + google-auth are required for the service-account backend. "
                "Install with: pip install gspread google-auth"
            ) from exc

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
        creds = Credentials.from_service_account_file(
            self.settings.google_sheets_credentials_path, scopes=scopes
        )
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(self.settings.higgsfield_sheet_id)
        self._worksheet = sh.worksheet(self.settings.higgsfield_worksheet_name)
        return self._worksheet

    def _column_for(self, header_name: str) -> str | None:
        """Find the A1-style column letter for the given header name."""
        ws = self._ensure_worksheet()
        headers = ws.row_values(1)
        target = _norm(header_name)
        for i, h in enumerate(headers):
            if _norm(h) == target:
                return _column_letter(i + 1)
        logger.warning("Column header %r not found in sheet", header_name)
        return None


def _norm(value: str) -> str:
    return (value or "").strip().lower().replace(" ", "_")


def _column_letter(index: int) -> str:
    """1 -> A, 27 -> AA, etc."""
    letters = ""
    while index > 0:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters
