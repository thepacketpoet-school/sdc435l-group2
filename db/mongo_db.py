# mongo_db.py
# Week 2 - MongoDB integration. Not started yet.
# Should follow the same pattern as redis_db.py: connect, ingest from
# utils/data_loader.py, CRUD, 3 features.

# Used redis_db.py as a framework for as much uniformity as possible -Signy
import os
import sys

import pymongo

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_jsonl, dataset_path



class MongoManager:
    def __init__(self, host="localhost", port=27017):
        self.client = pymongo.MongoClient("mongodb://localhost:27017")
        db = self.client["MongoDatabase"]
        mongoCol = db["MongoCollection"]

    def ping(self):
        try:
            return self.client.admin.command("ping")
        except Exception:
            return False

    # ---------- ingestion ----------

    def ingest_commits(self, limit=500):
        db = self.client["MongoDatabase"]
        mongoCol = db["MongoCollection"]
        filepath = dataset_path("commits")
        count = 0
        for record in load_jsonl(filepath, limit=limit):
            mongoCol.insert_one(record)
            count += 1
        return count

    def ingest_repos(self, limit=2000):
        db = self.client["MongoDatabase"]
        mongoCol = db["MongoCollection"]
        filepath = dataset_path("sample_repos")
        count = 0
        for record in load_jsonl(filepath, limit=limit):
            mongoCol.insert_one(record)
            count += 1
        return count

    def ingest_languages(self, limit=2000):
        db = self.client["MongoDatabase"]
        mongoCol = db["MongoCollection"]
        filepath = dataset_path("languages")
        count = 0
        for record in load_jsonl(filepath, limit=limit):
            mongoCol.insert_one(record)
            count += 1
        return count

    # Licenses.json is small (~25k lines) and the license values are grouped
    # together in the file, so a partial read can end up missing a license
    # type entirely (found this while testing - only 2 licenses show up in
    # the whole file anyway, isc and artistic-2.0). Just load the whole thing.
    def ingest_licenses(self, limit=None):
        db = self.client["MongoDatabase"]
        mongoCol = db["MongoCollection"]
        filepath = dataset_path("licenses")
        count = 0
        for record in load_jsonl(filepath, limit=limit):
            mongoCol.insert_one(record)
            count += 1
        return count

    def ingest_all(self, commit_limit=500, repo_limit=2000, language_limit=2000, license_limit=None):
        return {
            "commits": self.ingest_commits(commit_limit),
            "repos": self.ingest_repos(repo_limit),
            "languages": self.ingest_languages(language_limit),
            "licenses": self.ingest_licenses(license_limit),
        }

    # ---------- CRUD on commit records ----------

    def create_commit(self, sha, repo_name, author_name, author_email, message):
        db = self.client["MongoDatabase"]
        mongoCol = db["MongoCollection"]
        if mongoCol.find_one({"commit": sha}) is not None:
            return False
        mongoCol.insert_one({"commit": sha,
                             "repo_name": repo_name,
                             "author_name": author_name,
                             "author_email": author_email,
                             "message": message})
        return True

    def read_commit(self, sha):
        db = self.client["MongoDatabase"]
        mongoCol = db["MongoCollection"]
        if mongoCol.find_one({"commit": sha}) is None:
            return None
        return mongoCol.find_one({"commit": sha}, {"_id": 0})

    def update_commit(self, sha, field, value):
        db = self.client["MongoDatabase"]
        mongoCol = db["MongoCollection"]
        query = {"commit": sha}
        updateData = {"$set": {field: value}}
        if mongoCol.find_one({"commit": sha}) is None:
            return False
        mongoCol.update_one(query, updateData)
        return True

    def delete_commit(self, sha):
        db = self.client["MongoDatabase"]
        mongoCol = db["MongoCollection"]
        return mongoCol.delete_one({"commit": sha})

    def list_commit_keys(self, limit=20):
        db = self.client["MongoDatabase"]
        mongoCol = db["MongoCollection"]
        keys = []
        keyResult = mongoCol.find({"commit": {"$exists": True}},
                                  {"_id": 0, "commit": 1}).limit(100)
        for key in keyResult:
            keys.append(key)
            if len(keys) >= limit:
                break
        return keys

    # ---------- features ----------

    # feature 1: longest and shortest repo names via $strLenCP
    def find_longest_shortest(self):
        db = self.client["MongoDatabase"]
        mongoCol = db["MongoCollection"]
        maxResult = mongoCol.aggregate([
            {"$unwind": "$repo_name"},
            {"$addFields": {"repo_name_length": {"$strLenCP": "$repo_name"}}},
            {"$sort": {"repo_name_length": -1}},
            {"$project": {"_id": 0, "repo_name": 1, "repo_name_length": 1}},
            {"$limit": 1}])
        minResult = mongoCol.aggregate([
            {"$unwind": "$repo_name"},
            {"$addFields": {"repo_name_length": {"$strLenCP": "$repo_name"}}},
            {"$sort": {"repo_name_length": 1}},
            {"$project": {"_id": 0, "repo_name": 1, "repo_name_length": 1}},
            {"$limit": 1}])
        for doc in maxResult:
            print(doc)
        for doc in minResult:
            print(doc)
        

    # feature 2: top repos by watch count
    def top_repos_by_watch(self):
        db = self.client["MongoDatabase"]
        mongoCol = db["MongoCollection"]
        watchResult = mongoCol.find({"repo_name": {"$exists": True},
                                     "watch_count": {"$exists": True}},
                                     {"_id": 0}).sort("watch_count", -1)
        return watchResult

    # feature 3: most popular comments
    def popular_comments(self):
        db = self.client["MongoDatabase"]
        mongoCol = db["MongoCollection"]
        comResult = mongoCol.aggregate([
            {"$match": {"message": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": "$message", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}])
        return comResult
        
    # wipes everything this app wrote to mongoDB now, for resetting between demo runs
    def flush_all(self):
        db = self.client["MongoDatabase"]
        mongoCol = db["MongoCollection"]
        d = mongoCol.delete_many({})
        print(d.deleted_count, " documents deleted.")
