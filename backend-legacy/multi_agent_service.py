import uuid
import datetime
import json
import os
from typing import List, Dict, Optional, Any
import agent_utils
from models import AgentConnection, MultiAgentSystem
import database as db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# In-memory storage for multi-agent systems (for runtime use)
multi_agent_systems = {}

async def create_multi_agent_system(
    session: AsyncSession,
    name: str, 
    description: str, 
    agent_names: List[str], 
    triage_agent_name: str, 
    connections: List[AgentConnection] = None
) -> MultiAgentSystem:
    """
    Create a new multi-agent system
    """
    if not connections:
        connections = []
    
    # Validate that all agents exist
    agents = agent_utils.get_all_agents()
    for agent_name in agent_names:
        if agent_name not in agents:
            raise ValueError(f"Agent {agent_name} does not exist")
    
    # Validate that triage agent exists and is in the agent list
    if triage_agent_name not in agents:
        raise ValueError(f"Triage agent {triage_agent_name} does not exist")
    if triage_agent_name not in agent_names:
        raise ValueError(f"Triage agent must be included in the agent list")
    
    # Create multi-agent system
    system_id = str(uuid.uuid4())
    created_at = datetime.datetime.now().isoformat()
    
    system = MultiAgentSystem(
        id=system_id,
        name=name,
        description=description,
        agents=agent_names,
        triage_agent=triage_agent_name,
        connections=connections,
        created_at=created_at
    )
    
    # Store in memory
    multi_agent_systems[system_id] = system
    
    # Store in database
    db_system = db.MultiAgentSystemModel(
        id=system_id,
        name=name,
        description=description,
        agents=agent_names,
        triage_agent=triage_agent_name,
        connections=[conn.dict() for conn in connections],
        created_at=datetime.datetime.fromisoformat(created_at)
    )
    session.add(db_system)
    await session.commit()
    
    return system

def get_multi_agent_system(system_id: str) -> Optional[MultiAgentSystem]:
    """
    Get a multi-agent system by ID from memory
    """
    return multi_agent_systems.get(system_id)

async def get_multi_agent_system_from_db(
    system_id: str,
    db_session: AsyncSession
) -> Optional[db.MultiAgentSystemModel]:
    """
    Get a multi-agent system from the database
    
    Args:
        system_id: ID of the multi-agent system
        db_session: Database session
        
    Returns:
        The multi-agent system model or None if not found
    """
    if not db_session:
        return None
        
    result = await db_session.execute(
        select(db.MultiAgentSystemModel).where(db.MultiAgentSystemModel.id == system_id)
    )
    return result.scalar_one_or_none()

def get_all_multi_agent_systems() -> Dict[str, MultiAgentSystem]:
    """
    Get all multi-agent systems from memory
    """
    return multi_agent_systems

async def get_all_multi_agent_systems_from_db(
    db_session: AsyncSession
) -> List[db.MultiAgentSystemModel]:
    """
    Get all multi-agent systems from the database
    
    Args:
        db_session: Database session
        
    Returns:
        List of multi-agent system models
    """
    if not db_session:
        return []
        
    result = await db_session.execute(
        select(db.MultiAgentSystemModel).order_by(db.MultiAgentSystemModel.created_at.desc())
    )
    return result.scalars().all()

async def update_multi_agent_system(
    session: AsyncSession,
    system_id: str, 
    name: str = None, 
    description: str = None, 
    agent_names: List[str] = None, 
    triage_agent_name: str = None,
    connections: List[AgentConnection] = None
) -> Optional[MultiAgentSystem]:
    """
    Update a multi-agent system
    """
    # Check if system exists in memory
    if system_id not in multi_agent_systems:
        return None
    
    # Get system from memory
    system = multi_agent_systems[system_id]
    
    # Get system from database
    db_system = await get_multi_agent_system_from_db(system_id, session)
    if not db_system:
        return None
    
    # Update memory and database
    if name is not None:
        system.name = name
        db_system.name = name
    
    if description is not None:
        system.description = description
        db_system.description = description
    
    if agent_names is not None:
        # Validate that all agents exist
        agents = agent_utils.get_all_agents()
        for agent_name in agent_names:
            if agent_name not in agents:
                raise ValueError(f"Agent {agent_name} does not exist")
        system.agents = agent_names
        db_system.agents = agent_names
    
    if triage_agent_name is not None:
        # Validate that triage agent exists and is in the agent list
        agents = agent_utils.get_all_agents()
        if triage_agent_name not in agents:
            raise ValueError(f"Triage agent {triage_agent_name} does not exist")
        if triage_agent_name not in system.agents:
            raise ValueError(f"Triage agent must be included in the agent list")
        system.triage_agent = triage_agent_name
        db_system.triage_agent = triage_agent_name
    
    if connections is not None:
        system.connections = connections
        db_system.connections = [conn.dict() for conn in connections]
    
    # Update timestamp
    db_system.updated_at = datetime.datetime.utcnow()
    
    # Save to database
    await session.commit()
    
    return system

