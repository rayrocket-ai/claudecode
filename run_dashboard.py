"""Entry point for the Video Script Dashboard."""

import uvicorn
from config import get_settings


def main():
    settings = get_settings()
    uvicorn.run(
        "dashboard.app:app",
        host=settings.dashboard_host,
        port=settings.dashboard_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
