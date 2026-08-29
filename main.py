# main.py
# Entry point for the app. This is the menu that routes to whichever
# database's module is done. Weeks 2-5 are stubbed out in db/ for now
# and get wired in here as each one gets built, so we end up with one
# app instead of five separate scripts.

from db.redis_db import RedisManager
from db.mongo_db import MongoManager
from db.cassandra_db import CassandraManager
from db.neo4j_db import Neo4jManager
from db.sqlite_db import SQLiteManager

def print_header(title):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def redis_menu():
    """Week 1: Redis Integration menu."""
    manager = RedisManager()

    if not manager.ping():
        print("\nCould not connect to Redis. Make sure a Redis server is")
        print("running locally (default: localhost:6379) and try again.")
        return

    while True:
        print_header("Redis Menu (Week 1)")
        print("1. Ingest sample data from GitHub Archive")
        print("2. CRUD: Create a commit record")
        print("3. CRUD: Read a commit record")
        print("4. CRUD: Update a commit record")
        print("5. CRUD: Delete a commit record")
        print("6. CRUD: List stored commit keys")
        print("7. Feature: Top programming languages by bytes")
        print("8. Feature: Top repos by watch count")
        print("9. Feature: License distribution")
        print("10. Flush all Redis data (reset)")
        print("0. Back to main menu")

        choice = input("Select an option: ").strip()

        if choice == "1":
            print("\nIngesting data (this samples a subset, not the full files)...")
            results = manager.ingest_all()
            print(f"Ingested: {results}")

        elif choice == "2":
            sha = input("Commit SHA: ").strip()
            repo_name = input("Repo name: ").strip()
            author_name = input("Author name: ").strip()
            author_email = input("Author email: ").strip()
            message = input("Commit message: ").strip()
            created = manager.create_commit(sha, repo_name, author_name, author_email, message)
            print("Created." if created else "A commit with that SHA already exists.")

        elif choice == "3":
            sha = input("Commit SHA to read: ").strip()
            record = manager.read_commit(sha)
            print(record if record else "No commit found with that SHA.")

        elif choice == "4":
            sha = input("Commit SHA to update: ").strip()
            field = input("Field to update (repo_name/author_name/author_email/message): ").strip()
            value = input("New value: ").strip()
            updated = manager.update_commit(sha, field, value)
            print("Updated." if updated else "No commit found with that SHA.")

        elif choice == "5":
            sha = input("Commit SHA to delete: ").strip()
            deleted = manager.delete_commit(sha)
            print("Deleted." if deleted else "No commit found with that SHA.")

        elif choice == "6":
            keys = manager.list_commit_keys()
            print(f"\nShowing up to {len(keys)} commit keys:")
            for key in keys:
                print(f"  {key}")

        elif choice == "7":
            top = manager.feature_top_languages()
            print("\nTop languages by total bytes:")
            for name, total_bytes in top:
                print(f"  {name}: {total_bytes:,} bytes")

        elif choice == "8":
            top = manager.feature_top_repos_by_watch()
            print("\nTop repos by watch count:")
            for name, watch_count in top:
                print(f"  {name}: {watch_count:,} watchers")

        elif choice == "9":
            dist = manager.feature_license_distribution()
            print("\nLicense distribution:")
            for name, count, pct in dist:
                print(f"  {name}: {count} repos ({pct}%)")

        elif choice == "10":
            confirm = input("This will delete all Redis data for this app. Type 'yes' to confirm: ")
            if confirm.strip().lower() == "yes":
                manager.flush_all()
                print("Redis data cleared.")

        elif choice == "0":
            break

        else:
            print("Not a valid option, try again.")

