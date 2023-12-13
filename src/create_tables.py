from .create_database import database_instance
from .models import Base

database = database_instance()

Base.metadata.create_all(database)
