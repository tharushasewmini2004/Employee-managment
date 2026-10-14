# create_tables.py
from app import models  # noqa: F401  (loads the models so SQLAlchemy knows the tables)
from app.database import Base, engine

Base.metadata.create_all(engine)
print("Tables created: departments, employees, leaves")