def mongo_menu():
    """Week 2: MongoDB Integration menu."""
    # In the name of uniformity, I tried to make this as similar to the redis
    # menu as I could - Signy
    manager = MongoManager()

    if not manager.ping():
        print("\nCould not connect to MongoDB. Make sure a MongoDB server is")
        print("running locally (default: localhost:27017) and try again.")
        return

    while True:
        print_header("MongoDB Menu (Week 2)")
        print("1. Ingest sample data from GitHub Archive")
        print("2. CRUD: Create a commit record")
        print("3. CRUD: Read a commit record")
        print("4. CRUD: Update a commit record")
        print("5. CRUD: Delete a commit record")
        print("6. CRUD: List stored commit keys")
        print("7. Feature: Longest and shortest repo Names")
        print("8. Feature: Top repos by watch count")
        print("9. Feature: Most popular commit messages")
        print("10. Flush all MongoDB data (reset)")
        print("0. Back to main menu")

        choice = input("Select an option: ").strip()

        if choice == "1":
            print("\nIngesting data (this samples a subset, not the full files)...")
            results = manager.ingest_all()
            print(f"Ingested: {results}")

        elif choice == "2":
            sha = input("Commit SHA: ").strip()
            repo_name = input("Repo name: ").strip()
            author_name = input("Author name: ").strip()
            author_email = input("Author email: ").strip()
            message = input("Commit message: ").strip()
            created = manager.create_commit(sha, repo_name, author_name, author_email, message)
            print("Created." if created else "A commit with that SHA already exists.")

        elif choice == "3":
            sha = input("Commit SHA to read: ").strip()
            record = manager.read_commit(sha)
            print(record if record else "No commit found with that SHA.")

        elif choice == "4":
            sha = input("Commit SHA to update: ").strip()
            field = input("Field to update (repo_name/author_name/author_email/message): ").strip()
            value = input("New value: ").strip()
            updated = manager.update_commit(sha, field, value)
            print("Updated." if updated else "No commit found with that SHA.")

        elif choice == "5":
            sha = input("Commit SHA to delete: ").strip()
            deleted = manager.delete_commit(sha)
            print("Deleted." if deleted else "No commit found with that SHA.")

        elif choice == "6":
            keys = manager.list_commit_keys()
            print(f"\nShowing up to {len(keys)} commit keys:")
            for key in keys:
                print(f"  {key}")

        elif choice == "7":
            print("Printing the longest and the shortest repo name:")
            manager.find_longest_shortest()


        elif choice == "8":
            print("Printing repos in descending order of watch count:")
            watchResult = manager.top_repos_by_watch()
            for doc in watchResult:
                print(doc)
        elif choice == "9":
            print("Printing the most common comments on github commits")
            com = manager.popular_comments()
            for doc in com:
                 print(doc)

        elif choice == "10":
            confirm = input("This will delete all MongoDB data for this app. Type 'yes' to confirm: ")
            if confirm.strip().lower() == "yes":
                manager.flush_all()
                print("MongoDB data cleared.")

        elif choice == "0":
            break

        else:
            print("Not a valid option, try again.")
            