async def delete_multi_agent_system(session: AsyncSession, system_id: str) -> bool:
    """
    Delete a multi-agent system
    """
    # Delete from memory
    if system_id in multi_agent_systems:
        del multi_agent_systems[system_id]
    
    # Delete from database
    db_system = await get_multi_agent_system_from_db(system_id, session)
    if db_system:
        await session.delete(db_system)
        await session.commit()
        return True
    
    return False

async def initialize_multi_agent_systems(db_session: AsyncSession):
    """
    Load all multi-agent systems from the database into memory
    
    Args:
        db_session: Database session
    """
    global multi_agent_systems
    
    # Clear existing systems
    multi_agent_systems = {}
    
    # Get all systems from database
    systems = await get_all_multi_agent_systems_from_db(db_session)
    
    # Load into memory
    for system in systems:
        system_dict = db.model_to_dict(system)
        multi_agent_systems[system.id] = system_dict
        
    print(f"Loaded {len(multi_agent_systems)} multi-agent systems from database")

async def save_multi_agent_message(
    db_session: AsyncSession,
    role: str,
    content: str,
    conversation_id: Optional[int] = None,
    system_id: Optional[str] = None,
    user_id: str = "default_user",
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Save a message in a multi-agent conversation
    
    Args:
        db_session: Database session
        role: Message role (user, assistant, or agent name)
        content: Message content
        conversation_id: Optional conversation ID, will create a new one if not provided
        system_id: System ID (required if conversation_id not provided)
        user_id: User ID
        metadata: Additional metadata for the message
    
    Returns:
        conversation_id
    """
    if conversation_id is None:
        if system_id is None:
            raise ValueError("system_id is required when conversation_id is not provided")
        
        # Create a new conversation
        async with db_session.begin_nested():
            new_conversation = db.MultiAgentConversationModel(
                system_id=system_id,
                user_id=user_id,
                title=f"Conversation {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            db_session.add(new_conversation)
            await db_session.flush()
            conversation_id = new_conversation.id
        
        # Add the message to the conversation
        new_message = db.MultiAgentMessageModel(
            conversation_id=conversation_id,
            role=role,
            content=content,
            meta_data=metadata
        )
        db_session.add(new_message)
    
    return conversation_id

async def get_multi_agent_conversation_history(
    conversation_id: int,
    db_session: AsyncSession
) -> List[Dict[str, Any]]:
    """
    Get the history of a multi-agent conversation
    
    Args:
        conversation_id: ID of the conversation
        db_session: Database session
        
    Returns:
        List of messages in the conversation
    """
    if not db_session:
        return []
        
    # Get the conversation
    conversation = await db_session.execute(
        select(db.MultiAgentConversationModel).where(db.MultiAgentConversationModel.id == conversation_id)
    )
    conversation = conversation.scalar_one_or_none()
    
    if not conversation:
        return []
        
    # Get all messages in the conversation
    messages = await db_session.execute(
        select(db.MultiAgentMessageModel)
        .where(db.MultiAgentMessageModel.conversation_id == conversation_id)
        .order_by(db.MultiAgentMessageModel.timestamp)
    )
    messages = messages.scalars().all()
    
    # Convert to dictionaries
    result = []
    for message in messages:
        message_dict = db.model_to_dict(message)
        result.append(message_dict)
        
    return result

async def get_multi_agent_conversations(
    system_id: str,
    db_session: AsyncSession
) -> List[Dict[str, Any]]:
    """
    Get all conversations for a multi-agent system
    
    Args:
        system_id: ID of the multi-agent system
        db_session: Database session
        
    Returns:
        List of conversations for the multi-agent system
    """
    if not db_session:
        return []
        
    # Get all conversations for the system
    conversations = await db_session.execute(
        select(db.MultiAgentConversationModel)
        .where(db.MultiAgentConversationModel.system_id == system_id)
        .order_by(db.MultiAgentConversationModel.created_at.desc())
    )
    conversations = conversations.scalars().all()
    
    # Convert to dictionaries
    result = []
    for conversation in conversations:
        conversation_dict = db.model_to_dict(conversation)
        
        # Get the first few messages for preview
        messages = await db_session.execute(
            select(db.MultiAgentMessageModel)
            .where(db.MultiAgentMessageModel.conversation_id == conversation.id)
            .order_by(db.MultiAgentMessageModel.timestamp)
            .limit(3)
        )
        messages = messages.scalars().all()
        
        # Add message previews
        conversation_dict["message_previews"] = [db.model_to_dict(message) for message in messages]
        result.append(conversation_dict)
        
    return result

async def interact_with_multi_agent_system(
    system_id: str, 
    user_message: str, 
    user_id: str = "default_user",
    db_session: AsyncSession = None,
    conversation_id: Optional[int] = None
):
    """
    Send a message to a multi-agent system and get a response.
    
    Args:
        system_id: The ID of the multi-agent system
        user_message: The message from the user
        user_id: The ID of the user (for conversation tracking)
        db_session: Database session
        conversation_id: Optional ID of an existing conversation
        
    Returns:
        A response from the appropriate agent in the system
    """
    try:
        # Get the multi-agent system
        system = multi_agent_systems.get(system_id)
        if not system:
            if db_session:
                # Try to load from database
                system_model = await get_multi_agent_system_from_db(system_id, db_session)
                if system_model:
                    # Convert to dictionary and store in memory
                    system_dict = db.model_to_dict(system_model)
                    # Create a MultiAgentSystem object
                    system = MultiAgentSystem(
                        id=system_dict["id"],
                        name=system_dict["name"],
                        description=system_dict["description"],
                        agents=system_dict["agents"],
                        triage_agent=system_dict["triage_agent"],
                        connections=[AgentConnection(**conn) for conn in system_dict.get("connections", [])],
                        created_at=system_dict["created_at"].isoformat() if isinstance(system_dict["created_at"], datetime.datetime) else system_dict["created_at"]
                    )
                    multi_agent_systems[system_id] = system
                else:
                    return {"error": f"Multi-agent system with ID {system_id} not found"}
            else:
                return {"error": f"Multi-agent system with ID {system_id} not found"}
        
        # Access system properties consistently regardless of object type
        if isinstance(system, dict):
            triage_agent_name = system.get("triage_agent")
            available_agents = system.get("agents", [])
            system_connections = system.get("connections", [])
            system_name = system.get("name", "Multi-Agent System")
        else:
            # It's a MultiAgentSystem object
            triage_agent_name = system.triage_agent
            available_agents = system.agents
            system_connections = system.connections
            system_name = system.name
        
        if not triage_agent_name:
            return {"error": "No triage agent specified for this multi-agent system"}
        
        if not available_agents:
            return {"error": "No agents available in this multi-agent system"}
        
        # Get the triage agent from memory or database
        triage_agent = agent_utils.agents_store.get(triage_agent_name)
        if not triage_agent and db_session:
            # Try to load from database
            result = await db_session.execute(select(db.AgentModel).where(db.AgentModel.name == triage_agent_name))
            agent_model = result.scalars().first()
            
            if agent_model:
                # Agent exists in database but not in memory
                # We need to get the OpenAI client
                openai_client = agent_utils.get_openai_client()
                if openai_client:
                    triage_agent = agent_utils.create_agent(
                        name=agent_model.name,
                        role=agent_model.role,
                        personality=agent_model.personality,
                        tools=agent_model.tools,
                        openai_client=openai_client
                    )
                    agent_utils.agents_store[triage_agent_name] = triage_agent
        
        if not triage_agent:
            return {"error": f"Triage agent '{triage_agent_name}' not found"}
        
        # Create a prompt for the triage agent
        agent_descriptions = []
        for agent_name in available_agents:
            agent = agent_utils.agents_store.get(agent_name)
            if not agent and db_session:
                # Try to load from database
                result = await db_session.execute(select(db.AgentModel).where(db.AgentModel.name == agent_name))
                agent_model = result.scalars().first()
                
                if agent_model:
                    # We'll just use the database model for description
                    agent_descriptions.append(f"- {agent_name}: {agent_model.role} - {agent_model.personality}")
                    continue
            
            if agent:
                # Access agent properties safely
                handoff_desc = getattr(agent, 'handoff_description', f"{agent_name} agent")
                instructions = getattr(agent, 'instructions', "No specific instructions")
                agent_descriptions.append(f"- {agent_name}: {handoff_desc} - {instructions}")
            
        # Safety guardrails
        if "system" in user_message.lower() and any(term in user_message.lower() for term in ["prompt", "injection", "ignore", "previous"]):
            # This is a potential prompt injection attempt
            selected_agent_name = triage_agent_name
            reasoning = "Detected potential prompt injection attempt. Routing to triage agent for safe handling."
            response_message = "I cannot process that request as it appears to be attempting to manipulate the system. Please provide a legitimate query."
        else:
            # Normal processing
            triage_prompt = f"""
            You are the triage agent for a multi-agent system. Your job is to analyze the user's message and determine which agent is best suited to respond.
            
            Available agents:
            {chr(10).join(agent_descriptions)}
            
            User message: {user_message}
            
            First, analyze the user's message and determine which agent should respond. Provide your reasoning.
            Then, output the name of the selected agent exactly as it appears in the list above.
            
            Format your response as:
            Reasoning: <your analysis>
            Selected Agent: <agent_name>
            """
            
            # Get the triage agent's response directly
            try:
                triage_result = await agent_utils.Runner.run(triage_agent, triage_prompt)
                triage_response = triage_result.final_output
            except Exception as e:
                print(f"Error in triage: {str(e)}")
                triage_response = "Reasoning: Could not determine an appropriate agent. Using triage agent as fallback.\nSelected Agent: " + triage_agent_name
            
            # Parse the triage response to get the selected agent
            lines = triage_response.strip().split('\n')
            reasoning = ""
            selected_agent_name = ""
            
            for line in lines:
                if line.startswith("Reasoning:"):
                    reasoning = line[len("Reasoning:"):].strip()
                elif line.startswith("Selected Agent:"):
                    selected_agent_name = line[len("Selected Agent:"):].strip()
            
            # If no agent was selected, use the triage agent
            if not selected_agent_name or selected_agent_name not in available_agents:
                selected_agent_name = triage_agent_name
                if not reasoning:
                    reasoning = "Could not determine an appropriate agent. Using triage agent as fallback."
                    
            # Get the selected agent
            selected_agent = agent_utils.agents_store.get(selected_agent_name)
            if not selected_agent and db_session:
                # Try to load from database
                result = await db_session.execute(select(db.AgentModel).where(db.AgentModel.name == selected_agent_name))
                agent_model = result.scalars().first()
                
                if agent_model:
                    # Agent exists in database but not in memory
                    # We need to get the OpenAI client
                    openai_client = agent_utils.get_openai_client()
                    if openai_client:
                        selected_agent = agent_utils.create_agent(
                            name=agent_model.name,
                            role=agent_model.role,
                            personality=agent_model.personality,
                            tools=agent_model.tools,
                            openai_client=openai_client
                        )
                        agent_utils.agents_store[selected_agent_name] = selected_agent
            
            if not selected_agent:
                return {"error": f"Selected agent '{selected_agent_name}' not found"}
            
            # Get the response directly from the agent
            try:
                result = await agent_utils.Runner.run(selected_agent, user_message)
                response_message = result.final_output
            except Exception as e:
                return {"error": f"Error getting response from agent: {str(e)}"}
            
        # Get agent role safely for response metadata
        selected_agent_role = ""
        if selected_agent_name in agent_utils.agents_store:
            agent = agent_utils.agents_store[selected_agent_name]
            selected_agent_role = getattr(agent, 'handoff_description', "")
        
        # Return the response with metadata
        return {
            "role": "assistant",
            "content": response_message,
            "metadata": {
                "agent_name": selected_agent_name,
                "agent_role": selected_agent_role,
                "triage": {
                    "reasoning": reasoning,
                    "selected_agent": {
                        "name": selected_agent_name,
                        "reason": reasoning
                    }
                }
            },
            "conversation_id": conversation_id
        }
    
    except Exception as e:
        import traceback
        print(f"Error in interact_with_multi_agent_system: {str(e)}")
        print(traceback.format_exc())
        return {"error": f"An error occurred: {str(e)}"} 