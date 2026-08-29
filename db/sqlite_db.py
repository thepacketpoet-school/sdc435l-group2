# sqlite_db.py
# Week 5 - SQLite integration.
# Follows the same pattern as redis_db.py/mongo_db.py/cassandra_db.py/neo4j_db.py:
# connect, ingest from utils/data_loader.py, CRUD, 3 features.
#
# Unlike the other four weeks, SQLite is relational, so this is the one
# integration in the project that can use real foreign keys and JOINs
# instead of a NoSQL access pattern. Tables mirror the same commit/repo/
# language/license data model the rest of the app has used all along,
# which was actually something flagged as worth revisiting back in the
# Week 1 progress report notes.

import os
import sys
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_jsonl, dataset_path


class SQLiteManager:
    def __init__(self, db_path="github_archive.db"):
        # Connect to (or create) the local SQLite database file
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._create_tables()

    def close(self):
        self.conn.close()

    def _create_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS repos (
                repo_name TEXT PRIMARY KEY,
                watch_count INTEGER
            );
            """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS commits (
                sha TEXT PRIMARY KEY,
                repo_name TEXT,
                author_name TEXT,
                author_email TEXT,
                message TEXT,
                FOREIGN KEY (repo_name) REFERENCES repos(repo_name)
            );
            """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS languages (
                repo_name TEXT,
                language TEXT,
                bytes INTEGER,
                FOREIGN KEY (repo_name) REFERENCES repos(repo_name)
            );
            """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                repo_name TEXT,
                license TEXT,
                FOREIGN KEY (repo_name) REFERENCES repos(repo_name)
            );
            """)

        self.conn.commit()

    # ---------- ingestion ----------
    # repos get an INSERT OR IGNORE, since the same repo shows up across
    # multiple files and multiple records, and repos has to exist first
    # for the foreign keys on the other tables to be valid. commits get a
    # plain INSERT since each sha is already unique.

    def ingest_repos(self, limit=2000):
        filepath = dataset_path("sample_repos")
        cur = self.conn.cursor()
        count = 0
        for record in load_jsonl(filepath, limit=limit):
            cur.execute(
                "INSERT OR IGNORE INTO repos (repo_name, watch_count) VALUES (?, ?);",
                (record["repo_name"], record.get("watch_count", 0)))
            count += 1
        self.conn.commit()
        return count

    def ingest_commits(self, limit=500):
        filepath = dataset_path("commits")
        cur = self.conn.cursor()
        count = 0
        for record in load_jsonl(filepath, limit=limit):
            # repo_name comes back as a list, e.g. ['some/repo'], not a plain
            # string, take the first entry
            repo_field = record.get("repo_name", ["unknown"])
            if isinstance(repo_field, list) and repo_field:
                repo_name = repo_field[0]
            elif isinstance(repo_field, str):
                repo_name = repo_field
            else:
                repo_name = "unknown"

            # author info is nested under an "author" object, not flat
            # author_name/author_email fields
            author = record.get("author", {})
            author_name = author.get("name", "unknown") if isinstance(author, dict) else "unknown"
            author_email = author.get("email", "unknown") if isinstance(author, dict) else "unknown"

            cur.execute(
                "INSERT OR IGNORE INTO repos (repo_name, watch_count) VALUES (?, 0);",
                (repo_name,))
            cur.execute(
                """INSERT OR IGNORE INTO commits
                (sha, repo_name, author_name, author_email, message)
                VALUES (?, ?, ?, ?, ?);""",
                (record["commit"], repo_name, author_name, author_email,
                record.get("message", "")))
            count += 1
        self.conn.commit()
        return count

    def ingest_languages(self, limit=2000):
        filepath = dataset_path("languages")
        cur = self.conn.cursor()
        count = 0
        for record in load_jsonl(filepath, limit=limit):
            repo_name = record["repo_name"]
            languages = record.get("language", [])
            if isinstance(languages, dict):
                languages = [languages]

            cur.execute(
                "INSERT OR IGNORE INTO repos (repo_name, watch_count) VALUES (?, 0);",
                (repo_name,))

            for lang in languages:
                cur.execute(
                    "INSERT INTO languages (repo_name, language, bytes) VALUES (?, ?, ?);",
                    (repo_name, lang.get("name", "unknown"), lang.get("bytes")))
            count += 1
        self.conn.commit()
        return count

    def ingest_licenses(self, limit=None):
        filepath = dataset_path("licenses")
        cur = self.conn.cursor()
        count = 0
        for record in load_jsonl(filepath, limit=limit):
            repo_name = record["repo_name"]
            cur.execute(
                "INSERT OR IGNORE INTO repos (repo_name, watch_count) VALUES (?, 0);",
                (repo_name,))
            cur.execute(
                "INSERT INTO licenses (repo_name, license) VALUES (?, ?);",
                (repo_name, record.get("license", "unknown")))
            count += 1
        self.conn.commit()
        return count

    def ingest_all(self, repo_limit=2000, commit_limit=500, language_limit=2000, license_limit=None):
        return {
            "repos": self.ingest_repos(repo_limit),
            "commits": self.ingest_commits(commit_limit),
            "languages": self.ingest_languages(language_limit),
            "licenses": self.ingest_licenses(license_limit),
        }

    # ---------- CRUD on commit records ----------

    def create_commit(self, sha, repo_name, author_name, author_email, message):
        cur = self.conn.cursor()
        cur.execute("SELECT 1 FROM commits WHERE sha = ?;", (sha,))
        if cur.fetchone() is not None:
            return False
        cur.execute(
            "INSERT OR IGNORE INTO repos (repo_name, watch_count) VALUES (?, 0);",
            (repo_name,))
        cur.execute(
            """INSERT INTO commits (sha, repo_name, author_name, author_email, message)
               VALUES (?, ?, ?, ?, ?);""",
            (sha, repo_name, author_name, author_email, message))
        self.conn.commit()
        return True

    def read_commit(self, sha):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT sha, repo_name, author_name, author_email, message FROM commits WHERE sha = ?;",
            (sha,))
        row = cur.fetchone()
        if row is None:
            return None
        return {"sha": row[0], "repo_name": row[1], "author_name": row[2],
                "author_email": row[3], "message": row[4]}

    def update_commit(self, sha, field, value):
        # only allow updating fields that actually live on the commits table
        allowed_fields = ["message", "author_name", "author_email"]
        if field not in allowed_fields:
            return False
        cur = self.conn.cursor()
        cur.execute(f"UPDATE commits SET {field} = ? WHERE sha = ?;", (value, sha))
        self.conn.commit()
        return cur.rowcount > 0

    def delete_commit(self, sha):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM commits WHERE sha = ?;", (sha,))
        self.conn.commit()
        return cur.rowcount > 0

    # ---------- features ----------

    # feature 1: top repos by watch count, joined with their license
    def top_repos_with_license(self, limit=10):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT r.repo_name, r.watch_count, l.license
            FROM repos r
            LEFT JOIN licenses l ON r.repo_name = l.repo_name
            ORDER BY r.watch_count DESC
            LIMIT ?;
            """, (limit,))
        return cur.fetchall()

    # feature 2: repos with the highest count of unique languages used
    def repos_by_unique_language_count(self, limit=10):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT repo_name, COUNT(DISTINCT language) AS language_count
            FROM languages
            GROUP BY repo_name
            ORDER BY language_count DESC
            LIMIT ?;
            """, (limit,))
        return cur.fetchall()

    # feature 3: average number of distinct committers (authors) per repo
    def average_committers_per_repo(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT AVG(author_count) FROM (
                SELECT repo_name, COUNT(DISTINCT author_name) AS author_count
                FROM commits
                GROUP BY repo_name
            );
            """)
        result = cur.fetchone()
        return result[0] if result else 0

    # wipes everything this app wrote to the database, for resetting between demo runs
    def flush_all(self):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM commits;")
        cur.execute("DELETE FROM languages;")
        cur.execute("DELETE FROM licenses;")
        cur.execute("DELETE FROM repos;")
        self.conn.commit()