def cassandra_menu():
    """Week 3: Cassandra Integration menu."""

    try:
        manager = CassandraManager()
    except Exception as error:
        print("\nCould not connect to Cassandra.")
        print("Make sure Cassandra is running on localhost:9042.")
        print(f"Error: {error}")
        return

    if not manager.ping():
        print("\nCould not connect to Cassandra.")
        return

    while True:
        print_header("Cassandra Menu (Week 3)")
        print("1. Ingest sample data from GitHub Archive")
        print("2. CRUD: Create a commit record")
        print("3. CRUD: Read a commit record")
        print("4. CRUD: Update a commit record")
        print("5. CRUD: Delete a commit record")
        print("6. CRUD: List stored commit keys")
        print("7. Feature: Top repositories by watch count")
        print("8. Feature: Top programming languages by bytes")
        print("9. Feature: Commit count by repository")
        print("10. Flush all Cassandra data (reset)")
        print("0. Back to main menu")

        choice = input("Select an option: ").strip()

        if choice == "1":
            print("\nIngesting GitHub Archive data...")
            results = manager.ingest_all()
            print(f"Ingested: {results}")

        elif choice == "2":
            sha = input("Commit SHA: ").strip()
            repo_name = input("Repo name: ").strip()
            author_name = input("Author name: ").strip()
            author_email = input("Author email: ").strip()
            message = input("Commit message: ").strip()

            created = manager.create_commit(
                sha,
                repo_name,
                author_name,
                author_email,
                message,
            )

            print(
                "Created."
                if created
                else "A commit with that SHA already exists."
            )

        elif choice == "3":
            sha = input("Commit SHA to read: ").strip()

            record = manager.read_commit(sha)

            print(
                record
                if record
                else "No commit found with that SHA."
            )

        elif choice == "4":
            sha = input("Commit SHA to update: ").strip()

            field = input(
                "Field to update "
                "(repo_name/author_name/author_email/message): "
            ).strip()

            value = input("New value: ").strip()

            updated = manager.update_commit(
                sha,
                field,
                value,
            )

            print(
                "Updated."
                if updated
                else "Commit or field was not found."
            )

        elif choice == "5":
            sha = input("Commit SHA to delete: ").strip()

            deleted = manager.delete_commit(sha)

            print(
                "Deleted."
                if deleted
                else "No commit found with that SHA."
            )

        elif choice == "6":
            keys = manager.list_commit_keys()

            print(f"\nShowing up to {len(keys)} commit keys:")

            for key in keys:
                print(f"  {key}")

        elif choice == "7":
            repos = manager.feature_top_repos()

            print("\nTop repositories by watch count:")

            for repo, watches in repos:
                print(f"  {repo}: {watches:,} watchers")

        elif choice == "8":
            languages = manager.feature_top_languages()

            print("\nTop programming languages by bytes:")

            for language, total_bytes in languages:
                print(
                    f"  {language}: "
                    f"{total_bytes:,} bytes"
                )

        elif choice == "9":
            repos = manager.feature_commit_count_by_repo()

            print("\nRepositories with the most commits:")

            for repo, count in repos:
                print(f"  {repo}: {count} commits")

        elif choice == "10":
            confirm = input(
                "This will delete all Cassandra data for this app. "
                "Type 'yes' to confirm: "
            )

            if confirm.strip().lower() == "yes":
                manager.flush_all()
                print("Cassandra data cleared.")

        elif choice == "0":
            manager.close()
            break

        else:
            print("Not a valid option, try again.")

def neo4j_menu():
    #Week 4 Neo4j integration

    manager = Neo4jManager()
    if not manager:
        print("\nCould not connect to Neo4j.")
        print("Make sure Neo4j is running locally! (Default: localhost:7687)")
        return
    
    print_header("Neo4j Menu (Week 4)")
    print("1. Ingest sample data from GitHub Archive")
    print("2. CRUD: Create a commit record")
    print("3. CRUD: Read a commit record")
    print("4. CRUD: Update a commit record")
    print("5. CRUD: Delete a commit record")
    print("6. Feature: List top 10 repos by distinct author count")
    print("7. Feature: List repos with shared contributors")
    print("8. Feature: List repos grouped by shared programming language")
    print("9. Flush all Neo4j data (reset)")
    print("0. Back to main menu")

    choice = input("Select an option: ").strip()

    if choice == "1":
        print("Ingesting sample data from the archive...")
        ingested = manager.ingest_all()
        if ingested:
            print("Done.")
        else:
            return
        
    elif choice == "2":
        sha = input("Commit SHA: ").strip()
        repo_name = input("Repo name: ").strip()
        author_name = input("Author name: ").strip()
        author_email = input("Author email: ").strip()
        message = input("Commit message: ").strip()
        created = manager.create_commit(sha, repo_name, author_name, author_email, message)
        print("Created."
            if created
            else
            "A commit with that SHA already exists.")
              
    elif choice == "3":
        sha = input("Commit SHA to read: ").strip()
        record = manager.read_commit(sha)
        print(record
            if record
            else "No commit found with that SHA.")
            
    elif choice == "4":
        sha = input("Commit SHA to update: ").strip()
        value = input("New value (message): ").strip()
        field = "message"
        updated = manager.update_commit(sha, field, value)
        print("Updated."
            if updated
            else "Commit or field was not found.")

    elif choice == "5":
        sha = input("Commit SHA to delete: ").strip()
        deleted = manager.delete_commit(sha)
        print("Deleted."
            if deleted
            else "No commit found with that SHA.")

    elif choice == "6":
        top_repos = manager.top_repos_by_author_count()
        print("\nTop repos by distinct author count: ")
        for repo in top_repos:
            print(repo)

    elif choice == "7":
        shared_repos = manager.repos_with_shared_contributors()
        print("\nRepos with shared contributors: ")
        for repo in shared_repos:
            print(repo)

    elif choice == "8":
        language = input("\nGroup by which language? : ").strip()
        repos_by_lang = manager.repos_by_language(language)
        print(f"\nRepos grouped by shared programming language '{language}': ")
        for repo in repos_by_lang:
            print(repo)

    elif choice == "9":
        confirm = input("Are you sure you want to delete all Neo4j data? (Y/N): ")
        if confirm.strip().upper() == "Y":
            manager.flush_all()
            print("Neo4j data deleted.")

    elif choice == "0":
        manager.close()

    else:
        print("Invlaid option. Try again.")
        
