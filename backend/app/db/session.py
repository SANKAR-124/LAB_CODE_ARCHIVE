# Generator is a type hint from Python's built-in collections module.
# It is used to annotate functions that use 'yield' (like get_db below).
from collections.abc import Generator

# declarative_base  → creates the base class that all SQLAlchemy ORM models will inherit from.
# sessionmaker      → a factory that produces database Session objects with a fixed configuration.
# Session           → the type used for type-hinting the db session.
from sqlalchemy.orm import declarative_base,sessionmaker,Session

# Imports the SQLAlchemy engine created in database.py.
# The engine holds the actual DB connection pool and knows how to talk to your database.
from app.db.database import engine

# Creates a configured Session factory called 'Sessionlocal'.
# autocommit=False → transactions must be committed manually (safer, prevents accidental writes).
# autoflush=False  → SQLAlchemy won't auto-sync pending ORM changes to the DB before queries.
# bind=engine      → ties this session factory to the engine (i.e., your actual database).
Sessionlocal=sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Creates the declarative base class.
# All your ORM models (e.g., User, Lab) will inherit from this Base.
# It keeps track of all mapped tables so SQLAlchemy can create/query them.
Base=declarative_base()

# A FastAPI dependency function that provides a database session to route handlers.
# Return type Generator[Session] means: this function yields a Session object (one per request).
def get_db()->Generator[Session]:
    # Opens a new database session for the current request.
    db=Sessionlocal()
    try:
        # Yields the session to the route handler (pauses here until the request is done).
        yield db
    finally:
        # Always closes the session after the request finishes, even if an error occurred.
        # This returns the connection back to the pool and prevents connection leaks.
        db.close()
