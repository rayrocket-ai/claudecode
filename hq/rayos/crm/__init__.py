"""CRM adapters.

The engine never imports a vendor SDK. It talks to :class:`~rayos.crm.base.
CRMAdapter`, and exactly one implementation is wired in at startup. Lofty is
the choice of record; the interface exists so that choice is switchable
without a rewrite, and so every rule above it can be tested against
:class:`~rayos.crm.memory.InMemoryCRM` with no network at all.
"""

from .base import (
    Activity,
    Appointment,
    Contact,
    CRMAdapter,
    CRMError,
    Task,
    WebhookEvent,
)
from .memory import InMemoryCRM

__all__ = [
    "Activity",
    "Appointment",
    "Contact",
    "CRMAdapter",
    "CRMError",
    "InMemoryCRM",
    "Task",
    "WebhookEvent",
]
