from pymongo import MongoClient

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    def connect(self, mongo_uri: str):
        self.client = MongoClient(mongo_uri)
        self.db = self.client["HBH"]

    def disconnect(self):
        if self.client:
            self.client.close()

    def get_collection(self, collection_name: str):
        if self.db is None:
            raise Exception("Database connection is not initialized")
        return self.db[collection_name]

# Global MongoDB instance
mongodb = None

def init_mongoDB(settings):
    global mongodb
    mongodb = MongoDB()
    mongo_uri = settings.MONGO_URI
    mongodb.connect(mongo_uri)

def get_db():
    if mongodb is None:
        raise Exception("MongoDB is not initialized")
    return mongodb
