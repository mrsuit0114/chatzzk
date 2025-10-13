from sqlalchemy.orm import declarative_base

# Create a single DeclarativeBase instance for the entire application's ORM models.
# All ORM models will inherit from this Base.
Base = declarative_base()
