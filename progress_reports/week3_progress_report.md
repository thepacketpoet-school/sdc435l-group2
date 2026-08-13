# Week 3 Progress Report

## Application Description

This Python application will integrate five different databases over the five weeks of the project. This report covers Week 3, which focuses on Cassandra. The Cassandra portion was added to the same shared menu and continues to use the shared data-loading file from the previous weeks. This keeps each database as part of one application instead of creating separate programs for each week.

## Features Implemented This Week

Data ingestion: reads records from the GitHub Archive dataset and loads the data into Cassandra. The Cassandra portion uses Commits.json, Sample_Repos.json, and Languages.json.

CRUD: create, read, update, and delete operations were added for commit records stored in Cassandra. Commit SHA is used to identify individual commit records.

Three features:

1. Top repositories by watch count using the repository data stored in Cassandra.
2. Top programming languages by total bytes using the language data from the GitHub Archive.
3. Repositories with the highest number of commits based on the commit data stored in Cassandra.

The Cassandra portion also includes an option to list stored commit records and a flush/reset option for clearing the Cassandra tables when testing the application.

## Next Goals / Future Plans

* Continue testing the Cassandra portion of the application to make sure the CRUD operations and three features work correctly with the GitHub Archive data.
* Make sure the Cassandra portion works correctly when it is merged with the main project branch.
* Keep the shared menu and data loader working for the remaining Neo4j and SQLite portions of the project.
* Continue updating the README with the dependencies, setup requirements, and features added to the application.

## Issues / Notes

* Cassandra requires both the Cassandra server and the Python Cassandra driver to be installed before the application can connect to the database.
* The GitHub Archive files must be placed in the project's `data/` folder before the ingestion feature can run. During testing, the application returned a FileNotFoundError when Commits.json was not available in the expected folder.
* Some of the GitHub Archive files are very large, so the application only loads a limited number of records instead of loading the entire dataset into memory.
* Cassandra handles data differently from Redis and MongoDB, so tables and queries were set up around the data that the application needs to retrieve.