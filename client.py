import pymongo
from settings import *


class MongoClient:
    def __init__(self, host=HOST, database=MONGO_DB):
        self.client = pymongo.MongoClient(HOST)
        self.db = self.client(database)
