from dashboard.backend.db.base import Base
from dashboard.backend.db.engine import engine

# Import all models so they register with Base.metadata
import dashboard.backend.auth.models  # noqa: F401
import dashboard.backend.platforms.models  # noqa: F401
import dashboard.backend.analytics.models  # noqa: F401


async def init_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
