"""Vercel serverless entrypoint — exposes the RayRocket Studio storefront."""

from studio.app import app  # noqa: F401  (Vercel discovers the ASGI `app`)
