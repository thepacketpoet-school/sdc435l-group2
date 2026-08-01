# redis_db.py
# Week 1 - Redis integration
#
# Commits get stored as Redis hashes: commit:<sha> -> {repo_name, author_name, author_email, message}
# We also use a couple other Redis structures for the 3 features:
#   languages:bytes         sorted set, language -> total bytes (feature 1)
#   leaderboard:watch_count sorted set, repo -> watch count (feature 2)
#   licenses:count          hash, license name -> count (feature 3)

import os
import sys

import redis

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_jsonl, dataset_path


class RedisManager:
    def __init__(self, host="localhost", port=6379, db=0):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def ping(self):
        try:
            return self.client.ping()
        except redis.exceptions.ConnectionError:
            return False

    # ---------- ingestion ----------

    def ingest_commits(self, limit=500):
        filepath = dataset_path("commits")
        count = 0
        for record in load_jsonl(filepath, limit=limit):
            sha = record.get("commit")
            if not sha:
                continue
            author = record.get("author", {}) or {}
            repo_names = record.get("repo_name", [])
            repo_name = repo_names[0] if repo_names else "unknown"
            self.client.hset(
                f"commit:{sha}",
                mapping={
                    "repo_name": repo_name,
                    "author_name": author.get("name", "unknown"),
                    "author_email": author.get("email", "unknown"),
                    "message": (record.get("subject") or "").strip(),
                },
            )
            count += 1
        return count

    def ingest_repos(self, limit=2000):
        filepath = dataset_path("sample_repos")
        count = 0
        for record in load_jsonl(filepath, limit=limit):
            repo_name = record.get("repo_name")
            watch_count = record.get("watch_count")
            if not repo_name or watch_count is None:
                continue
            try:
                watch_count = int(watch_count)
            except ValueError:
                continue
            self.client.zadd("leaderboard:watch_count", {repo_name: watch_count})
            count += 1
        return count

    def ingest_languages(self, limit=2000):
        filepath = dataset_path("languages")
        count = 0
        for record in load_jsonl(filepath, limit=limit):
            for lang in record.get("language", []) or []:
                name = lang.get("name")
                byte_count = lang.get("bytes")
                if not name or byte_count is None:
                    continue
                try:
                    byte_count = int(byte_count)
                except ValueError:
                    continue
                self.client.zincrby("languages:bytes", byte_count, name)
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
            license_name = record.get("license")
            if not license_name:
                continue
            self.client.hincrby("licenses:count", license_name, 1)
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
        key = f"commit:{sha}"
        if self.client.exists(key):
            return False
        self.client.hset(
            key,
            mapping={
                "repo_name": repo_name,
                "author_name": author_name,
                "author_email": author_email,
                "message": message,
            },
        )
        return True

    def read_commit(self, sha):
        key = f"commit:{sha}"
        if not self.client.exists(key):
            return None
        return self.client.hgetall(key)

    def update_commit(self, sha, field, value):
        key = f"commit:{sha}"
        if not self.client.exists(key):
            return False
        self.client.hset(key, field, value)
        return True

    def delete_commit(self, sha):
        key = f"commit:{sha}"
        return self.client.delete(key) > 0

    def list_commit_keys(self, limit=20):
        keys = []
        for key in self.client.scan_iter(match="commit:*", count=100):
            keys.append(key)
            if len(keys) >= limit:
                break
        return keys

    # ---------- features ----------

    # feature 1: top languages by total bytes across ingested repos
    def feature_top_languages(self, top_n=10):
        results = self.client.zrevrange("languages:bytes", 0, top_n - 1, withscores=True)
        return [(name, int(score)) for name, score in results]

    # feature 2: top repos by watch count
    def feature_top_repos_by_watch(self, top_n=10):
        results = self.client.zrevrange("leaderboard:watch_count", 0, top_n - 1, withscores=True)
        return [(name, int(score)) for name, score in results]

    # feature 3: license distribution, returns (name, count, pct) tuples
    def feature_license_distribution(self):
        counts = self.client.hgetall("licenses:count")
        total = sum(int(c) for c in counts.values()) or 1
        sorted_counts = sorted(counts.items(), key=lambda item: int(item[1]), reverse=True)
        return [
            (name, int(count), round(int(count) / total * 100, 1))
            for name, count in sorted_counts
        ]

    # wipes everything this app wrote to redis, for resetting between demo runs
    def flush_all(self):
        self.client.flushdb()