def sqlite_menu():
    """Week 5: SQLite integration menu."""
    manager = SQLiteManager()

    while True:
        print("\n" + "=" * 50)
        print("SQLite Menu (Week 5)")
        print("=" * 50)
        print("1. Ingest sample data from GitHub Archive")
        print("2. CRUD: Create a commit record")
        print("3. CRUD: Read a commit record")
        print("4. CRUD: Update a commit record")
        print("5. CRUD: Delete a commit record")
        print("6. Feature: Top repos by watch count (with license)")
        print("7. Feature: Repos with the most unique languages")
        print("8. Feature: Average committers per repo")
        print("9. Flush all SQLite data (reset)")
        print("0. Back to main menu")

        choice = input("Select an option: ").strip()

        if choice == "1":
            print("Ingesting sample data from the archive...")
            ingested = manager.ingest_all()
            print(f"Ingested: {ingested}")

        elif choice == "2":
            sha = input("Commit SHA: ").strip()
            repo_name = input("Repo name: ").strip()
            author_name = input("Author name: ").strip()
            author_email = input("Author email: ").strip()
            message = input("Commit message: ").strip()
            created = manager.create_commit(sha, repo_name, author_name, author_email, message)
            print("Commit created." if created else "A commit with that SHA already exists.")

        elif choice == "3":
            sha = input("Commit SHA to look up: ").strip()
            result = manager.read_commit(sha)
            print(result if result else "No commit found with that SHA.")

        elif choice == "4":
            sha = input("Commit SHA to update: ").strip()
            print("Editable fields: message, author_name, author_email")
            field = input("Field to update: ").strip()
            value = input("New value: ").strip()
            updated = manager.update_commit(sha, field, value)
            print("Commit updated." if updated else "Update failed, check the SHA and field name.")

        elif choice == "5":
            sha = input("Commit SHA to delete: ").strip()
            deleted = manager.delete_commit(sha)
            print("Commit deleted." if deleted else "No commit found with that SHA.")

        elif choice == "6":
            print("\nTop repos by watch count:")
            for repo_name, watch_count, license_name in manager.top_repos_with_license():
                print(f"  {repo_name} - {watch_count} watches - license: {license_name}")

        elif choice == "7":
            print("\nRepos with the most unique languages:")
            for repo_name, language_count in manager.repos_by_unique_language_count():
                print(f"  {repo_name} - {language_count} unique language(s)")

        elif choice == "8":
            avg = manager.average_committers_per_repo()
            print(f"\nAverage distinct committers per repo: {avg:.2f}" if avg else "No commit data ingested yet.")

        elif choice == "9":
            confirm = input("This will delete all SQLite data for this app. Type 'yes' to confirm: ")
            if confirm.strip().lower() == "yes":
                manager.flush_all()
                print("SQLite data cleared.")
            else:
                print("Cancelled.")

        elif choice == "0":
            manager.close()
            break

        else:
            print("Invalid option.")


def main_menu():
    while True:
        print_header("GitHub Archive Data Analysis")
        print("1. Redis (Week 1)")
        print("2. MongoDB (Week 2)")
        print("3. Cassandra (Week 3)")
        print("4. Neo4j (Week 4)")
        print("5. SQLite (Week 5)")
        print("0. Exit")

        choice = input("Select a database to work with: ").strip()

        if choice == "1":
            redis_menu()
        elif choice == "2":
            mongo_menu()
        elif choice == "3":
            cassandra_menu()
        elif choice == "4":
            neo4j_menu()
        elif choice == "5":
            sqlite_menu()
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Not a valid option, try again.")


if __name__ == "__main__":
    main_menu()
