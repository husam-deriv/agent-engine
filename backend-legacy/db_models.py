from sqlalchemy import Column, String, Integer, Text, ForeignKey, Boolean, DateTime, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # e.g., "Marketing AI", "HR AI", "Sales AI"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    projects = relationship("Project", back_populates="department")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"))
    goal = Column(String)  # e.g., "Productivity", "Cost Savings", "Win new Customers"
    expected_value = Column(Float, default=3.0)  # Scale of 1-5
    target_date = Column(DateTime, nullable=True)
    status = Column(String, default="Not Started")  # "Not Started", "In Progress", "Completed"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    department = relationship("Department", back_populates="projects")
    solutions = relationship("Agent", secondary="project_solutions", back_populates="projects")

# Junction table for many-to-many relationship between projects and agents (now called solutions)
class ProjectSolution(Base):
    __tablename__ = "project_solutions"
    
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    role = Column(String)
    personality = Column(Text)
    tools = Column(JSON)  # Store tools as JSON
    custom_tools = Column(JSON, nullable=True, default=None)  # Store custom tool names as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    conversations = relationship("Conversation", back_populates="agent", cascade="all, delete-orphan")
    projects = relationship("Project", secondary="project_solutions", back_populates="solutions")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"))
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    agent = relationship("Agent", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"))
    role = Column(String)  # "user", "assistant", "system", etc.
    content = Column(Text)
    message_metadata = Column(JSON, nullable=True)  # Store metadata like API response details
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")

class CustomTool(Base):
    __tablename__ = "custom_tools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    implementation = Column(Text)  # Python code as a string
    requirements = Column(JSON, nullable=True)  # Required packages as a JSON list
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CustomToolSecret(Base):
    __tablename__ = "custom_tool_secrets"
    
    id = Column(Integer, primary_key=True, index=True)
    tool_name = Column(String, ForeignKey("custom_tools.name", ondelete="CASCADE"))
    key = Column(String)
    value = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MultiAgentSystem(Base):
    __tablename__ = "multi_agent_systems"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    agents = Column(JSON)  # List of agent names
    triage_agent = Column(String)  # Name of the triage agent
    connections = Column(JSON, nullable=True)  # Configuration for connections between agents
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
class MultiAgentConversation(Base):
    __tablename__ = "multi_agent_conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, ForeignKey("multi_agent_systems.id", ondelete="CASCADE"))
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    messages = relationship("MultiAgentMessage", back_populates="conversation", cascade="all, delete-orphan")

class MultiAgentMessage(Base):
    __tablename__ = "multi_agent_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("multi_agent_conversations.id", ondelete="CASCADE"))
    role = Column(String)  # "user", "assistant", "system", etc.
    content = Column(Text)
    agent = Column(String, nullable=True)  # Which agent generated this message, if applicable
    message_metadata = Column(JSON, nullable=True)  # Store metadata like which agent was used, routing info, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("MultiAgentConversation", back_populates="messages")

class SlackBot(Base):
    __tablename__ = "slack_bots"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, unique=True, index=True)
    bot_token = Column(String)  # Slack Bot User OAuth Token
    app_token = Column(String)  # Slack App-Level Token
    status = Column(String, default="stopped")  # running, stopped
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 