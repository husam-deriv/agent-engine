

CREATE TABLE "UserTable" (
    "User_id" integer NOT NULL,
    "UserName" text NOT NULL,
    "password" text NOT NULL,
    "company_id" integer NOT NULL,
    "user_type" enum NOT NULL,
    PRIMARY KEY ("User_id")
);



CREATE TABLE "Slack_Table" (
    "slack_id" bigint NOT NULL,
    "project_ID" integer NOT NULL,
    "channel_name" text NOT NULL,
    "app_token" text NOT NULL,
    "bot_token" text NOT NULL,
    PRIMARY KEY ("slack_id")
);



CREATE TABLE "CompanyTable" (
    "company_id" integer NOT NULL,
    "group_Name" text NOT NULL UNIQUE,
    "vertical_Name" text NOT NULL,
    "company_Name" text NOT NULL,
    PRIMARY KEY ("company_id")
);



CREATE TABLE "Agents" (
    "Agent_id" integer NOT NULL,
    "Agent_Name" text NOT NULL,
    "Agent_Type" enum NOT NULL,
    "instructions" text NOT NULL,
    "tool_list" text,
    "handoff_desc" text,
    "handoff_agentList" text,
    "project_id" integer NOT NULL,
    PRIMARY KEY ("Agent_id")
);



CREATE TABLE "FileUploads" (
    "file_id" bigint NOT NULL,
    "agent_id" integer NOT NULL,
    "file_type" enum NOT NULL,
    "file_name" text NOT NULL,
    "file_description" text NOT NULL,
    PRIMARY KEY ("file_id")
);



CREATE TABLE "multiAgentProject" (
    "project_id" integer NOT NULL,
    "agentTeamType" enum NOT NULL,
    "agent_id_List" text NOT NULL,
    "deployment_status" enum NOT NULL,
    "User_id" integer NOT NULL,
    PRIMARY KEY ("project_id")
);



ALTER TABLE "Agents"
ADD CONSTRAINT "fk_Agents_project_id_multiAgentProject_project_id" FOREIGN KEY("project_id") REFERENCES "multiAgentProject"("project_id");

ALTER TABLE "FileUploads"
ADD CONSTRAINT "fk_FileUploads_agent_id_Agents_Agent_id" FOREIGN KEY("agent_id") REFERENCES "Agents"("Agent_id");

ALTER TABLE "multiAgentProject"
ADD CONSTRAINT "fk_multiAgentProject_User_id_UserTable_User_id" FOREIGN KEY("User_id") REFERENCES "UserTable"("User_id");

ALTER TABLE "Slack_Table"
ADD CONSTRAINT "fk_Slack_Table_project_ID_multiAgentProject_project_id" FOREIGN KEY("project_ID") REFERENCES "multiAgentProject"("project_id");

ALTER TABLE "UserTable"
ADD CONSTRAINT "fk_UserTable_company_id_CompanyTable_company_id" FOREIGN KEY("company_id") REFERENCES "CompanyTable"("company_id");
