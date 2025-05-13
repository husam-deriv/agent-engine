"""
Agent Generator for Gargash AI Builder
Creates specialized agents based on project requirements using LLM.
"""

import json
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI
import agent_utils
from database import AgentModel, engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import re
import time

class AgentGenerator:
    """Generates specialized agents based on project requirements."""
    
    def __init__(self, openai_client: AsyncOpenAI):
        self.openai_client = openai_client
    
    async def generate_agent(self, 
                           project_title: str,
                           project_description: str,
                           company_name: str,
                           sector_name: str,
                           problem_type: str,
                           suggested_tools: List[str],
                           db_session: AsyncSession) -> Dict[str, Any]:
        """
        Generate a specialized agent for a project using LLM.
        
        Args:
            project_title: Title of the project
            project_description: Description of the project
            company_name: Company the project is for
            sector_name: Industry sector
            problem_type: Type of problem being solved
            suggested_tools: List of suggested tool names
            db_session: Database session
            
        Returns:
            Dict with agent details including id, name, role, and personality
        """
        try:
            # Generate agent name and details
            agent_spec = await self._generate_agent_spec(
                project_title, 
                project_description,
                company_name,
                sector_name,
                problem_type,
                suggested_tools
            )
            
            # Create the agent in the database
            new_agent = await self._create_agent_in_db(agent_spec, suggested_tools, db_session)
            
            # Create in-memory agent instance
            try:
                await agent_utils.get_or_create_agent(
                    session=db_session,
                    name=new_agent.name,
                    role=new_agent.role,
                    personality=new_agent.personality,
                    tools=suggested_tools,
                    openai_client=self.openai_client
                )
            except Exception as e:
                print(f"Warning: Failed to create in-memory agent instance: {str(e)}")
                # Continue anyway since the DB record was created successfully
            
            return {
                "id": new_agent.id,
                "name": new_agent.name,
                "role": new_agent.role,
                "personality": new_agent.personality,
                "tools": suggested_tools
            }
        except Exception as e:
            print(f"Error generating agent: {str(e)}")
            raise
    
    async def _generate_agent_spec(self,
                                project_title: str,
                                project_description: str,
                                company_name: str,
                                sector_name: str,
                                problem_type: str,
                                suggested_tools: List[str]) -> Dict[str, str]:
        """Generate agent name, role, and personality using LLM."""
        system_prompt = """You are an AI agent designer for the Gargash Group's AI Builder Platform.
Your task is to create a specialized AI agent for a specific project.

The agent should be highly specialized for the specific task, not a general-purpose assistant.
Use the project details, company, and sector information to create:
1. A short, memorable name for the agent (should be relevant and professional)
2. A concise role description (what the agent specializes in)
3. A detailed personality and instruction set (how the agent should behave, respond, and approach tasks)

Your output will be directly used to create a new agent in the system."""

        user_prompt = f"""Project details:
- Title: {project_title}
- Description: {project_description}
- Company: {company_name} (Sector: {sector_name})
- Problem type: {problem_type}
- Tools available: {', '.join(suggested_tools)}

Please generate a specialized agent for this project with:
1. A name (short, memorable, no spaces)
2. A role description (one sentence)
3. A detailed personality and instruction set (2-3 paragraphs)"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            result = json.loads(response.choices[0].message.content)
            
            # Ensure we have all required fields
            if not all(k in result for k in ["name", "role", "personality"]):
                raise ValueError("Missing required fields in agent specification")
            
            # Sanitize the agent name to ensure no invalid characters
            sanitized_name = re.sub(r'[^a-zA-Z0-9]', '', result["name"])
            if not sanitized_name:
                sanitized_name = f"{problem_type.replace(' ', '')}Agent"
            
            # Always add "Agent" suffix if not present
            if not sanitized_name.endswith("Agent"):
                sanitized_name += "Agent"
            
            # Make the name unique by adding a timestamp
            timestamp = int(time.time())
            sanitized_name = f"{sanitized_name}_{timestamp}"
            
            # Update the name in the result
            result["name"] = sanitized_name
            
            return result
        except Exception as e:
            print(f"Error generating agent specification: {str(e)}")
            # Return default values with timestamp to ensure uniqueness
            timestamp = int(time.time())
            name = f"{problem_type.replace(' ', '')}Agent_{timestamp}"
            return {
                "name": name,
                "role": f"Specialized {problem_type} assistant for {company_name}",
                "personality": f"I am a specialized AI assistant for {company_name} in the {sector_name} sector. I focus on {problem_type} tasks and provide professional, accurate assistance for {project_title}. I use data-driven approaches and best practices relevant to {sector_name} companies."
            }
    
    async def _create_agent_in_db(self,
                                agent_spec: Dict[str, str],
                                tools: List[str],
                                db_session: AsyncSession) -> AgentModel:
        """Create the agent in the database."""
        # Check if agent with this name already exists
        result = await db_session.execute(
            select(AgentModel).where(AgentModel.name == agent_spec["name"])
        )
        existing_agent = result.scalars().first()
        
        if existing_agent:
            # Agent already exists, just update its properties
            existing_agent.role = agent_spec["role"]
            existing_agent.personality = agent_spec["personality"]
            existing_agent.tools = tools
            await db_session.commit()
            await db_session.refresh(existing_agent)
            return existing_agent
        
        # Create new agent model if it doesn't exist
        new_agent = AgentModel(
            name=agent_spec["name"],
            role=agent_spec["role"],
            personality=agent_spec["personality"],
            tools=tools
        )
        
        db_session.add(new_agent)
        await db_session.commit()
        await db_session.refresh(new_agent)
        
        return new_agent
    
    async def generate_custom_tool(self,
                                 tool_name: str,
                                 tool_description: str,
                                 project_context: str,
                                 db_session: AsyncSession) -> Dict[str, Any]:
        """
        Generate a custom tool for an agent based on project requirements.
        
        Args:
            tool_name: Suggested name for the tool
            tool_description: Description of what the tool should do
            project_context: Context about the project to help generate the tool
            db_session: Database session
            
        Returns:
            Dict with tool details
        """
        system_prompt = """You are a tool designer for AI agents in the Gargash AI Builder Platform.
