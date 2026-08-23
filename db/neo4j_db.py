# neo4j_db.py
# Week 4 - Neo4j integration.
# Follows the same pattern as redis_db.py/mongo_db.py: connect, ingest from
# utils/data_loader.py, CRUD, 3 features.

import os
import sys

from neo4j import GraphDatabase as gDB

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import load_jsonl, dataset_path

class Neo4jManager:
    def __init__(self, uri="neo4j://localhost:7687", user="neo4j", password="password1"):
        # Connect to Neo4j
        self.driver = gDB.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    # ---------- ingestion ----------
    # Nodes: Commit, Author, Repo, Language, License
    # Relationships: (Author)-[:AUTHORED]->(Commit)-[:IN_REPO]->(Repo)
    #                (Repo)-[:WRITTEN_IN]->(Language)
    #                (Repo)-[:LICENSED_UNDER]->(License)
    #
    # Repo/Author/Language/License all use MERGE instead of CREATE, since the
    # same repo (or author, language, license) shows up across multiple files
    # and multiple records. MERGE checks whether a node with that property
    # already exists first, reuses it if so, and only creates a new one if it
    # doesn't. That keeps us from ending up with duplicate nodes for the same
    # repo every time it's referenced again in a different file.
    #
    # Commit nodes use CREATE instead, since each commit sha is unique to
    # begin with, there's nothing to merge against.

    def ingest_commits(self, limit=500):
        filepath = dataset_path("commits")
        count = 0
        with self.driver.session() as session:
            for record in load_jsonl(filepath, limit=limit):
                query = """
                    MERGE (a:Author {name: $author_name, email: $author_email})
                    MERGE (r:Repo {name: $repo_name})
                    CREATE (c:Commit {sha: $sha, message: $message})
                    CREATE (a)-[:AUTHORED]->(c)
                    CREATE (c)-[:IN_REPO]->(r)
                    """
                session.run(query,
                    sha=record["commit"],
                    message=record.get("message", ""),
                    author_name=record.get("author_name", "unknown"),
                    author_email=record.get("author_email", "unknown"),
                    repo_name=record["repo_name"])
                count += 1
        return count

    def ingest_repos(self, limit=2000):
        filepath = dataset_path("sample_repos")
        count = 0
        with self.driver.session() as session:
            for record in load_jsonl(filepath, limit=limit):
                query = """
                    MERGE (r:Repo {name: $repo_name})
                    SET r.watch_count = $watch_count
                    """
                session.run(query,
                    repo_name=record["repo_name"],
                    watch_count=record.get("watch_count", 0))
                count += 1
        return count

    def ingest_languages(self, limit=2000):
        filepath = dataset_path("languages")
        count = 0
        with self.driver.session() as session:
            for record in load_jsonl(filepath, limit=limit):
                repo_name = record["repo_name"]
                languages = record.get("language", [])

                # language is a list of {name, bytes} objects, since a repo
                # can be written in more than one language
                if isinstance(languages, dict):
                    languages = [languages]  # handle a stray single-object case defensively

                for lang in languages:
                    language_name = lang.get("name", "unknown")
                    language_bytes = lang.get("bytes")

                    query = """
                        MERGE (r:Repo {name: $repo_name})
                        MERGE (l:Language {name: $language})
                        MERGE (r)-[rel:WRITTEN_IN]->(l)
                        SET rel.bytes = $bytes
                        """
                    session.run(query,
                        repo_name=repo_name,
                        language=language_name,
                        bytes=language_bytes)

                count += 1
        return count

    def ingest_licenses(self, limit=None):
        filepath = dataset_path("licenses")
        count = 0
        with self.driver.session() as session:
            for record in load_jsonl(filepath, limit=limit):
                query = """
                    MERGE (r:Repo {name: $repo_name})
                    MERGE (lic:License {name: $license})
                    MERGE (r)-[:LICENSED_UNDER]->(lic)
                    """
                session.run(query,
                    repo_name=record["repo_name"],
                    license=record.get("license", "unknown"))
                count += 1
        return count

    def ingest_all(self, commit_limit=500, repo_limit=2000, language_limit=2000, license_limit=None):
        return {
            "commits": self.ingest_commits(commit_limit),
            "repos": self.ingest_repos(repo_limit),
            "languages": self.ingest_languages(language_limit),
            "licenses": self.ingest_licenses(license_limit),
        }

    # ---------- CRUD on Commit nodes ----------

    def create_commit(self, sha, repo_name, author_name, author_email, message):
        with self.driver.session() as session:
            existing = session.run("MATCH (c:Commit {sha: $sha}) RETURN c", sha=sha).single()
            if existing is not None:
                return False
            query = """
                MERGE (a:Author {name: $author_name, email: $author_email})
                MERGE (r:Repo {name: $repo_name})
                CREATE (c:Commit {sha: $sha, message: $message})
                CREATE (a)-[:AUTHORED]->(c)
                CREATE (c)-[:IN_REPO]->(r)
                """
            session.run(query, sha=sha, message=message,
                author_name=author_name, author_email=author_email, repo_name=repo_name)
            return True

    def read_commit(self, sha):
        with self.driver.session() as session:
            query = """
                MATCH (a:Author)-[:AUTHORED]->(c:Commit {sha: $sha})-[:IN_REPO]->(r:Repo)
                RETURN c.sha AS sha, c.message AS message,
                       a.name AS author_name, r.name AS repo_name
                """
            result = session.run(query, sha=sha).single()
            return dict(result) if result else None

    def update_commit(self, sha, field, value):
        # only allow updating fields that actually live on the Commit node
        allowed_fields = ["message"]
        if field not in allowed_fields:
            return False
        with self.driver.session() as session:
            query = f"MATCH (c:Commit {{sha: $sha}}) SET c.{field} = $value RETURN c"
            result = session.run(query, sha=sha, value=value).single()
            return result is not None

    def delete_commit(self, sha):
        with self.driver.session() as session:
            query = "MATCH (c:Commit {sha: $sha}) DETACH DELETE c"
            session.run(query, sha=sha)

    # ---------- features ----------

    # feature 1: collaboration patterns - repos with the most distinct authors
    def top_repos_by_author_count(self, limit=10):
        with self.driver.session() as session:
            query = """
                MATCH (a:Author)-[:AUTHORED]->(:Commit)-[:IN_REPO]->(r:Repo)
                RETURN r.name AS repo, count(DISTINCT a) AS author_count
                ORDER BY author_count DESC
                LIMIT $limit
                """
            return [dict(record) for record in session.run(query, limit=limit)]

    # feature 2: repos that share common contributors
    def repos_with_shared_contributors(self, limit=10):
        with self.driver.session() as session:
            query = """
                MATCH (r1:Repo)<-[:IN_REPO]-(:Commit)<-[:AUTHORED]-(a:Author)
                      -[:AUTHORED]->(:Commit)-[:IN_REPO]->(r2:Repo)
                WHERE r1.name < r2.name
                RETURN r1.name AS repo_a, r2.name AS repo_b,
                       count(DISTINCT a) AS shared_authors
                ORDER BY shared_authors DESC
                LIMIT $limit
                """
            return [dict(record) for record in session.run(query, limit=limit)]

    # feature 3: repos grouped by shared programming language
    def repos_by_language(self, language, limit=10):
        with self.driver.session() as session:
            query = """
                MATCH (r:Repo)-[:WRITTEN_IN]->(l:Language {name: $language})
                RETURN r.name AS repo, r.watch_count AS watch_count
                ORDER BY watch_count DESC
                LIMIT $limit
                """
            return [dict(record) for record in session.run(query, language=language, limit=limit)]

    # wipes everything this app wrote to Neo4j, for resetting between demo runs
    def flush_all(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
