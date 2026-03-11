import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base,sessionmaker

from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

# Get the URL from the environment
SQLALCHEMY_DATABASE_URL = os.environ.get('DATABASE_URL')

# Fix for common naming issues (Postgres vs Postgresql)
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create the Engine
# Note: For Cloud/Postgres, we don't need 'check_same_thread'
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # This checks if the connection is alive before using it
    connect_args={'sslmode': 'require'} # Explicitly force SSL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

"""
DATABASE_URL = "sqlite:///app.db"


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread":False}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()"""