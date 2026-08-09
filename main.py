# main.py
# Entry point for the app. This is the menu that routes to whichever
# database's module is done. Weeks 2-5 are stubbed out in db/ for now
# and get wired in here as each one gets built, so we end up with one
# app instead of five separate scripts.

from db.redis_db import RedisManager
from db.mongo_db import MongoManager


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
            
def not_yet_available(week_name):
    print(f"\n{week_name} isn't implemented yet. Check back in a future week!")


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
            not_yet_available("Cassandra")
        elif choice == "4":
            not_yet_available("Neo4j")
        elif choice == "5":
            not_yet_available("SQLite")
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Not a valid option, try again.")


if __name__ == "__main__":
    main_menu()
