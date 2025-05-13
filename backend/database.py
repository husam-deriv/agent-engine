import os
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, Boolean, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
import datetime
import json
from typing import Dict, List, Optional, Any

# Create the database directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Create async engine using the Gargash database
DATABASE_URL = "sqlite+aiosqlite:///data/gargash.db"
engine = create_async_engine(DATABASE_URL, echo=True)

# Create base class for declarative models
Base = declarative_base()

# Define Department model
class DepartmentModel(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    projects = relationship("ProjectModel", back_populates="department")

# Define Sector model
class SectorModel(Base):
    __tablename__ = "sectors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    companies = relationship("CompanyModel", back_populates="sector")

# Define Company model
class CompanyModel(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    sector = relationship("SectorModel", back_populates="companies")
    projects = relationship("ProjectModel", back_populates="company")
    data_corpuses = relationship("DataCorpusModel", back_populates="company")

# Define DataCorpus model for managing company/sector data
class DataCorpusModel(Base):
    __tablename__ = "data_corpuses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    file_path = Column(String, nullable=False)  # Path to data file/directory
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=True)
    is_sector_wide = Column(Boolean, default=False)  # Whether data is shared across sector
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    company = relationship("CompanyModel", back_populates="data_corpuses")
    sector = relationship("SectorModel")

# Define Project model
class ProjectModel(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)  # New: link to company
    goal = Column(String, nullable=False)
    expected_value = Column(Float, default=3.0)
    priority = Column(Integer, default=5)
    is_scheduled = Column(Boolean, default=False)  # Whether this is a scheduled job
    schedule_frequency = Column(String, nullable=True)  # Cron expression or frequency description
    slack_channel = Column(String, nullable=True)  # Target Slack channel
    status = Column(String, default="Not Started")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    department = relationship("DepartmentModel", back_populates="projects")
    company = relationship("CompanyModel", back_populates="projects")  # New relationship
    solutions = relationship("ProjectSolutionModel", back_populates="project")

# Define the Agent model
class AgentModel(Base):
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    role = Column(String)
    personality = Column(Text)
    tools = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    projects = relationship("ProjectSolutionModel", back_populates="agent")
    conversations = relationship("ConversationModel", back_populates="agent")
    slack_bot = relationship("SlackBotModel", back_populates="agent", uselist=False)

class ProjectSolutionModel(Base):
    __tablename__ = "project_solutions"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    project = relationship("ProjectModel", back_populates="solutions")
    agent = relationship("AgentModel", back_populates="projects")

# Define the Conversation model
class ConversationModel(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)  # Link to project
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    agent = relationship("AgentModel", back_populates="conversations")
    project = relationship("ProjectModel", backref="conversations")  # Relationship to project
    messages = relationship("MessageModel", back_populates="conversation", cascade="all, delete-orphan")

# Define the Message model
class MessageModel(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String)  # user, assistant, intermediate, or system
    content = Column(Text)
    message_metadata = Column(JSON, nullable=True)  # Store additional data like agent name, sequence position, etc.
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    conversation = relationship("ConversationModel", back_populates="messages")

# Define the Multi-Agent System model
class MultiAgentSystemModel(Base):
    __tablename__ = "multi_agent_systems"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    agents = Column(JSON)  # List of agent names
    triage_agent = Column(String)  # Name of triage agent
    connections = Column(JSON, nullable=True)  # Connection mapping
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class MultiAgentConversationModel(Base):
    __tablename__ = "multi_agent_conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(String, ForeignKey("multi_agent_systems.id"), nullable=False)
    title = Column(String, default="Multi-Agent Conversation")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    messages = relationship("MultiAgentMessageModel", back_populates="conversation", cascade="all, delete-orphan")

class MultiAgentMessageModel(Base):
    __tablename__ = "multi_agent_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("multi_agent_conversations.id"), nullable=False)
    agent = Column(String, nullable=True)  # None for user messages
    role = Column(String)  # user, assistant, or system
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    conversation = relationship("MultiAgentConversationModel", back_populates="messages")

class SlackBotModel(Base):
    __tablename__ = "slack_bots"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), unique=True)
    bot_token = Column(String, nullable=False)
    app_token = Column(String, nullable=False)
    status = Column(String, default="stopped")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    agent = relationship("AgentModel", back_populates="slack_bot")

# Create a session factory
async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Create tables
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Database session dependency
async def get_db():
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

# Function to close the database
async def close_db():
    await engine.dispose()

# Helper function to convert SQLAlchemy model to dict
def model_to_dict(model):
    result = {}
    for column in model.__table__.columns:
        value = getattr(model, column.name)
        if isinstance(value, datetime.datetime):
            value = value.isoformat()
        result[column.name] = value
    return result 