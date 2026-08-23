# GitHub Archive Data Analysis

Python app that integrates with five different databases (Redis, MongoDB,
Cassandra, Neo4j, SQLite) using data from the GitHub Archive
(https://www.gharchive.org/). One database per week, but it's all one app,
not five separate scripts, so each week plugs into the same menu.

## Structure

```
main.py                 entry point / menu
db/redis_db.py          Week 1 (done)
db/mongo_db.py           Week 2 (done)
db/cassandra_db.py       Week 3 (done)
db/neo4j_db.py           Week 4 (done)
db/sqlite_db.py          Week 5 (stub)
utils/data_loader.py     shared dataset reader, use this instead of writing your own parsing
data/                    put the unzipped dataset here (gitignored)
progress_reports/        weekly reports go here
```

## Setup

1. Install deps:
```
pip install -r requirements.txt
```

2. Get the dataset from Canvas (GitHubArchive-Dataset.zip) and unzip it into `data/` so you have:
```
data/Commits.json
data/Contents.json
data/Files.json
data/Languages.json
data/Licenses.json
data/Sample_Commits.json
data/Sample_Contents.json
data/Sample_Files.json
data/Sample_Repos.json
```

Heads up, these are JSON Lines files (one JSON object per line), not a single JSON array. `utils/data_loader.py` already handles that, don't try to `json.load()` the file directly or it'll error out.

We're not committing the dataset itself to the repo since some of the files are 300+ MB, that's what the .gitignore is for.

3. Install Redis for Week 1.

Mac:
```
brew install redis
brew services start redis
```

Linux:
```
sudo apt-get update
sudo apt-get install redis-server
sudo service redis-server start
```

Windows: use WSL and follow the Linux steps, or install Memurai.

Check it's running:
```
redis-cli ping
```
should say PONG.

App connects to localhost:6379 by default. If yours is somewhere else, update the RedisManager() call in main.py.

4. Run it:
```
python3 main.py
```

## Week 1 (Redis) - what's implemented

Commits get stored as Redis hashes. Three features:
1. Top languages by total bytes across ingested repos (sorted set, ZINCRBY/ZREVRANGE)
2. Top repos by watch count (sorted set leaderboard)
3. License distribution with percentages (hash, HINCRBY)

Full CRUD on commit records through the menu, plus an ingest step and a flush/reset option.

## Week 2 (MongoDB) - what's implemented

Commits, repos, languages, and licenses get ingested from the dataset. Three features:
1. Longest and shortest repo names (aggregation with $strLenCP)
2. Top repos by watch count
3. Most common commit messages (aggregation, grouped and counted)

Full CRUD on commit records through the menu, plus an ingest step and a flush/reset option.

Install MongoDB locally if you don't have it:

Mac:
```
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

Linux/Windows: follow the official MongoDB install docs for your distro.

App connects to localhost:27017 by default.

## Week 3 (Cassandra) - what's implemented
Commits, repositories, and programming language data are ingested from the GitHub Archive dataset and stored in Cassandra. Three features:
1.	Top repositories by watch count
2.	Top programming languages by total bytes
3.	Repositories with the highest number of commits
  
Full CRUD operations for commit records are available through the menu, including creating, reading, updating, and deleting. The Cassandra menu also includes an ingest step and a flush/reset option.
Install the Cassandra Python driver:

Mac:
python3 -m pip install cassandra-driver

The application connects to Cassandra on 127.0.0.1:9042 by default.

## Week 4 (Neo4j) - what's implemented

Commits, repos, languages, and licenses get ingested from the dataset and modeled as a connected graph rather than flat records. Nodes: Commit, Author, Repo, Language, License. Relationships: (Author)-[:AUTHORED]->(Commit)-[:IN_REPO]->(Repo), (Repo)-[:WRITTEN_IN]->(Language), (Repo)-[:LICENSED_UNDER]->(License). Repo/Author/Language/License nodes use MERGE so the same repo, author, language, or license doesn't end up duplicated across records; Commit nodes use CREATE since each commit sha is already unique.

Three features:
1. Top 10 repos by distinct author count (collaboration pattern)
2. Repos that share common contributors
3. Repos grouped by shared programming language

Full CRUD on commit records through the menu, plus an ingest step and a flush/reset option.

Install the Neo4j Python driver:

Mac:
```
pip3 install neo4j
```

Neo4j itself needs to be running separately, either through Neo4j Desktop (`brew install --cask neo4j-desktop`) or a Docker container. The app connects to `neo4j://localhost:7687` by default, with credentials set in `Neo4jManager.__init__` in `db/neo4j_db.py`, update those to match whatever your local instance is actually using.

Note that ingestion here is slower than the other weeks since each record does an individual write (or, for languages, one write per language a repo uses) rather than a batched insert. A full ingest with the default limits, especially since licenses ingest the whole file uncapped, can take several minutes. Watching `MATCH (n) RETURN count(n)` in Neo4j Browser is a good way to confirm it's progressing rather than stuck.

## Dependencies

- Python 3.9+
- redis (pip package, see requirements.txt)
- pymongo (pip package, see requirements.txt)
- cassandra-driver (pip package, see requirements.txt)
- neo4j (pip package, see requirements.txt)
- a running Redis server
- a running MongoDB server
- a running Cassandra server
- a running Neo4j DBMS

## Workflow

Each week gets its own branch, e.g. week2-mongodb, merged into main via PR once it's done. Aiming for stuff being done by Saturday, if a week isn't finished someone else can pick it up Sunday since we're all working off the same repo (just continue from whatever branch is there).

Progress reports go in progress_reports/, one per week.

## Team

- Haley Archer - Week 1 (Redis), Week 5 (SQLite)
- Signy Levitt - Week 2 (MongoDB)
- Dale Livingston - Week 3 (Cassandra)
- Emily Gillespie - Week 4 (Neo4j)
