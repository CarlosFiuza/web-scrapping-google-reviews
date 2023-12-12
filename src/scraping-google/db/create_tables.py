from create import database_instance
from review_model import ReviewModel

database = database_instance()
database.connect()
database.create_tables([ReviewModel])
