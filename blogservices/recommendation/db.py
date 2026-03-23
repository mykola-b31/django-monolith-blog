import os
import pymongo
from dotenv import load_dotenv

load_dotenv()

mongo_server = os.environ['RECOMMENDATION_DB_URL']
mongo_user = os.environ['MONGO_RECOMM_USER']
mongo_pass = os.environ['MONGO_RECOMM_PASS']
mongo_client = pymongo.MongoClient(f"mongodb://{mongo_server}/",
                                   username=mongo_user,
                                   password=mongo_pass)
recommendation_db = mongo_client[os.environ['RECOMMENDATION_DB']]

def get_recommendations(author_id):
    col = recommendation_db['recommendations']
    result = col.find({
        "author": {"$ne": int(author_id)},
    }, projection={'_id': False})

    return [res for res in result]

def create_recommendation(recommendation):
    col = recommendation_db['recommendations']
    result = col.insert_one(recommendation)
    return str(result.inserted_id)