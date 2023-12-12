from peewee import *
from dotenv import load_dotenv
import os

load_dotenv()


user = os.environ["DB_USERNAME"]
password = os.environ["DB_PASS"]
host = os.environ["DB_HOST"]
port = os.environ["DB_PORT"]


def database_instance():
    return PostgresqlDatabase(
        database='postgres', user=user, password=password, host=host, port=port)
