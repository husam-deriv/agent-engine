#!/usr/bin/env python3
"""
Database migration script for Gargash AI Builder Platform.
This script provides a command-line interface for managing database migrations.

Usage:
    python db_migrate.py create "Migration message"  - Create a new migration
    python db_migrate.py upgrade                     - Apply all pending migrations
    python db_migrate.py downgrade                   - Revert the last migration
    python db_migrate.py history                     - Show migration history
"""

import os
import sys
import subprocess
import argparse

def run_alembic_command(command, *args):
    """Run an Alembic command with arguments."""
    cmd = ["alembic", command]
    cmd.extend(args)
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing Alembic command: {e}")
        return False

def create_migration(message):
    """Create a new migration with the given message."""
    return run_alembic_command("revision", "--autogenerate", "-m", message)

def upgrade_db(revision="head"):
    """Upgrade the database to the specified revision (default: head)."""
    return run_alembic_command("upgrade", revision)

def downgrade_db(revision="-1"):
    """Downgrade the database by the specified number of revisions (default: 1)."""
    return run_alembic_command("downgrade", revision)

def show_history():
    """Show the migration history."""
    return run_alembic_command("history")

def main():
    """Main function to handle command-line arguments."""
    parser = argparse.ArgumentParser(description="Database migration tool for Gargash AI Builder Platform")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Create migration
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument("message", help="Migration message")

    # Upgrade
    upgrade_parser = subparsers.add_parser("upgrade", help="Apply migrations")
    upgrade_parser.add_argument("revision", nargs="?", default="head", 
                              help="Revision to upgrade to (default: head)")

    # Downgrade
    downgrade_parser = subparsers.add_parser("downgrade", help="Revert migrations")
    downgrade_parser.add_argument("revision", nargs="?", default="-1", 
                                help="Number of revisions to downgrade (default: 1)")

    # History
    subparsers.add_parser("history", help="Show migration history")

    args = parser.parse_args()

    if args.command == "create":
        if create_migration(args.message):
            print(f"Migration created: {args.message}")
    elif args.command == "upgrade":
        if upgrade_db(args.revision):
            print(f"Database upgraded to: {args.revision}")
    elif args.command == "downgrade":
        if downgrade_db(args.revision):
            print(f"Database downgraded by: {args.revision}")
    elif args.command == "history":
        show_history()
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 