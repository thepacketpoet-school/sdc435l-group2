# cassandra_db.py
# Week 3 - Cassandra integration.
# Follows the same pattern as redis_db.py and mongo_db.py:
# connect, ingest from utils/data_loader.py, CRUD, and 3 features.

import os
import sys

from cassandra.cluster import Cluster

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_jsonl, dataset_path


class CassandraManager:

    def __init__(self, host="127.0.0.1", port=9042):
        # Connect to Cassandra
        self.cluster = Cluster([host], port=port)
        self.session = self.cluster.connect()

        # Create the keyspace if it does not already exist
        self.session.execute("""
            CREATE KEYSPACE IF NOT EXISTS github_archive
            WITH replication = {
                'class': 'SimpleStrategy',
                'replication_factor': 1
            }
        """)

        # Connect to the keyspace
        self.session.set_keyspace("github_archive")

        # Create tables
        self.create_tables()

    def create_tables(self):
        """Create the Cassandra tables needed by the application."""

        # Commit records
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS commits (
                commit_sha text PRIMARY KEY,
                repo_name text,
                author_name text,
                author_email text,
                message text
            )
        """)

        # Repository information
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS repositories (
                repo_name text PRIMARY KEY,
                watch_count int
            )
        """)

        # Programming language information
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS languages (
                repo_name text,
                language text,
                bytes bigint,
                PRIMARY KEY (repo_name, language)
            )
        """)

    def ping(self):
        """Check whether the Cassandra server is available."""

        try:
            self.session.execute(
                "SELECT release_version FROM system.local"
            )
            return True

        except Exception:
            return False

    # --------------------------------------------------
    # Ingestion
    # --------------------------------------------------

    def ingest_commits(self, limit=500):
        """Read GitHub Archive commit data and store it in Cassandra."""

        filepath = dataset_path("commits")
        count = 0

        insert_query = """
            INSERT INTO commits
            (
                commit_sha,
                repo_name,
                author_name,
                author_email,
                message
            )
            VALUES (%s, %s, %s, %s, %s)
        """

        for record in load_jsonl(filepath, limit=limit):

            sha = record.get("commit")

            # Skip records that do not have a commit SHA
            if not sha:
                continue

            # repo_name appears as a list in the GitHub Archive data
            repo_names = record.get("repo_name", [])

            if repo_names:
                repo_name = repo_names[0]
            else:
                repo_name = "unknown"

            # Get author information
            author = record.get("author", {}) or {}

            author_name = author.get("name", "unknown")
            author_email = author.get("email", "unknown")

            # Commit message
            message = (record.get("subject") or "").strip()

            self.session.execute(
                insert_query,
                (
                    sha,
                    repo_name,
                    author_name,
                    author_email,
                    message
                )
            )

            count += 1

        return count

    def ingest_repos(self, limit=2000):
        """Read repository data and store it in Cassandra."""

        filepath = dataset_path("sample_repos")
        count = 0

        insert_query = """
            INSERT INTO repositories
            (repo_name, watch_count)
            VALUES (%s, %s)
        """

        for record in load_jsonl(filepath, limit=limit):

            repo_name = record.get("repo_name")
            watch_count = record.get("watch_count")

            if not repo_name or watch_count is None:
                continue

            try:
                watch_count = int(watch_count)

            except (ValueError, TypeError):
                continue

            self.session.execute(
                insert_query,
                (
                    repo_name,
                    watch_count
                )
            )

            count += 1

        return count

    def ingest_languages(self, limit=2000):
        """Read programming language data and store it in Cassandra."""

        filepath = dataset_path("languages")
        count = 0

        insert_query = """
            INSERT INTO languages
            (repo_name, language, bytes)
            VALUES (%s, %s, %s)
        """

        for record in load_jsonl(filepath, limit=limit):

            repo_names = record.get("repo_name", [])

            if repo_names:
                repo_name = repo_names[0]
            else:
                repo_name = "unknown"

            languages = record.get("language", []) or []

            for lang in languages:

                language_name = lang.get("name")
                byte_count = lang.get("bytes")

                if not language_name or byte_count is None:
                    continue

                try:
                    byte_count = int(byte_count)

                except (ValueError, TypeError):
                    continue

                self.session.execute(
                    insert_query,
                    (
                        repo_name,
                        language_name,
                        byte_count
                    )
                )

                count += 1

        return count

    def ingest_all(
        self,
        commit_limit=500,
        repo_limit=2000,
        language_limit=2000
    ):
        """Load all required GitHub Archive datasets."""

        return {
            "commits": self.ingest_commits(commit_limit),
            "repos": self.ingest_repos(repo_limit),
            "languages": self.ingest_languages(language_limit)
        }

    # --------------------------------------------------
    # CRUD Operations
    # --------------------------------------------------

    def create_commit(
        self,
        sha,
        repo_name,
        author_name,
        author_email,
        message
    ):
        """Create a new commit record."""

        # Check whether the commit already exists
        existing = self.read_commit(sha)

        if existing is not None:
            return False

        query = """
            INSERT INTO commits
            (
                commit_sha,
                repo_name,
                author_name,
                author_email,
                message
            )
            VALUES (%s, %s, %s, %s, %s)
        """

        self.session.execute(
            query,
            (
                sha,
                repo_name,
                author_name,
                author_email,
                message
            )
        )

        return True

    def read_commit(self, sha):
        """Read one commit record using its SHA."""

        query = """
            SELECT
                commit_sha,
                repo_name,
                author_name,
                author_email,
                message
            FROM commits
            WHERE commit_sha = %s
        """

        result = self.session.execute(
            query,
            (sha,)
        ).one()

        if result is None:
            return None

        return {
            "commit": result.commit_sha,
            "repo_name": result.repo_name,
            "author_name": result.author_name,
            "author_email": result.author_email,
            "message": result.message
        }

    def update_commit(self, sha, field, value):
        """Update one field in an existing commit."""

        allowed_fields = [
            "repo_name",
            "author_name",
            "author_email",
            "message"
        ]

        # Prevent invalid fields from being used
        if field not in allowed_fields:
            return False

        # Check whether the commit exists
        if self.read_commit(sha) is None:
            return False

        query = f"""
            UPDATE commits
            SET {field} = %s
            WHERE commit_sha = %s
        """

        self.session.execute(
            query,
            (
                value,
                sha
            )
        )

        return True

    def delete_commit(self, sha):
        """Delete a commit record."""

        # Check first so we can return False if it does not exist
        if self.read_commit(sha) is None:
            return False

        self.session.execute(
            """
            DELETE FROM commits
            WHERE commit_sha = %s
            """,
            (sha,)
        )

        return True

    def list_commit_keys(self, limit=20):
        """Return a list of commit SHAs."""

        query = f"""
            SELECT commit_sha
            FROM commits
            LIMIT {int(limit)}
        """

        results = self.session.execute(query)

        keys = []

        for row in results:
            keys.append(row.commit_sha)

        return keys

    # --------------------------------------------------
    # Feature 1
    # Top repositories by watch count
    # --------------------------------------------------

    def feature_top_repos_by_watch(self, top_n=10):
        """Return repositories with the highest watch count."""

        results = self.session.execute(
            """
            SELECT repo_name, watch_count
            FROM repositories
            """
        )

        repos = []

        for row in results:

            if row.watch_count is not None:
                repos.append(
                    (
                        row.repo_name,
                        row.watch_count
                    )
                )

        repos.sort(
            key=lambda item: item[1],
            reverse=True
        )

        return repos[:top_n]

    # --------------------------------------------------
    # Feature 2
    # Top programming languages by total bytes
    # --------------------------------------------------

    def feature_top_languages(self, top_n=10):
        """Return programming languages ranked by total bytes."""

        results = self.session.execute(
            """
            SELECT language, bytes
            FROM languages
            """
        )

        language_totals = {}

        for row in results:

            if row.language is None or row.bytes is None:
                continue

            if row.language not in language_totals:
                language_totals[row.language] = 0

            language_totals[row.language] += row.bytes

        sorted_languages = sorted(
            language_totals.items(),
            key=lambda item: item[1],
            reverse=True
        )

        return sorted_languages[:top_n]

    # --------------------------------------------------
    # Feature 3
    # Repositories with the most commits
    # --------------------------------------------------

    def feature_commit_count_by_repo(self, top_n=10):
        """Return repositories ranked by number of commits."""

        results = self.session.execute(
            """
            SELECT repo_name
            FROM commits
            """
        )

        repo_counts = {}

        for row in results:

            repo_name = row.repo_name

            if not repo_name:
                continue

            if repo_name not in repo_counts:
                repo_counts[repo_name] = 0

            repo_counts[repo_name] += 1

        sorted_repos = sorted(
            repo_counts.items(),
            key=lambda item: item[1],
            reverse=True
        )

        return sorted_repos[:top_n]

    # --------------------------------------------------
    # Reset Cassandra data
    # --------------------------------------------------

    def flush_all(self):
        """Remove all records from the Cassandra tables."""

        self.session.execute(
            "TRUNCATE commits"
        )

        self.session.execute(
            "TRUNCATE repositories"
        )

        self.session.execute(
            "TRUNCATE languages"
        )

    def close(self):
        """Close the Cassandra connection."""

        self.cluster.shutdown()