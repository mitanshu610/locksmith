"""
Database Setup and Initialization Script

This script provides utilities for setting up and initializing the catalyst AI Assistant database.
It handles database migrations using Alembic and seeds initial model configurations.

Usage:
    python startup.py --migrate  # Run database migrations
    python startup.py --all      # Run both migrations and seeding
    python startup.py            # Show help message

The script uses the same database connection handling as the main application,
ensuring consistency across the codebase.
"""

import asyncio
import argparse
import os
import sys

# Add project root to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def run_alembic_upgrade():
    """
    Run Alembic migrations to upgrade the database schema.
    
    This function executes the 'alembic upgrade head' command to apply all
    pending migrations to the database, bringing it to the latest schema version.
    """
    print("Running Alembic migrations...")
    os.system("alembic upgrade head")
    print("Alembic migrations completed successfully")



async def main():
    """
    Main function to run startup tasks based on command line arguments.
    
    This function parses command line arguments and executes the requested
    database operations. It supports running migrations, seeding data, or both.
    If no arguments are provided, it displays the help message.
    
    Command line arguments:
        --migrate: Run database migrations
        --all: Run both migrations and seeding
    """
    parser = argparse.ArgumentParser(description="Database setup and initialization script")
    parser.add_argument("--migrate", action="store_true", help="Run database migrations")
    parser.add_argument("--all", action="store_true", help="Run both migrations and seeding")

    args = parser.parse_args()

    # If no arguments provided, show help
    if not (args.migrate or args.all):
        parser.print_help()
        return

    # Run migrations if --migrate or --all flag is provided
    if args.migrate or args.all:
        await run_alembic_upgrade()


    print("Requested startup tasks completed successfully")


if __name__ == "__main__":
    asyncio.run(main())