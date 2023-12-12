from peewee import *
from .create import database_instance

db = database_instance()


class ReviewModel(Model):
    author = CharField(null=False)
    comment = TextField()
    rating = SmallIntegerField(null=False)
    rating_scale = CharField(null=False)
    estimated_date = DateTimeField(null=False)

    class Meta:
        database = db
        table_name = "review"
