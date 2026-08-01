# Progress Report - Week 1: Redis Integration

## Team Members
- Haley Archer
- [Teammate 2]
- [Teammate 3]
- [Teammate 4]

## Application Description
Python app that'll end up integrating five databases over the five weeks. This report covers Week 1, the Redis part. I set it up so every week plugs into one shared menu and one shared data-loading file instead of everyone building separate scripts, since the assignment wants a single integrated app by the end.

## Features Implemented This Week

Data ingestion: reads records from the GitHub Archive dataset (Commits.json, Sample_Repos.json, Languages.json, Licenses.json) and loads a sample into Redis.

CRUD: create, read, update, delete on commit records, stored as Redis hashes keyed by commit SHA.

Three features:
1. Top programming languages by total bytes, using a Redis sorted set (ZINCRBY/ZREVRANGE)
2. Top repos by watch count, sorted set used as a leaderboard
3. License distribution with percentages, using a Redis hash as a running count (HINCRBY)

## Next Goals / Future Plans
- Get the rest of the team set up on the repo and branch workflow before Week 2 starts
- Confirm who's taking Week 2 (MongoDB) and get them added as a collaborator
- Think about whether the commit data model from this week should carry over into how we structure MongoDB documents, since it's the same underlying dataset

## Issues / Notes
- A couple of the dataset files are huge (Languages.json is 400+ MB), so the app samples a limited number of records instead of loading everything. Keeps things fast while we're building and testing.
- Licenses.json only has two license values in the whole file (isc and artistic-2.0), so the license feature only shows two categories. That's just what's in the data, not a bug.
