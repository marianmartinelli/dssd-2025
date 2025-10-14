from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import get_settings

# Create the database engine
settings = get_settings()
engine = create_async_engine(settings.database_url, future=True, echo=True)

# Create a session factory
async_session_factory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency to get the database session
async def get_db_session():
    async with async_session_factory() as session:
        yield session

# Define the base class for models
Base = declarative_base()