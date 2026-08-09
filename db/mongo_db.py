# mongo_db.py
# Week 2 - MongoDB integration.
# Follows the same pattern as redis_db.py: connect, ingest from
# utils/data_loader.py, CRUD, 3 features.

# Used redis_db.py as a framework for as much uniformity as possible -Signy
# Updated to use one collection per dataset type instead of one shared
# collection, so commits/repos/languages/licenses don't mix. -Haley
import os
import sys

import pymongo

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_jsonl, dataset_path


class MongoManager:
    def __init__(self, host="localhost", port=27017):
        self.client = pymongo.MongoClient(f"mongodb://{host}:{port}")
        self.db = self.client["MongoDatabase"]
        self.commits = self.db["commits"]
        self.repos = self.db["repos"]
        self.languages = self.db["languages"]
        self.licenses = self.db["licenses"]

    def ping(self):
        try:
            return self.client.admin.command("ping")
        except Exception:
            return False

    # ---------- ingestion ----------

    def ingest_commits(self, limit=500):
        filepath = dataset_path("commits")
        count = 0
        for record in load_jsonl(filepath, limit=limit):
            self.commits.insert_one(record)
            count += 1
        return count

    def ingest_repos(self, limit=2000):
        filepath = dataset_path("sample_repos")
        count = 0
        for record in load_jsonl(filepath, limit=limit):
            self.repos.insert_one(record)
            count += 1
        return count

    def ingest_languages(self, limit=2000):
        filepath = dataset_path("languages")
        count = 0
        for record in load_jsonl(filepath, limit=limit):
            self.languages.insert_one(record)
            count += 1
        return count

    # Licenses.json is small (~25k lines) and the license values are grouped
    # together in the file, so a partial read can end up missing a license
    # type entirely (found this while testing - only 2 licenses show up in
    # the whole file anyway, isc and artistic-2.0). Just load the whole thing.
    def ingest_licenses(self, limit=None):
        filepath = dataset_path("licenses")
        count = 0
        for record in load_jsonl(filepath, limit=limit):
            self.licenses.insert_one(record)
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
        if self.commits.find_one({"commit": sha}) is not None:
            return False
        self.commits.insert_one({"commit": sha,
                                  "repo_name": repo_name,
                                  "author_name": author_name,
                                  "author_email": author_email,
                                  "message": message})
        return True

    def read_commit(self, sha):
        return self.commits.find_one({"commit": sha}, {"_id": 0})

    def update_commit(self, sha, field, value):
        query = {"commit": sha}
        updateData = {"$set": {field: value}}
        result = self.commits.update_one(query, updateData)
        return result.matched_count > 0

    def delete_commit(self, sha):
        return self.commits.delete_one({"commit": sha})

    def list_commit_keys(self, limit=20):
        keys = []
        keyResult = self.commits.find({"commit": {"$exists": True}},
                                       {"_id": 0, "commit": 1}).limit(limit)
        for key in keyResult:
            keys.append(key)
        return keys

    # ---------- features ----------

    # feature 1: longest and shortest repo names via $strLenCP
    # (reads from the repos collection now, since repo_name lives there)
    def find_longest_shortest(self):
        maxResult = self.repos.aggregate([
            {"$match": {"repo_name": {"$exists": True}}},
            {"$addFields": {"repo_name_length": {"$strLenCP": "$repo_name"}}},
            {"$sort": {"repo_name_length": -1}},
            {"$project": {"_id": 0, "repo_name": 1, "repo_name_length": 1}},
            {"$limit": 1}])
        minResult = self.repos.aggregate([
            {"$match": {"repo_name": {"$exists": True}}},
            {"$addFields": {"repo_name_length": {"$strLenCP": "$repo_name"}}},
            {"$sort": {"repo_name_length": 1}},
            {"$project": {"_id": 0, "repo_name": 1, "repo_name_length": 1}},
            {"$limit": 1}])
        for doc in maxResult:
            print(doc)
        for doc in minResult:
            print(doc)

    # feature 2: top repos by watch count (reads from the repos collection)
    def top_repos_by_watch(self):
        watchResult = self.repos.find({"repo_name": {"$exists": True},
                                        "watch_count": {"$exists": True}},
                                       {"_id": 0}).sort("watch_count", -1)
        return watchResult

    # feature 3: most popular commit messages (reads from the commits collection)
    def popular_comments(self):
        comResult = self.commits.aggregate([
            {"$match": {"message": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": "$message", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}])
        return comResult

    # wipes everything this app wrote to mongoDB now, for resetting between demo runs
    def flush_all(self):
        total = 0
        for col in (self.commits, self.repos, self.languages, self.licenses):
            d = col.delete_many({})
            total += d.deleted_count
        print(total, " documents deleted.")
