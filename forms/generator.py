"""Document generation orchestrator.

Primary path: TransactionDesk (WebForms) via browser automation.
Fallback: Local PDF generation with ReportLab.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Awaitable

from config import get_settings
from forms.pdf_builder import generate_aps_pdf, generate_summary_pdf

logger = logging.getLogger(__name__)

# Store last TD result so the bot handler can read it
_last_td_result: dict[str, Any] = {}


def get_last_td_result() -> dict[str, Any]:
    return dict(_last_td_result)


async def generate_document(
    doc_type: str,
    deal_data: dict,
    two_factor_callback: Callable[[], Awaitable[str]] | None = None,
) -> str:
    """Generate a document. Returns path to the output PDF.

    Tries TransactionDesk first. Falls back to local PDF if TD is not
    configured or fails.
    """
    global _last_td_result
    settings = get_settings()

    # Try TransactionDesk (primary path)
    if settings.is_realm_configured:
        try:
            from integrations.transactiondesk import TransactionDeskClient

            td = TransactionDeskClient(two_factor_callback=two_factor_callback)
            result = await td.run_full_workflow(deal_data, doc_type)
            _last_td_result = result

            if result.get("success"):
                logger.info("TransactionDesk form filled successfully: %s", result.get("form_url"))
                # Generate a summary PDF with TD links
                td_links = {
                    "transaction_url": result.get("transaction_url"),
                    "form_url": result.get("form_url"),
                }
                return generate_summary_pdf(deal_data, doc_type, td_links=td_links)

            logger.warning("TransactionDesk failed: %s", result.get("error"))
        except Exception as e:
            logger.exception("TransactionDesk error: %s", e)
            _last_td_result = {"success": False, "error": str(e)}

    # Fallback: local PDF
    logger.info("Using fallback PDF generation for %s", doc_type)
    if doc_type == "aps":
        return generate_aps_pdf(deal_data)
    else:
        return generate_summary_pdf(deal_data, doc_type)
