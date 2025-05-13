"""
Project Analyzer for Gargash AI Builder
Analyzes project descriptions and recommends appropriate tools and configurations.
"""

import json
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI
from tool_registry import registry

class ProjectAnalyzer:
    """Analyzes project descriptions using LLM to recommend tools and configurations."""
    
    def __init__(self, openai_client: AsyncOpenAI):
        self.openai_client = openai_client
    
    async def analyze_project(self, 
                           title: str,
                           description: str,
                           company_name: str,
                           sector_name: str) -> Dict[str, Any]:
        """Analyze a project description and suggest appropriate tools and agent configuration."""
        system_prompt = """You are an AI project analyst for the Gargash AI Builder Platform.
Your task is to analyze a project description and determine the appropriate tools, agent type, and data requirements.

For each project, provide:
1. Problem type classification
2. Agent configuration (type, name, recommended tools, scheduling, slack channel)
3. Data requirements (list of data sources needed, their types, and whether they are company-specific)

Your analysis should be tailored to both the project needs and the company/sector context.

IMPORTANT:
- Only include data requirements if the project explicitly requires data integration or analysis
- For simple chat or interaction-only projects, return an empty list for data_requirements
- For data analysis projects or those requiring external sources, specify the needed data sources
- If a project primarily involves conversational AI with no data analysis, data_requirements should be empty"""

        user_prompt = f"""Project Title: {title}

Project Description:
{description}

Company: {company_name}
Sector: {sector_name}

Please analyze this project and provide a structured JSON response with:
1. Problem type (e.g., "Data Analysis", "Customer Service", "Marketing Automation")
2. Agent configuration
   - Type (e.g., "Single Agent", "Sequential Workflow", "Multi-Agent System")
   - Name (suggest a descriptive name)
   - Tools (list of recommended tools)
   - Is scheduled (boolean)
   - Schedule frequency (e.g., "Daily", "Weekly", "Monthly")
   - Slack channel (suggest an appropriate name, no spaces, use dashes)
3. Data requirements (ONLY if explicitly needed for the project)
   - List of data sources required
   - Type of each data source (e.g., "CSV", "Database", "API")
   - Whether each source is company-specific

For simple conversational agents or agents that don't require data analysis, use an empty list for data_requirements."""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5,
                max_tokens=1000
            )
            
            # Parse the JSON response
            analysis = json.loads(response.choices[0].message.content)
            
            # Check if this is a mental health, personal assistant, or conversation-only project
            needs_data = True
            description_lower = description.lower()
            conversation_indicators = [
                "mental health", "companion", "chat", "conversation", 
                "talking", "personal assistant", "virtual friend", "chatbot",
                "therapy", "counseling", "wellbeing", "well-being",
                "coaching", "mentor"
            ]
            
            # Check for indicators that suggest a conversation-only project
            if any(indicator in description_lower for indicator in conversation_indicators):
                # If we detect conversation indicators AND there's no mention of data analysis
                if not any(term in description_lower for term in ["data", "analyze", "dashboard", "report", "metrics"]):
                    # Override the data requirements to be empty
                    needs_data = False
                    analysis["data_requirements"] = []
            
            # Ensure the response has the expected structure
            return {
                "project": {
                    "title": title,
                    "description": description,
                    "company": company_name,
                    "sector": sector_name
                },
                "analysis": analysis.get("analysis", {
                    "problem_type": analysis.get("problem_type", "General AI Project")
                }),
                "agent_configuration": analysis.get("agent_configuration", {
                    "type": "Single Agent",
                    "name": "Default Assistant",
                    "tools": ["web_search", "rag_query"],
                    "is_scheduled": False,
                    "schedule_frequency": "None",
                    "slack_channel": "increase-marketing-throughput"
                }),
                "data_requirements": analysis.get("data_requirements", []),
                "needs_data_integration": needs_data and len(analysis.get("data_requirements", [])) > 0,
                "needs_slack_integration": analysis.get("agent_configuration", {}).get("is_scheduled", False)
            }
        except Exception as e:
            print(f"Error analyzing project: {str(e)}")
            # Return default values
            return {
                "project": {
                    "title": title,
                    "description": description,
                    "company": company_name,
                    "sector": sector_name
                },
                "analysis": {
                    "problem_type": "General AI Project"
                },
                "agent_configuration": {
                    "type": "Single Agent",
                    "name": "Default Assistant",
                    "tools": ["web_search", "rag_query"],
                    "is_scheduled": False,
                    "schedule_frequency": "None",
                    "slack_channel": "increase-marketing-throughput"
                },
                "data_requirements": [],
                "needs_data_integration": False,
                "needs_slack_integration": False
            }
    
    async def generate_agent_personality(self, analysis_result: Dict[str, Any]) -> str:
        """Generate agent personality based on project analysis."""
        system_prompt = """You are an AI personality designer for the Gargash AI Builder Platform.
Your task is to create a personality for an AI agent based on project analysis.

The personality should be professional, helpful, and tailored to the specific domain and company."""

        user_prompt = f"""Project details:
- Title: {analysis_result['project']['title']}
- Description: {analysis_result['project']['description']}
- Company: {analysis_result['project']['company']} (Sector: {analysis_result['project']['sector']})
- Problem Type: {analysis_result['analysis']['problem_type']}

Please generate a personality for an AI agent that will assist with this project."""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating agent personality: {str(e)}")
            # Return default personality
            return f"I am a professional AI assistant for {analysis_result['project']['company']} in the {analysis_result['project']['sector']} sector. I specialize in {analysis_result['analysis']['problem_type']} and I provide accurate, relevant information to help with your needs."
    
    async def generate_followup_questions(self, 
                                       title: str,
                                       description: str,
                                       company_name: str,
                                       sector_name: str) -> List[str]:
        """
        Generate follow-up questions based on project description to clarify requirements.
        
        Args:
            title: Project title
            description: Project description
            company_name: Company the project is for
            sector_name: Industry sector
            
        Returns:
            List of follow-up questions (maximum 3)
        """
        system_prompt = """You are an AI project requirements analyst for the Gargash AI Builder Platform.
Your task is to generate follow-up questions based on a project description to clarify requirements.

The questions should:
1. Be specific and focused on clarifying ambiguous aspects of the project
2. Help determine whether a single agent, sequential agents, or a multi-agent system would be most appropriate
3. Identify data sources, integration needs, and expected outputs
4. Be answerable with brief responses (not open-ended discussion questions)

Generate EXACTLY 3 questions. No more, no less."""

        user_prompt = f"""Project details:
- Title: {title}
- Description: {description}
- Company: {company_name} (Sector: {sector_name})

Please generate exactly 3 follow-up questions to help clarify the project requirements.
Format the response as a JSON array of strings, each containing one question."""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            result = json.loads(response.choices[0].message.content)
            
            # Extract questions
            questions = result.get("questions", [])
            
            # Ensure we have exactly 3 questions
            if len(questions) > 3:
                questions = questions[:3]
            
            while len(questions) < 3:
                questions.append(f"What are the primary success metrics for this {sector_name} project?")
            
            return questions
        except Exception as e:
            print(f"Error generating follow-up questions: {str(e)}")
            # Return default questions
            return [
                f"What specific outcomes or deliverables do you expect from this {sector_name} project?",
                f"Will this project require integration with existing systems at {company_name}?",
                f"What is the expected timeline and frequency of use for this AI solution?"
            ]
    
    async def recommend_agent_architecture(self,
                                        title: str,
                                        description: str,
                                        company_name: str,
                                        sector_name: str,
                                        question_answers: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Recommend agent architecture based on project description and question answers.
        
        Args:
            title: Project title
            description: Project description
            company_name: Company the project is for
            sector_name: Industry sector
            question_answers: List of dicts with 'question' and 'answer' keys
            
        Returns:
            Dict with recommended architecture, agents, tools, and flow
        """
        # First, check if this is a simple conversational project with no data or integration needs
        is_simple_conversation = self._is_simple_conversational_project(description, question_answers)
        
        if is_simple_conversation:
            return self._generate_single_agent_architecture(title, description, company_name, sector_name)
        
        # For more complex projects, use the LLM to recommend architecture
        system_prompt = """You are an AI architect for the Gargash AI Builder Platform.
Your task is to design the optimal agent architecture for a project based on its description and follow-up answers.

Consider three possible architectures and choose the MOST APPROPRIATE one based on actual project needs:

1. Single Agent: One specialized agent handling all tasks.
   - Appropriate for simple, focused, single-domain projects
   - Best for projects with minimal or no integrations
   - Ideal for conversational interfaces, assistants, companions, or simple advisors

2. Sequential Workflow: Multiple agents working in sequence, each handling a specific step.
   - Appropriate for projects with clear linear processes or data pipelines
   - Recommended when different expertise is needed at different stages
   - Good for data processing, analysis, and reporting projects
   - Example: DataCollector → Analyzer → ReportGenerator

3. Multi-Agent Team: Multiple specialized agents with a triage agent to coordinate.
   - Appropriate for complex, multi-domain projects requiring parallel work
   - Recommended when tasks are diverse and potentially concurrent
   - Example: TriageAgent coordinates DataAgent, AnalysisAgent, and CustomerAgent

IMPORTANT GUIDANCE:
- DO NOT default to more complex architectures when in doubt - match the architecture to actual needs
- Pay special attention to the answers about integrations, data needs, and project complexity
- Choose Single Agent when there are no data sources, integrations, or complex workflows mentioned
- Only recommend complex architectures when explicitly justified by project requirements

For each agent, specify:
- Name (descriptive of function)
- Role/specialization (detailed)
- Personality (brief, relevant to role)
- Required tools (specific to function, can be empty for conversational agents)
- Knowledge sources (detailed)

Your output will be used directly to configure AI agents, so be detailed and precise."""

        # Format Q&A for prompt
        qa_formatted = "\n".join([f"Q: {qa['question']}\nA: {qa['answer']}" for qa in question_answers])
        
        user_prompt = f"""Project details:
- Title: {title}
- Description: {description}
- Company: {company_name} (Sector: {sector_name})

Follow-up Q&A:
{qa_formatted}

Based on the project details and follow-up answers, recommend the most appropriate agent architecture.
Include detailed agent specifications, tools, and workflow in JSON format.

IMPORTANT: Choose the simplest architecture that can meet the project requirements. Do not add unnecessary complexity.
If the project is primarily conversation-based with no integrations or data requirements, a Single Agent with minimal tools is likely sufficient."""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,  # Reduced temperature for more deterministic outputs
                max_tokens=2500,
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            result = json.loads(response.choices[0].message.content)
            
            # Add project info to the result
            result["project"] = {
                "title": title,
                "description": description,
                "company": company_name,
                "sector": sector_name
            }
            
            # Double check the architecture recommendation against project requirements
            # If integration/data needs are explicitly denied in answers but complex architecture is recommended,
            # override to simpler architecture
            if self._should_downgrade_architecture(result, question_answers):
                return self._downgrade_architecture(result, title, description, company_name, sector_name)
            
            return result
        except Exception as e:
            print(f"Error recommending agent architecture: {str(e)}")
            # Check if we can use a simple agent first
            if self._is_simple_conversational_project(description, question_answers):
                return self._generate_single_agent_architecture(title, description, company_name, sector_name)
            # Fall back to sequential workflow only for complex projects
            return await self._generate_sequential_workflow(title, description, company_name, sector_name, question_answers)
    
    def _is_simple_conversational_project(self, description: str, question_answers: List[Dict[str, str]]) -> bool:
        """Determine if this is a simple conversational project with no data or integration needs."""
        description_lower = description.lower()
        
        # Check for conversation indicators
        conversation_indicators = [
            "chat", "conversation", "assistant", "companion", "mental health", 
            "therapy", "counseling", "wellbeing", "well-being", "meditation",
            "mindfulness", "talking", "personal assistant", "virtual friend", "chatbot",
            "coaching", "mentor"
        ]
        
        # Check for data/integration indicators
        data_integration_indicators = [
            "data", "database", "integration", "api", "analyze", "dashboard", 
            "report", "metrics", "csv", "excel", "visualization", "statistics",
            "processing", "pipeline", "collect"
        ]
        
        has_conversation_indicators = any(indicator in description_lower for indicator in conversation_indicators)
        has_data_integration = any(indicator in description_lower for indicator in data_integration_indicators)
        
        # Check question answers for integration or data needs
        integration_denial = False
        data_denial = False
        
        for qa in question_answers:
            answer_lower = qa["answer"].lower()
            question_lower = qa["question"].lower()
            
            # Check for explicit denial of integration needs
            if "integration" in question_lower or "existing systems" in question_lower:
                integration_denial = ("no" in answer_lower or "not" in answer_lower or "won't" in answer_lower or 
                                     "doesn't" in answer_lower or "does not" in answer_lower)
            
            # Check for denial of data collection/analysis needs
            if "data" in question_lower or "deliverables" in question_lower or "outcome" in question_lower:
                data_denial = ("no data" in answer_lower or "without data" in answer_lower or 
                              "purely conversation" in answer_lower or "just conversation" in answer_lower or
                              "only conversation" in answer_lower)
        
        # It's a simple conversational project if:
        # 1. It has conversation indicators
        # 2. It either lacks data/integration indicators OR explicitly denies needing them in answers
        return has_conversation_indicators and (not has_data_integration or integration_denial or data_denial)
    
    def _generate_single_agent_architecture(self, title: str, description: str, company_name: str, sector_name: str) -> Dict[str, Any]:
        """Generate a simple single agent architecture for conversational projects."""
        # Extract purpose from title or description
        description_lower = description.lower()
        purpose = ""
        
        if "meditation" in description_lower or "mindfulness" in description_lower:
            purpose = "Meditation & Mindfulness"
        elif "therapy" in description_lower or "counseling" in description_lower:
            purpose = "Therapeutic Support"
        elif "coach" in description_lower or "mentor" in description_lower:
            purpose = "Personal Coaching"
        elif "assistant" in description_lower:
            purpose = "Personal Assistant"
        else:
            purpose = "Conversational Support"
        
        # Create a simple agent
        agent_name = f"{purpose.replace(' & ', '').replace(' ', '')}Agent"
        
        return {
            "architecture_type": "single_agent",
            "description": f"A simple conversational agent focused on {purpose.lower()} through natural dialogue.",
            "agents": [{
                "name": agent_name,
                "role": f"{purpose} Specialist",
                "personality": f"Empathetic and supportive conversation partner focused on providing {purpose.lower()} guidance for {company_name} in the {sector_name} sector.",
                "tools": [],  # No tools for a pure conversational agent
                "knowledge_sources": [f"{purpose} techniques", "Conversation design", "Empathetic response patterns"]
            }],
            "workflow": f"{agent_name} engages in direct conversation with users",
            "project": {
                "title": title,
                "description": description,
                "company": company_name,
                "sector": sector_name
            }
        }
    
    def _should_downgrade_architecture(self, result: Dict[str, Any], question_answers: List[Dict[str, str]]) -> bool:
        """Check if the architecture should be downgraded based on answers."""
        if result.get("architecture_type") == "single_agent":
            return False  # Already the simplest architecture
            
        # Check if answers explicitly deny needing complex architecture
        integration_denial = False
        data_denial = False
        simple_need = False
        
        for qa in question_answers:
            answer_lower = qa["answer"].lower()
            question_lower = qa["question"].lower()
            
            # Check for explicit denial of integration needs
            if "integration" in question_lower or "existing systems" in question_lower:
                integration_denial = ("no" in answer_lower or "not" in answer_lower or "won't" in answer_lower or 
                                     "doesn't" in answer_lower or "does not" in answer_lower)
            
            # Check for denial of data collection/analysis needs
            if "data" in question_lower or "deliverables" in question_lower or "outcome" in question_lower:
                data_denial = ("no data" in answer_lower or "without data" in answer_lower or 
                              "purely conversation" in answer_lower or "just conversation" in answer_lower or
                              "only conversation" in answer_lower)
                
            # Check for simple needs
            if "expect" in question_lower or "deliverable" in question_lower or "outcome" in question_lower:
                simple_need = ("simple" in answer_lower or "basic" in answer_lower or "just" in answer_lower or
                              "only" in answer_lower or "merely" in answer_lower)
        
        # Downgrade if there are explicit denials contradicting a complex architecture
        return (integration_denial and data_denial) or (simple_need and (integration_denial or data_denial))
    
    def _downgrade_architecture(self, result: Dict[str, Any], title: str, description: str, company_name: str, sector_name: str) -> Dict[str, Any]:
        """Downgrade a complex architecture to a simpler one."""
        # If it's sequential or multi-agent, downgrade to single agent
        if result.get("architecture_type") in ["sequential", "multi_agent"]:
            return self._generate_single_agent_architecture(title, description, company_name, sector_name)
        
        return result
    
    async def _generate_sequential_workflow(self, 
                                         title: str, 
                                         description: str, 
                                         company_name: str, 
                                         sector_name: str,
                                         question_answers: List[Dict[str, str]]) -> Dict[str, Any]:
        """Fallback method to generate a sequential workflow architecture."""
        # Identify potential roles based on project description
        roles = []
        
        # Common data-related keywords
        data_sources = ["database", "csv", "excel", "api", "crm", "salesforce", "sap", "data warehouse"]
        analysis_terms = ["analyze", "analysis", "insights", "trends", "patterns", "visualization"]
        reporting_terms = ["report", "dashboard", "email", "presentation", "summary", "communicate"]
        
        # Check for data collection needs
        if any(source in description.lower() for source in data_sources):
            roles.append("data_collection")
            
        # Check for analysis needs
        if any(term in description.lower() for term in analysis_terms):
            roles.append("analysis")
            
        # Check for reporting needs
        if any(term in description.lower() for term in reporting_terms):
            roles.append("reporting")
            
        # Ensure we have at least 3 roles
        if "data_collection" not in roles:
            roles.insert(0, "data_collection")
        if "analysis" not in roles:
            roles.insert(min(1, len(roles)), "analysis")
        if "reporting" not in roles:
            roles.append("reporting")
            
        # Generate agents based on roles
        agents = []
        
        if "data_collection" in roles:
            agents.append({
                "name": "DataCollectorAgent",
                "role": "Data Extraction & Integration Specialist",
                "personality": f"Methodical and detail-oriented specialist focused on collecting and preparing data for {sector_name} analytics.",
                "tools": ["csv_agent", "database_connector", "web_search"],
                "knowledge_sources": ["Integration APIs", f"{company_name} data sources", "Data schemas"]
            })
            
        if "analysis" in roles:
            agents.append({
                "name": "AnalyticsAgent",
                "role": f"{sector_name} Analytics Specialist",
                "personality": f"Analytical and insight-driven expert in {sector_name} data patterns and market trends.",
                "tools": ["data_analysis", "visualization", "ml_prediction"],
                "knowledge_sources": [f"{sector_name} benchmarks", "Statistical methods", "Market indicators"]
            })
            
        if "reporting" in roles:
            agents.append({
                "name": "ReportingAgent",
                "role": "Business Reporting & Communication Specialist",
                "personality": f"Clear communicator focused on transforming complex {sector_name} insights into actionable business recommendations.",
                "tools": ["summarization", "document_creator", "email_formatter"],
                "knowledge_sources": [f"{company_name} brand guidelines", "Report templates", "Communication best practices"]
            })
        
        # Construct workflow description
        workflow_steps = []
        for i, agent in enumerate(agents):
            if i == 0:
                workflow_steps.append(f"{agent['name']} collects and prepares data")
            elif i == len(agents) - 1:
                workflow_steps.append(f"{agent['name']} produces final outputs")
            else:
                workflow_steps.append(f"{agent['name']} processes outputs from previous step")
                
        workflow = " → ".join(workflow_steps)
        
        return {
            "architecture_type": "sequential",
            "description": f"A sequential workflow with {len(agents)} specialized agents, each handling a specific step in the process.",
            "agents": agents,
            "workflow": workflow,
            "project": {
                "title": title,
                "description": description,
                "company": company_name,
                "sector": sector_name
            }
        } 