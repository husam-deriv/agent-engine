import os
import time
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Query, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
from typing import List, Dict, Optional, Any, Union
from dotenv import load_dotenv
import agent_utils
import agent_tools
import multi_agent_service
import project_management
from models import AgentConnection, MultiAgentSystem, MultiAgentSystemResponse
import database as db_module
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from fastapi.responses import FileResponse
from sqlalchemy import select, func
import datetime
import json
from project_analyzer import ProjectAnalyzer
from agent_generator import AgentGenerator

# Load environment variables
load_dotenv()

app = FastAPI(title="Gargash AI Builder Platform")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
openai_client = None

@app.on_event("startup")
async def startup_event():
    global openai_client
    openai_client = agent_utils.get_openai_client()
    if not openai_client:
        print("Warning: OpenAI client initialization failed. API key may be missing.")
    
    # Ensure the profile pictures directory exists
    os.makedirs("data/profile_pictures", exist_ok=True)
    print("Created profile pictures directory")
    
    # Initialize database
    await db_module.init_db()
    
    # Ensure all required tables exist
    try:
        # Run our migration script first
        import migration_script
        print("Running database migrations...")
        migration_script.ensure_tables_exist()
        
        # Then try the other integration scripts
        try:
            import slack_integration
            if hasattr(slack_integration, 'ensure_slack_table_exists'):
                print("Ensuring Slack tables exist...")
                slack_integration.ensure_slack_table_exists()
        except ImportError:
            print("Warning: Could not import slack_integration module")
        
        # Then try the other migration script as fallback
        try:
            print("Running migrations from migration_script...")
            migration_script.ensure_tables_exist()
        except Exception as e:
            print(f"Warning: Migration script error: {str(e)}")
        
        # Always attempt direct SQL creation as a last resort
        try:
            import sqlite3
            
            # Find database path
            db_paths = ["./app.db", "../app.db", "./data/agents.db", "../data/agents.db"]
            db_path = None
            
            for path in db_paths:
                if os.path.exists(path):
                    db_path = path
                    break
                    
            if db_path:
                print(f"Checking database at {db_path} for required tables...")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if slack_bots table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='slack_bots';")
                if not cursor.fetchone():
                    print("Creating slack_bots table directly with SQLite...")
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS slack_bots (
                        id INTEGER PRIMARY KEY,
                        agent_name TEXT UNIQUE,
                        bot_token TEXT NOT NULL,
                        app_token TEXT NOT NULL,
                        status TEXT DEFAULT 'stopped',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """)
                    
                    # Create an index on agent_name
                    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_slack_bots_agent_name ON slack_bots (agent_name);")
                    conn.commit()
                    print("Successfully created slack_bots table.")
                
                conn.close()
        except Exception as sqlite_err:
            print(f"Warning: Direct SQLite attempt failed: {str(sqlite_err)}")
            
    except Exception as e:
        print(f"Warning: Failed to ensure all tables exist: {str(e)}")
        print("Continuing startup process despite table creation errors...")
    
    # Get a database session
    async for session in db_module.get_db():
        # Initialize agents from database
        await agent_utils.initialize_agents(session, openai_client)
        
        # Initialize multi-agent systems from database
        await multi_agent_service.initialize_multi_agent_systems(session)
        
        # Initialize Slack bots that should be running
        try:
            import slack_integration
            if hasattr(slack_integration, 'initialize_slack_bots'):
                print("Initializing Slack bots...")
                await slack_integration.initialize_slack_bots(session)
                print("Slack bots initialization completed")
            else:
                print("Warning: slack_integration module does not have initialize_slack_bots function")
        except ImportError:
            print("Warning: Could not import slack_integration module for bot initialization")
        except Exception as slack_error:
            print(f"Error initializing Slack bots: {str(slack_error)}")
        
        # Initialize departments for Gargash AI Builder
        await project_management.ensure_default_departments(session)
        print("Initialized departments for Gargash AI Builder Platform")
        
        break

# Pydantic models
class Agent(BaseModel):
    name: str
    role: str
    tools: List[str]
    personality: str

class MessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None

class MessageResponse(BaseModel):
    response: str
    conversation_id: str

class ToolDescription(BaseModel):
    name: str
    description: str
    type: Optional[str] = "function"

class MultiAgentSystemRequest(BaseModel):
    name: str
    description: str
    agents: List[str]
    triage_agent: str
    connections: Optional[List[AgentConnection]] = None

class MultiAgentInteractionRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None

class ConversationRequest(BaseModel):
    title: Optional[str] = None

class ConversationResponse(BaseModel):
    conversation_id: str
    agent_id: str
    title: str
    messages: List[Dict[str, Any]]
    created_at: str
    updated_at: str

class MessageHistoryResponse(BaseModel):
    id: int
    role: str
    content: str
    timestamp: str

# Add new models for custom tools
class CreateCustomToolRequest(BaseModel):
    description: str
    install_requirements: bool = True

class CustomToolResponse(BaseModel):
    name: str
    description: str
    requirements: List[str]
    secrets: List[str]
    success: bool
    message: str

# Add models for Slack integration
class SlackDeployRequest(BaseModel):
    bot_token: str
    app_token: str

class SlackBotResponse(BaseModel):
    success: bool
    message: str
    status: Optional[str] = None

class SlackToggleRequest(BaseModel):
    action: str  # 'start' or 'stop'

class SlackBotStatusResponse(BaseModel):
    deployed: bool
    status: str

# Add new models for project management
class Department(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    department: str
    goal: str
    expected_value: Optional[float] = 3.0
    solution_ids: Optional[List[int]] = None

class ProjectCreate(ProjectBase):
    company_id: Optional[int] = None
    skip_data_integration: Optional[bool] = False
    skip_slack_integration: Optional[bool] = False
    recommended_architecture: Optional[Dict[str, Any]] = None

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    goal: Optional[str] = None
    expected_value: Optional[float] = None
    status: Optional[str] = None
    solution_ids: Optional[List[int]] = None

class ProjectResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    department: str
    goal: str
    expected_value: float
    status: str
    solutions: Optional[List[Dict[str, Any]]] = []
    created_at: str
    updated_at: str

# Add models for the new endpoints
class CompanyResponse(BaseModel):
    id: int
    name: str
    sector_id: int
    sector_name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str
    
class SectorResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    company_count: int
    created_at: str
    updated_at: str

class DataCorpusUpload(BaseModel):
    name: str
    description: Optional[str] = None
    company_id: int
    is_sector_wide: bool = False

class ProjectAnalysisRequest(BaseModel):
    title: str
    description: str
    company_id: int

class ProjectAnalysisResponse(BaseModel):
    project: Dict[str, Any]
    analysis: Dict[str, Any]
    agent_configuration: Dict[str, Any]
    data_requirements: List[Dict[str, Any]]
    needs_data_integration: Optional[bool] = False
    needs_slack_integration: Optional[bool] = False

# Add new models for agent and tool generation
class AgentGenerationRequest(BaseModel):
    project_title: str
    project_description: str
    company_id: int
    problem_type: str
    suggested_tools: List[str]

class ToolGenerationRequest(BaseModel):
    tool_name: str
    tool_description: str
    project_context: str

# Add new models for project analysis with additional steps
class ProjectFollowupQuestionsRequest(BaseModel):
    title: str
    description: str
    company_id: int

class ProjectFollowupQuestionsResponse(BaseModel):
    questions: List[str]

class ArchitectureRecommendationRequest(BaseModel):
    title: str
    description: str
    company_id: int
    question_answers: List[Dict[str, str]]

class ArchitectureRecommendationResponse(BaseModel):
    architecture_type: str
    description: str
    agents: List[Dict[str, Any]]
    workflow: str
    project: Dict[str, Any]

# Database dependency
async def get_db():
    async for session in db_module.get_db():
        yield session

# Dependency to get OpenAI client
async def get_openai_client():
    global openai_client
    if not openai_client:
        openai_client = agent_utils.get_openai_client()
    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenAI client not initialized. Check API key.")
    return openai_client

@app.post("/ai-solutions/")
async def create_ai_solution(agent: Agent, client: AsyncOpenAI = Depends(get_openai_client), db: AsyncSession = Depends(get_db)):
    """Create a new AI Solution (formerly known as agent)."""
    try:
        # Create the agent
        await agent_utils.get_or_create_agent(
            session=db,
            name=agent.name,
            role=agent.role,
            personality=agent.personality,
            tools=agent.tools,
            openai_client=client
        )
        return {"message": "AI Solution created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create AI Solution: {str(e)}")

@app.get("/ai-solutions/")
async def list_ai_solutions(db: AsyncSession = Depends(get_db)):
    """List all available AI Solutions (formerly known as agents)."""
    # Maintain the original endpoint for backward compatibility
    return await list_agents(db)

@app.post("/create_agent/")
async def create_agent(agent: Agent, client: AsyncOpenAI = Depends(get_openai_client), db: AsyncSession = Depends(get_db)):
    return await create_ai_solution(agent, client, db)

@app.get("/list_agents/")
async def list_agents(db: AsyncSession = Depends(get_db)):
    """List all available AI Solutions."""
    # Get in-memory agents first
    agents_dict = {}
    in_memory_agents = agent_utils.get_all_agents()
    
    if in_memory_agents:
        # Convert agents to a dictionary format that can be serialized
        for name, agent_obj in in_memory_agents.items():
            # Extract tools from the agent
            tool_names = []
            if hasattr(agent_obj, 'tools') and agent_obj.tools:
                for tool in agent_obj.tools:
                    if hasattr(tool, 'name'):
                        tool_names.append(tool.name)
            
            # Get original personality from database
            result = await db.execute(select(db_module.AgentModel).where(db_module.AgentModel.name == name))
            agent_model = result.scalars().first()
            original_personality = agent_model.personality if agent_model else ""
            
            agents_dict[name] = {
                "name": name,
                "role": agent_obj.handoff_description.replace(" agent", ""),
                "personality": original_personality,  # Use original personality for the list view
                "tools": tool_names,
                "id": agent_model.id if agent_model else None
            }
    
    # If no in-memory agents, check database directly
    if not agents_dict:
        try:
            # Query all agents from database
            result = await db.execute(select(db_module.AgentModel))
            agent_models = result.scalars().all()
            
            # Convert database agents to dictionary
            for agent_model in agent_models:
                # Parse tools JSON if available
                tool_names = []
                if agent_model.tools:
                    tool_names = json.loads(agent_model.tools) if isinstance(agent_model.tools, str) else agent_model.tools
                
                agents_dict[agent_model.name] = {
                    "name": agent_model.name,
                    "role": agent_model.role,
                    "personality": agent_model.personality,
                    "tools": tool_names,
                    "id": agent_model.id
                }
        except Exception as e:
            print(f"Error loading agents from database: {str(e)}")
            # Return empty dict if both approaches fail
            return {}
    
    return agents_dict

@app.get("/agent/{agent_name}")
async def get_agent(agent_name: str, db: AsyncSession = Depends(get_db)):
    agents = agent_utils.get_all_agents()
    if agent_name not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent_obj = agents[agent_name]
    # Extract tools from the agent
    tool_names = []
    if hasattr(agent_obj, 'tools') and agent_obj.tools:
        for tool in agent_obj.tools:
            if hasattr(tool, 'name'):
                tool_names.append(tool.name)
    
    # Check if this agent has a profile picture
    profile_pic_path = f"data/profile_pictures/{agent_name}.jpg"
    has_profile_picture = os.path.exists(profile_pic_path)
    
    # Get original personality from database
    result = await db.execute(select(db_module.AgentModel).where(db_module.AgentModel.name == agent_name))
    agent_model = result.scalars().first()
    original_personality = agent_model.personality if agent_model else ""
    
    return {
        "name": agent_name,
        "role": agent_obj.handoff_description.replace(" agent", ""),
        "personality": agent_obj.instructions,  # This is the full system prompt
        "original_personality": original_personality,  # This is the user's original input
        "tools": tool_names,
        "hasProfilePicture": has_profile_picture
    }

@app.delete("/delete_agent/{agent_name}")
async def delete_agent(agent_name: str, db: AsyncSession = Depends(get_db)):
    success = await agent_utils.delete_agent(db, agent_name)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Agent deleted successfully"}

@app.post("/interact/{agent_name}", response_model=MessageResponse)
async def interact_with_agent(agent_name: str, request: MessageRequest, db: AsyncSession = Depends(get_db)):
    try:
        conversation_id = request.conversation_id
        
        # Interact with the agent using the database
        result = await agent_utils.interact_with_agent(
            agent_name=agent_name,
            message=request.message,
            session=db,
            conversation_id=int(conversation_id) if conversation_id else None
        )
        
        # Check if result is a dictionary or string and extract the response
        if isinstance(result, dict):
            response_text = result.get("response", "No response from agent")
            # Update conversation_id if it was returned
            if "conversation_id" in result and result["conversation_id"]:
                conversation_id = str(result["conversation_id"])
        else:
            # For backward compatibility with string responses
            response_text = str(result)
        
        # Get the conversation ID from the database if not provided
        if not conversation_id:
            # Find the most recent conversation for this agent
            agent_conversations = await agent_utils.get_agent_conversations(db, agent_name)
            if agent_conversations:
                conversation_id = str(agent_conversations[0]["id"])
            else:
                # Fallback to default value
                conversation_id = "0"
        
        return {"response": response_text, "conversation_id": conversation_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interacting with agent: {str(e)}")

@app.get("/available_tools", response_model=List[ToolDescription])
async def get_available_tools():
    """Get a list of all available tools that can be assigned to agents."""
    return agent_utils.get_available_tool_descriptions()

# Add a health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "openai_client_initialized": openai_client is not None}

# Multi-agent system endpoints
@app.post("/multi_agent_systems/", response_model=MultiAgentSystemResponse)
async def create_multi_agent_system(request: MultiAgentSystemRequest, db: AsyncSession = Depends(get_db)):
    try:
        system = await multi_agent_service.create_multi_agent_system(
            session=db,
            name=request.name,
            description=request.description,
            agent_names=request.agents,
            triage_agent_name=request.triage_agent,
            connections=request.connections
        )
        return system
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create multi-agent system: {str(e)}")

@app.get("/multi_agent_systems/", response_model=List[MultiAgentSystemResponse])
async def list_multi_agent_systems(db: AsyncSession = Depends(get_db)):
    try:
        systems = await multi_agent_service.get_all_multi_agent_systems_from_db(db)
        return [
            {
                "id": system.id,
                "name": system.name,
                "description": system.description,
                "agents": system.agents,
                "triage_agent": system.triage_agent,
                "connections": [AgentConnection(**conn) for conn in system.connections] if system.connections else [],
                "created_at": system.created_at.isoformat()
            }
            for system in systems
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list multi-agent systems: {str(e)}")

@app.get("/multi_agent_systems/{system_id}", response_model=MultiAgentSystemResponse)
async def get_multi_agent_system(system_id: str, db: AsyncSession = Depends(get_db)):
    try:
        # Check for invalid system_id
        if not system_id or system_id == 'undefined':
            raise HTTPException(status_code=400, detail="Invalid system ID")
            
        system = await multi_agent_service.get_multi_agent_system_from_db(system_id, db)
        if not system:
            raise HTTPException(status_code=404, detail="Multi-agent system not found")
        return {
            "id": system.id,
            "name": system.name,
            "description": system.description,
            "agents": system.agents,
            "triage_agent": system.triage_agent,
            "connections": [AgentConnection(**conn) for conn in system.connections] if system.connections else [],
            "created_at": system.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get multi-agent system: {str(e)}")

@app.put("/multi_agent_systems/{system_id}", response_model=MultiAgentSystemResponse)
async def update_multi_agent_system(system_id: str, request: MultiAgentSystemRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Check for invalid system_id
        if not system_id or system_id == 'undefined':
            raise HTTPException(status_code=400, detail="Invalid system ID")
            
        system = await multi_agent_service.update_multi_agent_system(
            session=db,
            system_id=system_id,
            name=request.name,
            description=request.description,
            agent_names=request.agents,
            triage_agent_name=request.triage_agent,
            connections=request.connections
        )
        if not system:
            raise HTTPException(status_code=404, detail="Multi-agent system not found")
        return system
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update multi-agent system: {str(e)}")

@app.delete("/multi_agent_systems/{system_id}")
async def delete_multi_agent_system(system_id: str, db: AsyncSession = Depends(get_db)):
    try:
        success = await multi_agent_service.delete_multi_agent_system(db, system_id)
        if not success:
            raise HTTPException(status_code=404, detail="Multi-agent system not found")
        return {"message": f"Multi-agent system {system_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete multi-agent system: {str(e)}")

@app.post("/multi_agent_systems/{system_id}/interact")
async def interact_with_multi_agent_system_endpoint(
    system_id: str, 
    request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message to a multi-agent system and get a response
    """
    try:
        # Check for invalid system_id
        if not system_id or system_id == 'undefined':
            raise HTTPException(status_code=400, detail="Invalid system ID")
            
        # Extract necessary fields from the request
        user_message = request.get("message", "")
        user_id = request.get("user_id", "default_user")
        
        # Convert conversation_id to int if provided
        conversation_id = None
        if "conversation_id" in request and request["conversation_id"]:
            try:
                conversation_id = int(request["conversation_id"])
            except (ValueError, TypeError):
                # If conversion fails, just leave it as None
                pass
                
        response = await multi_agent_service.interact_with_multi_agent_system(
            system_id=system_id,
            user_message=user_message,
            user_id=user_id,
            db_session=db,
            conversation_id=conversation_id
        )
        
        if "error" in response:
            return response
            
        return response
    except HTTPException:
        raise
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

@app.get("/agent/{agent_name}/conversations", response_model=List[Dict[str, Any]])
async def get_agent_conversations(agent_name: str, db: AsyncSession = Depends(get_db)):
    try:
        conversations = await agent_utils.get_agent_conversations(db, agent_name)
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

@app.get("/conversation/{conversation_id}", response_model=List[Dict[str, Any]])
async def get_conversation_history(
    conversation_id: int, 
    include_intermediate: bool = False,
    db: AsyncSession = Depends(get_db)
):
    try:
        messages = await agent_utils.get_conversation_history(
            db, 
            conversation_id, 
            include_intermediate
        )
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation history: {str(e)}")

# Add back the old conversation endpoints for compatibility with frontend
@app.post("/agents/{agent_name}/conversations", response_model=ConversationResponse)
async def create_conversation(agent_name: str, request: ConversationRequest, db_session: AsyncSession = Depends(get_db)):
    try:
        # Check if agent exists
        agents = agent_utils.get_all_agents()
        if agent_name not in agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Get agent from database
        result = await db_session.execute(select(db_module.AgentModel).where(db_module.AgentModel.name == agent_name))
        agent_model = result.scalars().first()
        
        if not agent_model:
            raise HTTPException(status_code=404, detail="Agent not found in database")
        
        # Create new conversation
        title = request.title or f"Conversation with {agent_name}"
        conversation = db_module.ConversationModel(
            agent_id=agent_model.id,
            title=title
        )
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)
        
        # Format response to match the old format
        return {
            "conversation_id": str(conversation.id),
            "agent_id": agent_name,
            "title": conversation.title,
            "messages": [],
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating conversation: {str(e)}")

@app.get("/agents/{agent_name}/conversations", response_model=List[ConversationResponse])
async def get_conversations(agent_name: str, db_session: AsyncSession = Depends(get_db)):
    try:
        # Check if agent exists
        agents = agent_utils.get_all_agents()
        if agent_name not in agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Get conversations from database
        conversations = await agent_utils.get_agent_conversations(db_session, agent_name)
        
        # Format response to match the old format
        return [
            {
                "conversation_id": str(conv["id"]),
                "agent_id": agent_name,
                "title": conv["title"],
                "messages": [],  # We'll load messages separately
                "created_at": conv["created_at"],
                "updated_at": conv["updated_at"]
            }
            for conv in conversations
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversations: {str(e)}")

@app.get("/agents/{agent_name}/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(agent_name: str, conversation_id: str, db_session: AsyncSession = Depends(get_db)):
    try:
        # Check if agent exists
        agents = agent_utils.get_all_agents()
        if agent_name not in agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Get conversation from database
        result = await db_session.execute(
            select(db_module.ConversationModel)
            .join(db_module.AgentModel)
            .where(db_module.AgentModel.name == agent_name)
            .where(db_module.ConversationModel.id == int(conversation_id))
        )
        conversation = result.scalars().first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get messages
        messages = await agent_utils.get_conversation_history(db_session, int(conversation_id))
        
        # Format response to match the old format
        return {
            "conversation_id": str(conversation.id),
            "agent_id": agent_name,
            "title": conversation.title,
            "messages": messages,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation: {str(e)}")

@app.delete("/agents/{agent_name}/conversations/{conversation_id}")
async def delete_conversation(agent_name: str, conversation_id: str, db_session: AsyncSession = Depends(get_db)):
    try:
        # Check if agent exists
        agents = agent_utils.get_all_agents()
        if agent_name not in agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Get conversation from database
        result = await db_session.execute(
            select(db_module.ConversationModel)
            .join(db_module.AgentModel)
            .where(db_module.AgentModel.name == agent_name)
            .where(db_module.ConversationModel.id == int(conversation_id))
        )
        conversation = result.scalars().first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Delete conversation
        await db_session.delete(conversation)
        await db_session.commit()
        
        return {"message": "Conversation deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")

@app.get("/multi_agent_systems/{system_id}/conversations")
async def get_multi_agent_system_conversations(
    system_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all conversations for a multi-agent system
    """
    try:
        # Check for invalid system_id
        if not system_id or system_id == 'undefined':
            raise HTTPException(status_code=400, detail="Invalid system ID")
            
        conversations = await multi_agent_service.get_multi_agent_conversations(
            system_id=system_id,
            db_session=db
        )
        return conversations
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

@app.get("/multi_agent_systems/conversations/{conversation_id}")
async def get_multi_agent_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific multi-agent conversation
    """
    try:
        # Check for invalid conversation_id
        if not conversation_id:
            raise HTTPException(status_code=400, detail="Invalid conversation ID")
            
        messages = await multi_agent_service.get_multi_agent_conversation_history(
            conversation_id=conversation_id,
            db_session=db
        )
        
        if not messages:
            raise HTTPException(status_code=404, detail="Conversation not found or has no messages")
            
        return messages
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")

# Add new endpoints for custom tools
@app.post("/custom_tools", response_model=CustomToolResponse)
async def create_custom_tool(
    request: CreateCustomToolRequest, 
    client: AsyncOpenAI = Depends(get_openai_client)
):
    """
    Create a new custom tool for agents based on natural language description
    """
    from custom_tool_manager import custom_tool_manager
    from custom_tool_generator import CustomToolGenerator
    
    try:
        # Create the tool generator
        generator = CustomToolGenerator(openai_client=client)
        
        # Generate the tool definition
        tool_def = await generator.generate_tool_definition(request.description)
        
        # Generate implementation
        implementation = await generator.generate_implementation(tool_def)
        
        # Create the tool
        tool_info = await custom_tool_manager.create_custom_tool(request.description, client)
        
        # Install requirements if requested
        if request.install_requirements and tool_info.get("requirements"):
            install_result = custom_tool_manager.install_tool_requirements(tool_info["name"])
            if install_result["status"] == "error":
                return {
                    "name": tool_info["name"],
                    "description": tool_def["function"]["description"],
                    "requirements": tool_info.get("requirements", []),
                    "secrets": tool_info.get("secrets", []),
                    "success": False,
                    "message": f"Tool created but requirements installation failed: {install_result['message']}"
                }
        
        return {
            "name": tool_info["name"],
            "description": tool_def["function"]["description"],
            "requirements": tool_info.get("requirements", []),
            "secrets": tool_info.get("secrets", []),
            "success": True,
            "message": "Custom tool created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create custom tool: {str(e)}")

# New endpoint for saving API keys for custom tools
class SaveSecretsRequest(BaseModel):
    secrets: Dict[str, str]

@app.post("/custom_tools/{tool_name}/secrets")
async def save_tool_secrets(tool_name: str, request: SaveSecretsRequest):
    """
    Save API keys/secrets for a custom tool
    """
    from custom_tool_manager import custom_tool_manager
    import os
    
    try:
        # Get the required secrets for this tool
        required_secrets = custom_tool_manager.get_required_secrets(tool_name)
        
        # Check if all required secrets are provided
        missing_secrets = [secret for secret in required_secrets if secret not in request.secrets]
        if missing_secrets:
            return {
                "success": False,
                "message": f"Missing required secrets: {', '.join(missing_secrets)}"
            }
        
        # In a production environment, you would securely store these secrets
        # For this demo, we'll just set them as environment variables for the current process
        for key, value in request.secrets.items():
            os.environ[key] = value
        
        return {
            "success": True,
            "message": f"Secrets for {tool_name} saved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save secrets: {str(e)}")

@app.get("/custom_tools", response_model=List[Dict[str, str]])
async def list_custom_tools():
    """
    Get a list of all available custom tools
    """
    from custom_tool_manager import custom_tool_manager
    return custom_tool_manager.get_custom_tool_descriptions()

@app.get("/custom_tools/{tool_name}/requirements")
async def get_tool_requirements(tool_name: str):
    """
    Get the requirements for a custom tool
    """
    from custom_tool_manager import custom_tool_manager
    return {
        "requirements": custom_tool_manager.get_required_secrets(tool_name)
    }

@app.post("/custom_tools/{tool_name}/install")
async def install_tool_requirements(tool_name: str):
    """
    Install the requirements for a custom tool
    """
    from custom_tool_manager import custom_tool_manager
    return custom_tool_manager.install_tool_requirements(tool_name)

@app.delete("/custom_tools/{tool_name}")
async def delete_custom_tool(tool_name: str):
    """
    Delete a custom tool
    """
    from custom_tool_manager import custom_tool_manager
    success = custom_tool_manager.delete_custom_tool(tool_name)
    if not success:
        raise HTTPException(status_code=404, detail="Custom tool not found")
    return {"message": f"Custom tool {tool_name} deleted successfully"}

# Add Slack integration endpoints
@app.post("/agents/{agent_name}/deploy_to_slack", response_model=SlackBotResponse)
async def deploy_to_slack(
    agent_name: str,
    request: SlackDeployRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Deploy an agent as a Slack bot.
    Requires a Slack Bot User OAuth Token and App Level Token.
    """
    import slack_integration
    
    result = await slack_integration.deploy_agent_to_slack(
        agent_name=agent_name,
        bot_token=request.bot_token,
        app_token=request.app_token,
        db_session=db
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@app.post("/agents/{agent_name}/slack/toggle", response_model=SlackBotResponse)
async def toggle_slack_bot(
    agent_name: str,
    request: SlackToggleRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Start or stop a deployed Slack bot.
    """
    import slack_integration
    
    result = await slack_integration.toggle_slack_bot(
        agent_name=agent_name,
        action=request.action,
        db_session=db
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@app.get("/agents/{agent_name}/slack/status", response_model=SlackBotStatusResponse)
async def get_slack_bot_status(
    agent_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the status of a deployed Slack bot.
    """
    import slack_integration
    
    result = await slack_integration.get_slack_bot_status(
        agent_name=agent_name,
        db_session=db
    )
    return result

@app.get("/slack/bots", response_model=List[Dict[str, Any]])
async def list_slack_bots(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all deployed Slack bots.
    """
    import slack_integration
    
    result = await slack_integration.get_all_slack_bots(db_session=db)
    return result

@app.delete("/agents/{agent_name}/slack", response_model=SlackBotResponse)
async def undeploy_slack_bot(
    agent_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Undeploy a Slack bot.
    """
    import slack_integration
    
    result = await slack_integration.undeploy_slack_bot(
        agent_name=agent_name,
        db_session=db
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

# New endpoint for updating an agent
@app.put("/update_agent/{agent_name}")
async def update_agent(
    agent_name: str, 
    agent_data: Agent,
    db: AsyncSession = Depends(get_db),
    openai_client: AsyncOpenAI = Depends(get_openai_client)
):
    agents = agent_utils.get_all_agents()
    if agent_name not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Update the agent in the database and memory
    try:
        # Load existing tools for the agent if not provided
        if not agent_data.tools:
            existing_agent = agents[agent_name]
            tool_names = []
            if hasattr(existing_agent, 'tools') and existing_agent.tools:
                for tool in existing_agent.tools:
                    if hasattr(tool, 'name'):
                        tool_names.append(tool.name)
            agent_data.tools = tool_names
        
        # Store the original personality (not the system prompt)
        result = await db.execute(select(db_module.AgentModel).where(db_module.AgentModel.name == agent_name))
        agent_model = result.scalars().first()
        
        if agent_model:
            # Update the agent model directly to preserve original personality
            agent_model.role = agent_data.role
            agent_model.personality = agent_data.personality  # Store original personality
            agent_model.tools = agent_data.tools
            agent_model.updated_at = datetime.datetime.utcnow()
            await db.commit()
            
            # Recreate the in-memory agent with new parameters
            if agent_name in agent_utils.agents_store:
                del agent_utils.agents_store[agent_name]
            
            agent_utils.agents_store[agent_name] = agent_utils.create_agent(
                name=agent_name,
                role=agent_data.role,
                personality=agent_data.personality,
                tools=agent_data.tools,
                openai_client=openai_client
            )
            
            return {"status": "success", "message": f"Agent {agent_name} updated successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found in database")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update agent: {str(e)}")

# Upload profile picture for an agent
@app.post("/agent/{agent_name}/profile-picture")
async def upload_profile_picture(
    agent_name: str,
    file: UploadFile
):
    agents = agent_utils.get_all_agents()
    if agent_name not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Create all necessary directories recursively
    try:
        os.makedirs("data/profile_pictures", exist_ok=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create profile pictures directory: {str(e)}")
    
    # Validate that the file is an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read file content
        contents = await file.read()
        
        # Validate that content is not empty
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Save the image
        file_path = f"data/profile_pictures/{agent_name}.jpg"
        with open(file_path, "wb") as f:
            f.write(contents)
        
        return {"status": "success", "message": "Profile picture uploaded successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload profile picture: {str(e)}")

# Get profile picture for an agent
@app.get("/agent/{agent_name}/profile-picture")
async def get_profile_picture(agent_name: str):
    agents = agent_utils.get_all_agents()
    if agent_name not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check if profile picture exists
    file_path = f"data/profile_pictures/{agent_name}.jpg"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Profile picture not found")
    
    return FileResponse(file_path)

# PROJECT MANAGEMENT ENDPOINTS

@app.get("/roadmap", response_model=Dict[str, Any])
async def get_roadmap(db: AsyncSession = Depends(get_db)):
    """Get the AI Product Roadmap view with departments and projects."""
    try:
        roadmap = await project_management.get_roadmap(db)
        return roadmap
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get roadmap: {str(e)}")

@app.get("/departments", response_model=List[Dict[str, Any]])
async def get_departments(db: AsyncSession = Depends(get_db)):
    """Get all departments."""
    try:
        departments = await project_management.get_all_departments(db)
        return departments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get departments: {str(e)}")

@app.get("/departments/{department_name}/projects", response_model=List[Dict[str, Any]])
async def get_department_projects(department_name: str, db: AsyncSession = Depends(get_db)):
    """Get all projects in a department."""
    try:
        projects = await project_management.get_projects_by_department(db, department_name)
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get projects: {str(e)}")

@app.post("/projects", response_model=Dict[str, Any])
async def create_project(project: ProjectCreate, db: AsyncSession = Depends(get_db), openai_client: AsyncOpenAI = Depends(get_openai_client)):
    """Create a new AI project with LLM-powered tool/agent suggestions."""
    try:
        # Get company and sector information
        company_result = await db.execute(
            select(db_module.CompanyModel, db_module.SectorModel.name.label("sector_name"))
            .join(db_module.SectorModel)
            .where(db_module.CompanyModel.id == project.company_id)
        )
        company_with_sector = company_result.first()
        
        if not company_with_sector:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company, sector_name = company_with_sector
        
        # Create the project with basic information
        basic_project = await project_management.create_project(
            db=db,
            title=project.title,
            department_name=project.department,
            goal=project.goal,
            description=project.description,
            expected_value=project.expected_value,
            company_id=project.company_id,
            solution_ids=project.solution_ids
        )
        
        # If solution_ids were provided, make sure the project has those agents associated
        if project.solution_ids and len(project.solution_ids) > 0:
            # Ensure the solution_ids are properly associated with the project
            for agent_id in project.solution_ids:
                # Check if relationship already exists
                result = await db.execute(
                    select(db_module.ProjectSolutionModel)
                    .where(
                        db_module.ProjectSolutionModel.project_id == basic_project["id"],
                        db_module.ProjectSolutionModel.agent_id == agent_id
                    )
                )
                existing = result.scalars().first()
                
                if not existing:
                    # Create the association
                    new_solution = db_module.ProjectSolutionModel(
                        project_id=basic_project["id"],
                        agent_id=agent_id
                    )
                    db.add(new_solution)
            
            await db.commit()
        
        # If project description is substantial, analyze it with LLM
        if project.description and len(project.description) > 50:
            try:
                # Create project analyzer
                analyzer = ProjectAnalyzer(openai_client)
                
                # Analyze the project
                analysis = await analyzer.analyze_project(
                    title=project.title,
                    description=project.description,
                    company_name=company.name,
                    sector_name=sector_name
                )
                
                # Generate agent personality
                personality = await analyzer.generate_agent_personality(analysis)
                
                # Add analysis to project
                basic_project["analysis"] = analysis
                basic_project["suggested_personality"] = personality
                
                # Update project with suggested configuration only if not skipped
                config = analysis["agent_configuration"]
                updates = {}
                
                if "is_scheduled" in config:
                    updates["is_scheduled"] = config["is_scheduled"]
                
                if "schedule_frequency" in config:
                    updates["schedule_frequency"] = config["schedule_frequency"]
                
                # Only set Slack channel if Slack integration is not skipped
                if "slack_channel" in config and not project.skip_slack_integration:
                    updates["slack_channel"] = config["slack_channel"]
                
                if updates:
                    await project_management.update_project(db, basic_project["id"], updates)
                
                # Add flags to indicate if steps were skipped
                basic_project["skip_data_integration"] = project.skip_data_integration
                basic_project["skip_slack_integration"] = project.skip_slack_integration
                
            except Exception as e:
                print(f"Error performing LLM analysis: {str(e)}")
                # Continue without analysis if it fails
        
        # Fetch the associated agents to include in the response
        if basic_project["id"]:
            agents_result = await db.execute(
                select(db_module.AgentModel)
                .join(db_module.ProjectSolutionModel, db_module.ProjectSolutionModel.agent_id == db_module.AgentModel.id)
                .where(db_module.ProjectSolutionModel.project_id == basic_project["id"])
            )
            agents = agents_result.scalars().all()
            
            if agents:
                basic_project["agents"] = [{
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.role
                } for agent in agents]
        
        return basic_project
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@app.get("/projects/{project_id}", response_model=Dict[str, Any])
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """Get a project by ID."""
    try:
        project = await project_management.get_project_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project: {str(e)}")

@app.put("/projects/{project_id}", response_model=Dict[str, Any])
async def update_project(project_id: int, project: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    """Update a project."""
    try:
        updates = project.dict(exclude_unset=True)
        
        # Parse target date if provided
        if "target_date" in updates and updates["target_date"]:
            try:
                updates["target_date"] = datetime.datetime.fromisoformat(updates["target_date"])
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid target date format. Use ISO format (YYYY-MM-DD).")
        
        result = await project_management.update_project(db, project_id, updates)
        if not result:
            raise HTTPException(status_code=404, detail="Project not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")

@app.delete("/projects/{project_id}")
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a project."""
    try:
        success = await project_management.delete_project(db, project_id)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

# Add endpoints for companies and sectors
@app.get("/companies", response_model=List[CompanyResponse])
async def get_companies(db: AsyncSession = Depends(get_db)):
    """Get all companies."""
    try:
        # Query all companies with sector information
        result = await db.execute(
            select(db_module.CompanyModel, db_module.SectorModel.name.label("sector_name"))
            .join(db_module.SectorModel)
        )
        companies_with_sectors = result.all()
        
        # Format response
        return [
            {
                "id": company.id,
                "name": company.name,
                "sector_id": company.sector_id,
                "sector_name": sector_name,
                "description": company.description,
                "created_at": company.created_at.isoformat(),
                "updated_at": company.updated_at.isoformat()
            }
            for company, sector_name in companies_with_sectors
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get companies: {str(e)}")

@app.get("/sectors", response_model=List[SectorResponse])
async def get_sectors(db: AsyncSession = Depends(get_db)):
    """Get all sectors with company counts."""
    try:
        # Query all sectors
        result = await db.execute(select(db_module.SectorModel))
        sectors = result.scalars().all()
        
        # Get company counts for each sector
        sector_responses = []
        for sector in sectors:
            # Count companies in this sector
            company_count = await db.execute(
                select(func.count(db_module.CompanyModel.id))
                .where(db_module.CompanyModel.sector_id == sector.id)
            )
            count = company_count.scalar()
            
            sector_responses.append({
                "id": sector.id,
                "name": sector.name,
                "description": sector.description,
                "company_count": count,
                "created_at": sector.created_at.isoformat(),
                "updated_at": sector.updated_at.isoformat()
            })
        
        return sector_responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sectors: {str(e)}")

@app.get("/companies/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: int, db: AsyncSession = Depends(get_db)):
    """Get a company by ID."""
    try:
        # Query company with sector information
        result = await db.execute(
            select(db_module.CompanyModel, db_module.SectorModel.name.label("sector_name"))
            .join(db_module.SectorModel)
            .where(db_module.CompanyModel.id == company_id)
        )
        company_with_sector = result.first()
        
        if not company_with_sector:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company, sector_name = company_with_sector
        
        # Format response
        return {
            "id": company.id,
            "name": company.name,
            "sector_id": company.sector_id,
            "sector_name": sector_name,
            "description": company.description,
            "created_at": company.created_at.isoformat(),
            "updated_at": company.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get company: {str(e)}")

# Data corpus uploads
@app.post("/data-corpus/upload")
async def upload_data_corpus(
    file: UploadFile, 
    name: str = Form(...),
    description: str = Form(""),
    company_id: int = Form(...),
    is_sector_wide: bool = Form(False),
    db: AsyncSession = Depends(get_db)
):
    """Upload a data file to a company or sector corpus."""
    try:
        # Verify the company exists
        company_result = await db.execute(
            select(db_module.CompanyModel).where(db_module.CompanyModel.id == company_id)
        )
        company = company_result.scalars().first()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get sector_id from company
        sector_id = company.sector_id
        
        # Create data directory if it doesn't exist
        data_dir = "data/corpus"
        company_dir = f"{data_dir}/company_{company_id}"
        sector_dir = f"{data_dir}/sector_{sector_id}"
        
        # Create the appropriate directory based on is_sector_wide
        target_dir = sector_dir if is_sector_wide else company_dir
        os.makedirs(target_dir, exist_ok=True)
        
        # Save the file
        file_path = f"{target_dir}/{file.filename}"
        
        # Read file content
        contents = await file.read()
        
        # Validate that content is not empty
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Save the file
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Create data corpus entry in database
        new_corpus = db_module.DataCorpusModel(
            name=name,
            description=description,
            file_path=file_path,
            company_id=None if is_sector_wide else company_id,
            sector_id=sector_id if is_sector_wide else None,
            is_sector_wide=is_sector_wide
        )
        db.add(new_corpus)
        await db.commit()
        await db.refresh(new_corpus)
        
        return {
            "id": new_corpus.id,
            "name": new_corpus.name,
            "file_path": new_corpus.file_path,
            "is_sector_wide": new_corpus.is_sector_wide,
            "created_at": new_corpus.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload data corpus: {str(e)}")

@app.get("/company/{company_id}/data")
async def get_company_data(company_id: int, db: AsyncSession = Depends(get_db)):
    """Get all data available to a company (both company-specific and sector-wide)."""
    try:
        # Verify the company exists
        company_result = await db.execute(
            select(db_module.CompanyModel).where(db_module.CompanyModel.id == company_id)
        )
        company = company_result.scalars().first()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get company-specific data
        company_data_result = await db.execute(
            select(db_module.DataCorpusModel)
            .where(db_module.DataCorpusModel.company_id == company_id)
        )
        company_data = company_data_result.scalars().all()
        
        # Get sector-wide data for the company's sector
        sector_data_result = await db.execute(
            select(db_module.DataCorpusModel)
            .where(db_module.DataCorpusModel.sector_id == company.sector_id)
            .where(db_module.DataCorpusModel.is_sector_wide == True)
        )
        sector_data = sector_data_result.scalars().all()
        
        # Format response
        return {
            "company_data": [
                {
                    "id": data.id,
                    "name": data.name,
                    "description": data.description,
                    "file_path": data.file_path,
                    "created_at": data.created_at.isoformat()
                }
                for data in company_data
            ],
            "sector_data": [
                {
                    "id": data.id,
                    "name": data.name,
                    "description": data.description,
                    "file_path": data.file_path,
                    "created_at": data.created_at.isoformat()
                }
                for data in sector_data
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get company data: {str(e)}")

# Project analysis endpoints
@app.post("/projects/analyze", response_model=ProjectAnalysisResponse)
async def analyze_project(
    request: ProjectAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    openai_client: AsyncOpenAI = Depends(get_openai_client)
):
    """Analyze a project description and suggest appropriate tools and agent configuration."""
    try:
        # Get company and sector information
        result = await db.execute(
            select(db_module.CompanyModel, db_module.SectorModel.name.label("sector_name"))
            .join(db_module.SectorModel)
            .where(db_module.CompanyModel.id == request.company_id)
        )
        company_with_sector = result.first()
        
        if not company_with_sector:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company, sector_name = company_with_sector
        
        # Create project analyzer
        analyzer = ProjectAnalyzer(openai_client)
        
        # Analyze the project
        analysis = await analyzer.analyze_project(
            title=request.title,
            description=request.description,
            company_name=company.name,
            sector_name=sector_name
        )
        
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze project: {str(e)}")

# Add new endpoints for agent and tool generation
@app.post("/generate-agent", response_model=Dict[str, Any])
async def generate_agent(
    request: AgentGenerationRequest,
    db: AsyncSession = Depends(get_db),
    openai_client: AsyncOpenAI = Depends(get_openai_client)
):
    """Generate a specialized agent for a project using LLM."""
    try:
        # Get company and sector information
        result = await db.execute(
            select(db_module.CompanyModel, db_module.SectorModel.name.label("sector_name"))
            .join(db_module.SectorModel)
            .where(db_module.CompanyModel.id == request.company_id)
        )
        company_with_sector = result.first()
        
        if not company_with_sector:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company, sector_name = company_with_sector
        
        # Create agent generator
        generator = AgentGenerator(openai_client)
        
        # Generate specialized agent
        agent = await generator.generate_agent(
            project_title=request.project_title,
            project_description=request.project_description,
            company_name=company.name,
            sector_name=sector_name,
            problem_type=request.problem_type,
            suggested_tools=request.suggested_tools,
            db_session=db
        )
        
        return agent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate agent: {str(e)}")

# Also add a simplified version for the frontend to use
@app.post("/api/generate-agent", response_model=Dict[str, Any])
async def generate_agent_api(
    request: AgentGenerationRequest,
    db: AsyncSession = Depends(get_db),
    openai_client: AsyncOpenAI = Depends(get_openai_client)
):
    """Alternative endpoint for generating a specialized agent - works with frontend."""
    return await generate_agent(request, db, openai_client)

@app.post("/generate-tool", response_model=Dict[str, Any])
async def generate_tool(
    request: ToolGenerationRequest,
    db: AsyncSession = Depends(get_db),
    openai_client: AsyncOpenAI = Depends(get_openai_client)
):
    """Generate a custom tool based on project requirements."""
    try:
        # Create agent generator
        generator = AgentGenerator(openai_client)
        
        # Generate custom tool
        tool = await generator.generate_custom_tool(
            tool_name=request.tool_name,
            tool_description=request.tool_description,
            project_context=request.project_context,
            db_session=db
        )
        
        return tool
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate tool: {str(e)}")

# Update the project creation endpoint to optionally create specialized agents
@app.post("/projects/create-with-agent", response_model=Dict[str, Any])
async def create_project_with_agent(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    openai_client: AsyncOpenAI = Depends(get_openai_client)
):
    """Create a new AI project with a specialized agent generated using LLM."""
    try:
        # First check if we have a recommended architecture to use
        recommended_architecture = None
        if hasattr(project, 'recommended_architecture') and project.recommended_architecture:
            recommended_architecture = project.recommended_architecture
        
        # Create basic project first (without agents for now)
        project_without_agents = ProjectCreate(**{
            **project.dict(),
            "solution_ids": []  # Start with empty solution_ids
        })
        basic_project = await create_project(project_without_agents, db, openai_client)
        
        # Get company and sector information
        result = await db.execute(
            select(db_module.CompanyModel, db_module.SectorModel.name.label("sector_name"))
            .join(db_module.SectorModel)
            .where(db_module.CompanyModel.id == project.company_id)
        )
        company_with_sector = result.first()
        
        if not company_with_sector:
            return basic_project  # Return basic project if company not found
        
        company, sector_name = company_with_sector
        
        # Create agent generator
        generator = AgentGenerator(openai_client)
        generated_agents = []
        
        try:
            # Generate agents based on architecture or analysis
            if recommended_architecture and recommended_architecture.get("agents") and len(recommended_architecture["agents"]) > 0:
                # Create multiple agents from recommended architecture
                for agent_spec in recommended_architecture["agents"]:
                    try:
                        # Generate agent with specified role, tools, etc.
                        agent = await generator.generate_agent(
                            project_title=project.title,
                            project_description=project.description,
                            company_name=company.name,
                            sector_name=sector_name,
                            problem_type=agent_spec.get("role", "General Assistant"),
                            suggested_tools=agent_spec.get("tools", []),
                            db_session=db
                        )
                        
                        if agent and "id" in agent:
                            generated_agents.append(agent)
                    except Exception as e:
                        print(f"Error generating agent for role {agent_spec.get('role')}: {str(e)}")
                        # Continue with next agent in case of error
            else:
                # Get project analysis
                analyzer = ProjectAnalyzer(openai_client)
                analysis = await analyzer.analyze_project(
                    title=project.title,
                    description=project.description,
                    company_name=company.name,
                    sector_name=sector_name
                )
                
                # Generate a single specialized agent
                try:
                    agent = await generator.generate_agent(
                        project_title=project.title,
                        project_description=project.description,
                        company_name=company.name,
                        sector_name=sector_name,
                        problem_type=analysis["analysis"]["problem_type"],
                        suggested_tools=analysis["agent_configuration"]["tools"],
                        db_session=db
                    )
                    
                    if agent and "id" in agent:
                        generated_agents.append(agent)
                except Exception as e:
                    print(f"Error generating agent: {str(e)}")
                    # If agent generation fails, still return the basic project
            
            # Link agents to project
            solution_ids = []
            for agent in generated_agents:
                if "id" in agent:
                    solution_ids.append(agent["id"])
                    
                    # Create the relationship in the database
                    new_solution = db_module.ProjectSolutionModel(
                        project_id=basic_project["id"],
                        agent_id=agent["id"]
                    )
                    db.add(new_solution)
            
            await db.commit()
            
            # Update project with agents
            if solution_ids:
                # Update project with agent IDs
                await project_management.update_project(
                    db,
                    basic_project["id"],
                    {"solution_ids": solution_ids}
                )
                
                # Add agents to project response
                basic_project["specialized_agents"] = generated_agents
                basic_project["solution_ids"] = solution_ids
            
            # Add flags to indicate if steps were skipped
            basic_project["skip_data_integration"] = project.skip_data_integration
            basic_project["skip_slack_integration"] = project.skip_slack_integration
            
            # If using a multi-agent architecture, store that information
            if recommended_architecture and recommended_architecture.get("architecture_type") in ["sequential", "multi_agent_team"]:
                # Create a multi-agent system if we have multiple agents
                if len(generated_agents) > 1:
                    # Get agent names
                    agent_names = [agent["name"] for agent in generated_agents if "name" in agent]
                    
                    if agent_names:
                        # Determine triage agent (first agent in sequential workflow or designated triage in team)
                        triage_agent = agent_names[0]
                        
                        # Create system with appropriate connections based on architecture type
                        connections = []
                        if recommended_architecture.get("architecture_type") == "sequential":
                            # Create sequential connections
                            for i in range(len(agent_names) - 1):
                                connections.append({
                                    "source": agent_names[i],
                                    "target": agent_names[i + 1],
                                    "condition": "next"
                                })
                        
                        # Create the multi-agent system
                        try:
                            from uuid import uuid4
                            system_id = f"mas_{uuid4().hex[:8]}"
                            
                            new_system = db_module.MultiAgentSystemModel(
                                id=system_id,
                                name=f"{project.title} System",
                                description=f"Auto-generated system for project: {project.title}",
                                agents=agent_names,
                                triage_agent=triage_agent,
                                connections=connections
                            )
                            db.add(new_system)
                            await db.commit()
                            
                            # Add system info to response
                            basic_project["multi_agent_system"] = {
                                "id": system_id,
                                "name": new_system.name,
                                "agents": agent_names,
                                "triage_agent": triage_agent
                            }
                        except Exception as e:
                            print(f"Error creating multi-agent system: {str(e)}")
                            # If multi-agent system creation fails, continue without it
                            await db.rollback()
            
        except Exception as agent_error:
            # If something goes wrong during agent creation, roll back and return the basic project
            print(f"Error during agent creation process: {str(agent_error)}")
            await db.rollback()
        
        return basic_project
    except Exception as e:
        # Try to rollback the session if there's an error
        try:
            await db.rollback()
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to create project with agent: {str(e)}")

# Project analysis with additional steps for architecture recommendation
@app.post("/projects/generate-questions", response_model=ProjectFollowupQuestionsResponse)
async def generate_followup_questions(
    request: ProjectFollowupQuestionsRequest,
    db: AsyncSession = Depends(get_db),
    openai_client: AsyncOpenAI = Depends(get_openai_client)
):
    """Generate follow-up questions based on project description to clarify requirements."""
    try:
        # Get company and sector information
        result = await db.execute(
            select(db_module.CompanyModel, db_module.SectorModel.name.label("sector_name"))
            .join(db_module.SectorModel)
            .where(db_module.CompanyModel.id == request.company_id)
        )
        company_with_sector = result.first()
        
        if not company_with_sector:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company, sector_name = company_with_sector
        
        # Create project analyzer
        analyzer = ProjectAnalyzer(openai_client)
        
        # Generate follow-up questions
        questions = await analyzer.generate_followup_questions(
            title=request.title,
            description=request.description,
            company_name=company.name,
            sector_name=sector_name
        )
        
        return {"questions": questions}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate follow-up questions: {str(e)}")

@app.post("/projects/recommend-architecture", response_model=ArchitectureRecommendationResponse)
async def recommend_agent_architecture(
    request: ArchitectureRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    openai_client: AsyncOpenAI = Depends(get_openai_client)
):
    """Recommend agent architecture based on project description and question answers."""
    try:
        # Get company and sector information
        result = await db.execute(
            select(db_module.CompanyModel, db_module.SectorModel.name.label("sector_name"))
            .join(db_module.SectorModel)
            .where(db_module.CompanyModel.id == request.company_id)
        )
        company_with_sector = result.first()
        
        if not company_with_sector:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company, sector_name = company_with_sector
        
        # Create project analyzer
        analyzer = ProjectAnalyzer(openai_client)
        
        # Recommend agent architecture
        architecture = await analyzer.recommend_agent_architecture(
            title=request.title,
            description=request.description,
            company_name=company.name,
            sector_name=sector_name,
            question_answers=request.question_answers
        )
        
        return architecture
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recommend agent architecture: {str(e)}")

@app.post("/projects/{project_id}/interact", response_model=Dict[str, Any])
async def interact_with_project(
    project_id: int,
    request: MessageRequest,
    db: AsyncSession = Depends(get_db),
    openai_client: AsyncOpenAI = Depends(get_openai_client)
):
    """
    Interact with an AI project by routing the message to the appropriate agent(s).
    For single agent projects, this simply forwards to that agent.
    For multi-agent projects, it routes through the appropriate multi-agent system.
    """
    try:
        # Get the project
        project_result = await db.execute(
            select(db_module.ProjectModel).where(db_module.ProjectModel.id == project_id)
        )
        project = project_result.scalars().first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get associated agents
        agents_result = await db.execute(
            select(db_module.AgentModel)
            .join(db_module.ProjectSolutionModel, db_module.ProjectSolutionModel.agent_id == db_module.AgentModel.id)
            .where(db_module.ProjectSolutionModel.project_id == project_id)
        )
        agents = agents_result.scalars().all()
        
        if not agents:
            raise HTTPException(status_code=404, detail="No agents found for this project")
        
        # Check if this project has a multi-agent system
        system_result = await db.execute(
            select(db_module.MultiAgentSystemModel)
            .where(
                # Check if all agents in the system match the project's agents
                db_module.MultiAgentSystemModel.agents.contains([agent.name for agent in agents])
            )
        )
        multi_agent_system = system_result.scalars().first()
        
        # Parse conversation ID if it's a string
        conversation_id = None
        if request.conversation_id:
            try:
                conversation_id = int(request.conversation_id)
            except ValueError:
                pass  # Keep it as None
        
        # Case 1: Multi-agent system
        if multi_agent_system and len(agents) > 1:
            # Route through multi-agent system
            return await interact_with_multi_agent_system_endpoint(
                system_id=multi_agent_system.id,
                request={
                    "message": request.message,
                    "conversation_id": conversation_id,
                    "user_id": request.user_id
                },
                db=db
            )
        
        # Case 2: Sequential workflow (multiple agents, but no formal multi-agent system)
        elif len(agents) > 1:
            # First, check if there's an existing conversation for this project
            if not conversation_id:
                # Check for existing project conversations before creating a new one
                existing_conversations_result = await db.execute(
                    select(db_module.ConversationModel)
                    .where(db_module.ConversationModel.project_id == project_id)
                    .order_by(db_module.ConversationModel.updated_at.desc())
                    .limit(1)
                )
                existing_conversation = existing_conversations_result.scalars().first()
                
                if existing_conversation:
                    # Use the most recent conversation 
                    conversation = existing_conversation
                    conversation_id = existing_conversation.id
                else:
                    # Create new conversation only if no existing ones
                    conversation = db_module.ConversationModel(
                        agent_id=agents[0].id,  # Use first agent as primary
                        title=f"Project {project.title} - {request.message[:30]}...",
                        project_id=project_id
                    )
                    db.add(conversation)
                    await db.commit()
                    await db.refresh(conversation)
                    conversation_id = conversation.id
            else:
                # Use existing conversation if ID was provided
                conversation_result = await db.execute(
                    select(db_module.ConversationModel)
                    .where(db_module.ConversationModel.id == conversation_id)
                )
                conversation = conversation_result.scalars().first()
                
                if not conversation:
                    # Conversation ID was invalid, create a new one
                    conversation = db_module.ConversationModel(
                        agent_id=agents[0].id,  # Use first agent as primary
                        title=f"Project {project.title} - {request.message[:30]}...",
                        project_id=project_id
                    )
                    db.add(conversation)
                    await db.commit()
                    await db.refresh(conversation)
                    conversation_id = conversation.id
            
            # Add user message to conversation
            user_message = db_module.MessageModel(
                conversation_id=conversation_id,
                role="user",
                content=request.message
            )
            db.add(user_message)
            await db.commit()
            
            # Make sure the agent has access to the OpenAI client
            for agent_name, agent_obj in agent_utils.agents_store.items():
                if hasattr(agent_obj, 'model') and hasattr(agent_obj.model, 'openai_client'):
                    agent_obj.model.openai_client = openai_client
            
            # Process sequentially through all agents
            current_message = request.message
            final_response = None
            
            for i, agent in enumerate(agents):
                try:
                    # Pass message to this agent
                    try:
                        agent_response = await agent_utils.interact_with_agent_raw(
                            agent_name=agent.name,
                            message=current_message,
                            conversation_id=conversation_id  # Use the same conversation for all agents
                        )
                    except Exception as api_error:
                        # Handle API errors specifically
                        error_msg = str(api_error)
                        if "invalid_api_key" in error_msg or "authentication" in error_msg.lower() or "401" in error_msg:
                            raise HTTPException(
                                status_code=500, 
                                detail="API authentication error. Please check your API keys in the environment variables."
                            )
                        # Re-raise if it's not an authentication error
                        raise
                    
                    # Update current message for next agent in sequence
                    current_message = agent_response
                    
                    # Store intermediate response in database but don't return to user
                    intermediate_message = db_module.MessageModel(
                        conversation_id=conversation_id,
                        role="intermediate",  # Mark all intermediate messages consistently
                        content=agent_response,
                        message_metadata={"agent_name": agent.name, "sequence_position": i}
                    )
                    db.add(intermediate_message)
                    await db.commit()
                    
                    # Only keep final response to return to user
                    if i == len(agents) - 1:
                        final_response = agent_response
                        
                        # Add final response to conversation
                        final_message = db_module.MessageModel(
                            conversation_id=conversation_id,
                            role="assistant",
                            content=final_response
                        )
                        db.add(final_message)
                        await db.commit()
                except Exception as e:
                    print(f"Error with agent {agent.name} in sequence: {str(e)}")
                    # If an agent fails, break the chain and return error
                    error_message = f"Error processing with agent {agent.name}: {str(e)}"
                    error_db_message = db_module.MessageModel(
                        conversation_id=conversation_id,
                        role="system",
                        content=error_message
                    )
                    db.add(error_db_message)
                    await db.commit()
                    return {
                        "response": error_message,
                        "conversation_id": str(conversation_id),
                        "error": str(e)
                    }
            
            return {
                "response": final_response,
                "conversation_id": str(conversation_id)
            }
        
        # Case 3: Single agent (or fallback)
        # Use the first agent
        primary_agent = agents[0]
        print(f"Using single agent: {primary_agent.name} for project {project_id}")
        
        # First check for existing conversations for this project
        if not conversation_id:
            # Look for existing conversations for this project
            existing_conversations_result = await db.execute(
                select(db_module.ConversationModel)
                .where(db_module.ConversationModel.project_id == project_id)
                .order_by(db_module.ConversationModel.updated_at.desc())
                .limit(1)
            )
            existing_conversation = existing_conversations_result.scalars().first()
            
            if existing_conversation:
                conversation_id = existing_conversation.id
                print(f"Found existing conversation: {conversation_id} for project {project_id}")
            else:
                print(f"No existing conversations found for project {project_id}")
        else:
            print(f"Using provided conversation_id: {conversation_id}")
        
        # Create message response using the agent
        try:
            print(f"Sending message to agent {primary_agent.name} for project {project_id}")
            response_data = await agent_utils.interact_with_agent(
                agent_name=primary_agent.name,
                message=request.message,
                session=db,
                conversation_id=conversation_id,
                project_id=project_id
            )
            
            # Check if there was an error
            if "error" in response_data:
                print(f"Error in agent response: {response_data.get('error')}")
            
            # Update the conversation to link it with the project
            if isinstance(response_data, dict) and "conversation_id" in response_data:
                try:
                    conversation_id = int(response_data["conversation_id"])
                    conversation_result = await db.execute(
                        select(db_module.ConversationModel)
                        .where(db_module.ConversationModel.id == conversation_id)
                    )
                    conversation = conversation_result.scalars().first()
                    
                    if conversation and not conversation.project_id:
                        print(f"Linking conversation {conversation_id} to project {project_id}")
                        conversation.project_id = project_id
                        await db.commit()
                except (ValueError, TypeError) as e:
                    print(f"Error linking conversation to project: {str(e)}")
                    # If conversion fails, just ignore
                    pass
            
            return response_data
        except Exception as e:
            error_msg = f"Error in project interaction with agent {primary_agent.name}: {str(e)}"
            print(error_msg)
            # Print stack trace for debugging
            import traceback
            traceback.print_exc()
            
            # Still try to create a conversation if needed to record the error
            if not conversation_id:
                new_conversation = db_module.ConversationModel(
                    agent_id=primary_agent.id,
                    title=f"Error with {primary_agent.name} - {datetime.now().isoformat()}",
                    project_id=project_id
                )
                db.add(new_conversation)
                await db.commit()
                await db.refresh(new_conversation)
                conversation_id = new_conversation.id
            
            # Record the error message
            error_message = db_module.MessageModel(
                conversation_id=conversation_id,
                role="system",
                content=error_msg
            )
            db.add(error_message)
            await db.commit()
            
            # Return error response
            return {
                "response": error_msg,
                "conversation_id": conversation_id,
                "error": "agent_error"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to interact with project: {str(e)}")

@app.get("/projects/{project_id}/conversations", response_model=List[Dict[str, Any]])
async def get_project_conversations(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all conversations for a project by querying all its linked agents."""
    try:
        # Get the project
        project_result = await db.execute(
            select(db_module.ProjectModel).where(db_module.ProjectModel.id == project_id)
        )
        project = project_result.scalars().first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get associated agents
        agents_result = await db.execute(
            select(db_module.AgentModel)
            .join(db_module.ProjectSolutionModel, db_module.ProjectSolutionModel.agent_id == db_module.AgentModel.id)
            .where(db_module.ProjectSolutionModel.project_id == project_id)
        )
        agents = agents_result.scalars().all()
        
        if not agents:
            return []
        
        # Check if this project has a multi-agent system
        system_result = await db.execute(
            select(db_module.MultiAgentSystemModel)
            .where(
                # Check if all agents in the system match the project's agents
                db_module.MultiAgentSystemModel.agents.contains([agent.name for agent in agents])
            )
        )
        multi_agent_system = system_result.scalars().first()
        
        # If multi-agent system exists, get those conversations
        if multi_agent_system:
            mas_conversations_result = await db.execute(
                select(db_module.MultiAgentConversationModel)
                .where(db_module.MultiAgentConversationModel.system_id == multi_agent_system.id)
                .order_by(db_module.MultiAgentConversationModel.created_at.desc())
            )
            mas_conversations = mas_conversations_result.scalars().all()
            
            return [{
                "id": str(conv.id),
                "title": conv.title,
                "type": "multi_agent",
                "system_id": conv.system_id,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat()
            } for conv in mas_conversations]
        
        # Otherwise, get conversations from the primary agent
        if agents:
            primary_agent = agents[0]
            agent_conversations_result = await db.execute(
                select(db_module.ConversationModel)
                .where(db_module.ConversationModel.agent_id == primary_agent.id)
                .order_by(db_module.ConversationModel.created_at.desc())
            )
            agent_conversations = agent_conversations_result.scalars().all()
            
            return [{
                "id": str(conv.id),
                "title": conv.title,
                "type": "single_agent",
                "agent_id": primary_agent.id,
                "agent_name": primary_agent.name,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat()
            } for conv in agent_conversations]
        
        return []
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project conversations: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)