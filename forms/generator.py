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


async def generate_document(
    doc_type: str,
    deal_data: dict,
    two_factor_callback: Callable[[], Awaitable[str]] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Generate a document.

    Returns (pdf_path, td_result). td_result is the TransactionDesk
    workflow outcome ({} if TD was not attempted).

    Tries TransactionDesk first. Falls back to local PDF if TD is not
    configured or fails.
    """
    settings = get_settings()
    td_result: dict[str, Any] = {}

    # Try TransactionDesk (primary path)
    if settings.is_realm_configured:
        try:
            from integrations.transactiondesk import TransactionDeskClient

            td = TransactionDeskClient(two_factor_callback=two_factor_callback)
            td_result = await td.run_full_workflow(deal_data, doc_type)

            if td_result.get("success"):
                logger.info("TransactionDesk form filled successfully: %s", td_result.get("form_url"))
                # Generate a summary PDF with TD links
                td_links = {
                    "transaction_url": td_result.get("transaction_url"),
                    "form_url": td_result.get("form_url"),
                }
                return generate_summary_pdf(deal_data, doc_type, td_links=td_links), td_result

            logger.warning("TransactionDesk failed: %s", td_result.get("error"))
        except Exception as e:
            logger.exception("TransactionDesk error: %s", e)
            td_result = {"success": False, "error": str(e)}

    # Fallback: local PDF
    logger.info("Using fallback PDF generation for %s", doc_type)
    if doc_type == "aps":
        return generate_aps_pdf(deal_data), td_result
    return generate_summary_pdf(deal_data, doc_type), td_result
