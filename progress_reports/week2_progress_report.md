# Progress Report - Week 2: MongoDB Integration

## Team Members
- Haley Archer (W1, W5)
- Signy Levitt (W2)
- Dale Livingston (W3)
- Emily Gillespie (W4)

## Application Description
Python app that'll end up integrating five databases over the five weeks. This report covers Week 2, the MongoDB part. This app is set up so every week plugs into one shared menu and one shared data-loading file instead of everyone building separate scripts, since the assignment wants a single integrated app by the end.

## Features Implemented This Week

Data ingestion: reads records from the GitHub Archive dataset (Commits.json, Sample_Repos.json, Languages.json, Licenses.json) and loads a sample into MongoDB, built on the framework made from week 1.

CRUD: create, read, update, delete on commit records, stored as on a local MongoDB document database.

Three features:
1. Data report on the largest and smallest repo name, using .aggregate and $strlenCP.
2. Top repos by watch count, similar to week 1 but made to work in MongoDB.
3. Data report on most popular comments for a commit. Uses .aggregate pipleines to find unique values and counts.

## Next Goals / Future Plans
- Set up an easier way to communicate with the group. Teams, perhaps?
- Ensure we are practicing proper data safety, as to not lose valueable progress. 

## Issues / Notes
-There seems to be an issue in the mongoDB service that causes problems when the language file is read in its entirety. Given the scope of this app, I doubt it would be too much of an issue. If this were meant for a production environment, however, we would likely need to iron that out.