Your task is to design a specialized tool that an AI agent can use to perform specific tasks.

The tool should be highly specialized and perform a specific function.
You need to define:
1. A clear name for the tool (snake_case format)
2. A concise description of what the tool does
3. The parameters required by the tool (name, type, description, whether required)
4. Whether the tool requires access to company or sector data
"""

        user_prompt = f"""Tool requirements:
- Suggested name: {tool_name}
- Description: {tool_description}
- Project context: {project_context}

Please design a specialized tool with:
1. A name (in snake_case format)
2. A description (1-2 sentences explaining what it does)
3. Parameters (list of parameters with name, type, description, required status)
4. Data access requirements (whether it needs company or sector data)"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            result = json.loads(response.choices[0].message.content)
            
            # Register the tool in the registry
            from tool_registry import registry, TOOL_CATEGORIES
            
            # Determine tool category
            category = "DATA_ANALYSIS"  # Default category
            for cat in TOOL_CATEGORIES:
                if cat.lower() in tool_description.lower():
                    category = cat
                    break
            
            # Create parameters list
            parameters = []
            if "parameters" in result:
                parameters = result["parameters"]
            
            # Register the tool
            requires_data = result.get("requires_data_access", False)
            registry.register_tool(
                name=result["name"],
                category=category,
                description=result["description"],
                requires_data_access=requires_data,
                parameters=parameters
            )
            
            return {
                "name": result["name"],
                "description": result["description"],
                "category": category,
                "requires_data_access": requires_data,
                "parameters": parameters
            }
        except Exception as e:
            print(f"Error generating custom tool: {str(e)}")
            # Return default values
            tool_name_clean = tool_name.lower().replace(" ", "_")
            return {
                "name": tool_name_clean,
                "description": tool_description,
                "category": "DATA_ANALYSIS",
                "requires_data_access": True,
                "parameters": [
                    {
                        "name": "query",
                        "type": "string",
                        "description": "Query to process",
                        "required": True
                    }
                ]
            } 