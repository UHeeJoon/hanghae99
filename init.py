import requests
from bs4 import BeautifulSoup

# 별점 0으로 초기화

from pymongo import MongoClient
from bson.objectid import ObjectId
client = MongoClient('localhost', 27017)
db = client.dbteamsparta


def review_modify():
    db.restaurant.update_many({},{'$set':{'like':0}})


review_modify()