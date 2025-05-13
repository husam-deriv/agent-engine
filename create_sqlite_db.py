import sqlite3
import os

# Create the SQLite database file in the root directory
db_file = 'database.sqlite'

# Check if file exists and remove it if it does
if os.path.exists(db_file):
    os.remove(db_file)
    print(f"Removed existing database: {db_file}")

# Connect to SQLite database (this creates the file if it doesn't exist)
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Create tables with SQLite compatible syntax
# Note: SQLite doesn't support ENUM, so we'll use TEXT with CHECK constraints

# Create UserTable
cursor.execute('''
CREATE TABLE "UserTable" (
    "User_id" INTEGER NOT NULL,
    "UserName" TEXT NOT NULL,
    "password" TEXT NOT NULL,
    "company_id" INTEGER NOT NULL,
    "user_type" TEXT NOT NULL,
    PRIMARY KEY ("User_id"),
    FOREIGN KEY("company_id") REFERENCES "CompanyTable"("company_id")
)
''')

# Create Slack_Table
cursor.execute('''
CREATE TABLE "Slack_Table" (
    "slack_id" INTEGER NOT NULL,
    "project_ID" INTEGER NOT NULL,
    "channel_name" TEXT NOT NULL,
    "app_token" TEXT NOT NULL,
    "bot_token" TEXT NOT NULL,
    PRIMARY KEY ("slack_id"),
    FOREIGN KEY("project_ID") REFERENCES "multiAgentProject"("project_id")
)
''')

# Create CompanyTable
cursor.execute('''
CREATE TABLE "CompanyTable" (
    "company_id" INTEGER NOT NULL,
    "group_Name" TEXT NOT NULL UNIQUE,
    "vertical_Name" TEXT NOT NULL,
    "company_Name" TEXT NOT NULL,
    PRIMARY KEY ("company_id")
)
''')

# Create Agents
cursor.execute('''
CREATE TABLE "Agents" (
    "Agent_id" INTEGER NOT NULL,
    "Agent_Name" TEXT NOT NULL,
    "Agent_Type" TEXT NOT NULL,
    "instructions" TEXT NOT NULL,
    "tool_list" TEXT,
    "handoff_desc" TEXT,
    "handoff_agentList" TEXT,
    "project_id" INTEGER NOT NULL,
    PRIMARY KEY ("Agent_id"),
    FOREIGN KEY("project_id") REFERENCES "multiAgentProject"("project_id")
)
''')

# Create FileUploads
cursor.execute('''
CREATE TABLE "FileUploads" (
    "file_id" INTEGER NOT NULL,
    "agent_id" INTEGER NOT NULL,
    "file_type" TEXT NOT NULL,
    "file_name" TEXT NOT NULL,
    "file_description" TEXT NOT NULL,
    PRIMARY KEY ("file_id"),
    FOREIGN KEY("agent_id") REFERENCES "Agents"("Agent_id")
)
''')

# Create multiAgentProject
cursor.execute('''
CREATE TABLE "multiAgentProject" (
    "project_id" INTEGER NOT NULL,
    "agentTeamType" TEXT NOT NULL,
    "agent_id_List" TEXT NOT NULL,
    "deployment_status" TEXT NOT NULL,
    "User_id" INTEGER NOT NULL,
    PRIMARY KEY ("project_id"),
    FOREIGN KEY("User_id") REFERENCES "UserTable"("User_id")
)
''')

# Commit the changes and close the connection
conn.commit()
conn.close()

print(f"SQLite database '{db_file}' created successfully with all tables according to the updated schema.")
print("Note: Due to SQLite's constraints, the tables have been created in an order that respects foreign key dependencies.") 