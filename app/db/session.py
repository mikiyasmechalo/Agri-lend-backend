from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

if settings.is_postgres:
    engine = create_async_engine(
        settings.database_url, echo=settings.debug, pool_size=10, max_overflow=20
    )
else:
    engine = create_async_engine(
        settings.database_url, echo=settings.debug, connect_args={"check_same_thread": False}
    )

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
