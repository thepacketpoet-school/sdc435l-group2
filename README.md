# GitHub Archive Data Analysis

Python app that integrates with five different databases (Redis, MongoDB,
Cassandra, Neo4j, SQLite) using data from the GitHub Archive
(https://www.gharchive.org/). One database per week, but it's all one app,
not five separate scripts, so each week plugs into the same menu.

## Structure

```
main.py                 entry point / menu
db/redis_db.py          Week 1 (done)
db/mongo_db.py           Week 2 (stub)
db/cassandra_db.py       Week 3 (stub)
db/neo4j_db.py           Week 4 (stub)
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

## Dependencies

- Python 3.9+
- redis (pip package, see requirements.txt)
- a running Redis server

## Workflow

Each week gets its own branch, e.g. week2-mongodb, merged into main via PR once it's done. Aiming for stuff being done by Saturday, if a week isn't finished someone else can pick it up Sunday since we're all working off the same repo (just continue from whatever branch is there).

Progress reports go in progress_reports/, one per week.

## Team

- Haley Archer - Week 1 (Redis), Week 5 (SQLite)
- TBD - Week 2 (MongoDB)
- TBD - Week 3 (Cassandra)
- TBD - Week 4 (Neo4j)
