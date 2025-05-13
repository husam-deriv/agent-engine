from pydantic import BaseModel
from typing import List, Dict, Optional, Any

class AgentConnection(BaseModel):
    """Defines a connection between two agents in a multi-agent system"""
    source_agent: str
    target_agent: str
    description: Optional[str] = None

class MultiAgentSystem(BaseModel):
    """Model for a multi-agent system"""
    id: Optional[str] = None
    name: str
    description: str
    agents: List[str]  # List of agent names in the system
    triage_agent: str  # Name of the triage agent
    connections: List[AgentConnection] = []  # Connections between agents
    created_at: Optional[str] = None
    
class MultiAgentSystemResponse(BaseModel):
    """Response model for multi-agent system operations"""
    id: str
    name: str
    description: str
    agents: List[str]
    triage_agent: str
    connections: List[AgentConnection]
    created_at: str 