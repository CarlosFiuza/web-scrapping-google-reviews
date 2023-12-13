from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()


user = os.environ["DB_USERNAME"]
password = os.environ["DB_PASS"]
host = os.environ["DB_HOST"]
port = os.environ["DB_PORT"]

instance = None


def database_instance():
    global instance
    if not instance:
        instance = create_engine(
            url=f"postgresql://{user}:{password}@{host}:{port}/postgres")
        return instance
    return instance
