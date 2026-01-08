from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from os import getenv

load_dotenv()

POSTGRES_HOST = getenv('DB_HOST')
POSTGRES_PORT = getenv('DB_PORT')
POSTGRES_USER = getenv('DB_USERNAME')
POSTGRES_PASSWORD = getenv('DB_PASSWORD')
POSTGRES_DB = getenv('DB_NAME')
DEBUG = getenv('DEBUG')

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_async_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session
