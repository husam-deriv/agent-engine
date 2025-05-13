from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Union, Any
import os
import json
import uuid
import shutil
import datetime
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader, 
    Docx2txtLoader, 
    UnstructuredPowerPointLoader, 
    UnstructuredHTMLLoader
)

# Add parent directory to Python path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent, Runner
from tools.web_search_tool import search_web
from tools.csv_query_tool import csv_query
from tools.deep_search_tool import deep_research
from tools.mermaid_generator_tool import generate_mermaid_flowchart
from tools.interactive_ml_pipeline import run_interactive_pipeline
from tools.rag_tool import rag_collection_query

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create directories if they don't exist
os.makedirs("user_uploaded_files", exist_ok=True)
os.makedirs("agentTeamFiles", exist_ok=True)
os.makedirs("my_chroma_data_multisource", exist_ok=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Models for request/response validation
class FileDetails(BaseModel):
    name: str
    desc: str

class UserFiles(BaseModel):
    user_csv: Optional[FileDetails] = None
    user_doc: Optional[FileDetails] = None

class InitialRequest(BaseModel):
    description: str
    industry: str
    department: str
    files: UserFiles

class InitialResponse(BaseModel):
    questions: List[str]
    description: str
    files: UserFiles

class QuestionAnswer(BaseModel):
    question: str
    answer: str

class ToolInfo(BaseModel):
    name: str
    description: str

class PRDRequest(BaseModel):
    qa_pairs: List[QuestionAnswer]
    description: str
    files: UserFiles
    available_tools: List[ToolInfo]

class PRDResponse(BaseModel):
    team_name: str
    design_pattern: str
    agents: Dict[str, Any]

# Map tool names to their functions
TOOL_MAP = {
    "search_web": search_web,
    "query_csv_data": csv_query,
    "deep_research": deep_research,
    "create_mermaid_diagram": generate_mermaid_flowchart,
    "run_interactive_pipeline": run_interactive_pipeline,
    "rag_collection_query": rag_collection_query
}

# Additional models for inference and listing
class InferenceRequest(BaseModel):
    agent_team_name: str
    user_query: str

class InferenceResponse(BaseModel):
    result: str
    design_pattern: str
    team_name: str

class AgentTeamSummary(BaseModel):
    team_name: str
    design_pattern: str
    description: Optional[str] = None

class AgentTeamList(BaseModel):
    teams: List[AgentTeamSummary]

# Additional models for listing files
class UploadedFile(BaseModel):
    name: str
    type: str
    size: int
    uploadDate: str

class UploadedFileList(BaseModel):
    files: List[UploadedFile]

# Helper function to process document and create embeddings
def process_document_to_embeddings(file_path, collection_name):
    # Determine loader based on file extension
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == ".pdf":
        loader = PyPDFLoader(file_path)
    elif file_extension == ".docx":
        loader = Docx2txtLoader(file_path)
    elif file_extension == ".pptx":
        loader = UnstructuredPowerPointLoader(file_path)
    elif file_extension == ".html":
        loader = UnstructuredHTMLLoader(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {file_extension}")
    
    # Load and split documents
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    
    # Create embeddings
    embedder = OpenAIEmbeddings(model="text-embedding-3-large")
    
    # Initialize ChromaDB client
    chromadb_dir = os.path.join("backend/my_chroma_data_multisource")
    os.makedirs(chromadb_dir, exist_ok=True)
    client = chromadb.PersistentClient(path=chromadb_dir)
    
    # Create collection
    collection = client.create_collection(name=collection_name)
    
    # Add documents to collection
    for i, chunk in enumerate(chunks):
        # Get embeddings for the chunk
        embedding = embedder.embed_query(chunk.page_content)
        
        # Add to collection
        collection.add(
            documents=[chunk.page_content],
            embeddings=[embedding],
            metadatas=[{"source": file_path, "page": chunk.metadata.get("page", i)}],
            ids=[f"doc_{i}"]
        )
    
    return collection_name

@app.post("/createAgentTeamInitial", response_model=InitialResponse)
async def create_agent_team_initial(
    description: str = Form(...),
    industry: str = Form(...),
    department: str = Form(...),
    csv_file: Optional[UploadFile] = File(None),
    csv_desc: Optional[str] = Form(None),
    doc_file: Optional[UploadFile] = File(None),
    doc_desc: Optional[str] = Form(None)
):
    # Process files if provided
    files_info = UserFiles()
    
    if csv_file:
        # Save CSV file
        csv_file_path = os.path.join("user_uploaded_files", csv_file.filename)
        with open(csv_file_path, "wb") as f:
            shutil.copyfileobj(csv_file.file, f)
        
        files_info.user_csv = FileDetails(name=csv_file.filename, desc=csv_desc or "")
    
    if doc_file:
        # Save document file
        doc_file_path = os.path.join("user_uploaded_files", doc_file.filename)
        with open(doc_file_path, "wb") as f:
            shutil.copyfileobj(doc_file.file, f)
        
        # Create collection name from file name (without extension)
        collection_name = os.path.splitext(doc_file.filename)[0]
        
        # Process document and create embeddings if it's a supported file type
        file_ext = os.path.splitext(doc_file.filename)[1].lower()
        if file_ext in [".pdf", ".docx", ".pptx", ".html"]:
            try:
                process_document_to_embeddings(doc_file_path, collection_name)
            except Exception as e:
                print(f"Error processing document: {str(e)}")
        
        files_info.user_doc = FileDetails(name=doc_file.filename, desc=doc_desc or "")
    
    # Generate clarifying questions based on the initial description
    prompt = f"""
    You are an expert AI agent architect. The user has provided an initial description of an AI agent team project.
    
    Project Description: {description}
    Industry: {industry}
    Department: {department}
    
    Files provided:
    {f'CSV file: {files_info.user_csv.name} - {files_info.user_csv.desc}' if files_info.user_csv else 'No CSV file provided'}
    {f'Document file: {files_info.user_doc.name} - {files_info.user_doc.desc}' if files_info.user_doc else 'No document file provided'}
    
    Based on this information, generate 2-4 clarifying questions that would help you better understand the requirements 
    and design an effective AI agent team. The questions should be specific, actionable, and focused on gathering 
    important missing information.
    
    Return these questions as a numbered list, with no additional text.
    """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are an expert AI agent architect."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Process response to extract questions
        response_text = completion.choices[0].message.content
        questions = []
        
        # Clean up and extract questions
        for line in response_text.strip().split("\n"):
            # Remove leading numbers, dots, parentheses, etc.
            cleaned_line = line.strip()
            if cleaned_line:
                # Try to remove numbering patterns
                if cleaned_line[0].isdigit() and cleaned_line[1:3] in [". ", ") "]:
                    cleaned_line = cleaned_line[3:].strip()
                elif cleaned_line.startswith("- "):
                    cleaned_line = cleaned_line[2:].strip()
                
                questions.append(cleaned_line)
        
        # Ensure we have at least 2 questions
        if len(questions) < 2:
            questions = [
                "What specific tasks or workflows would you like the AI agent to handle?",
                "What metrics or outcomes would define success for this AI agent?",
                "Are there any specific integrations or systems this AI agent should work with?"
            ]
        
        # Limit to 4 questions
        questions = questions[:4]
        
        return InitialResponse(
            questions=questions,
            description=description,
            files=files_info
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")

@app.post("/createAgentTeamPRD", response_model=PRDResponse)
async def create_agent_team_prd(request: PRDRequest):
    # Extract the Q&A pairs into a formatted string
    qa_formatted = ""
    for i, qa in enumerate(request.qa_pairs):
        qa_formatted += f"Q{i+1}: {qa.question}\nA{i+1}: {qa.answer}\n\n"
    
    # Format the tools information
    tools_formatted = ""
    for tool in request.available_tools:
        tools_formatted += f"- {tool.name}: {tool.description}\n"
    
    # Step 1: Generate detailed and improved user description
    detailed_description_prompt = f"""
    You are an expert AI agent architect. The user has provided an initial project description, 
    along with answers to clarifying questions. Your task is to create a detailed and improved 
    version of the project description.
    
    Initial description: {request.description}
    
    Clarifying Questions and Answers:
    {qa_formatted}
    
    Files available:
    {f'CSV file: {request.files.user_csv.name} - {request.files.user_csv.desc}' if request.files.user_csv else 'No CSV file provided'}
    {f'Document file: {request.files.user_doc.name} - {request.files.user_doc.desc}' if request.files.user_doc else 'No document file provided'}
    
    Based on this information, create a detailed and improved project description that clearly 
    articulates the goals, requirements, and context of the AI agent team. This should be 
    comprehensive yet concise, focusing on what the AI agent team needs to accomplish.
    """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are an expert AI agent architect."},
                {"role": "user", "content": detailed_description_prompt}
            ]
        )
        
        improved_description = completion.choices[0].message.content
        
        # Step 2: Determine the most appropriate design pattern
        design_pattern_prompt = f"""
        You are an expert AI agent architect. Based on the detailed project description and available files,
        recommend the most appropriate agent design pattern from the following options:
        
        1. "single_agent" - A single agent that handles all user requests
        2. "sequential" - A workflow of sequentially called AI agents where output from one feeds into the next
        3. "multi_agent" - A team of specialist agents with a triage agent that routes requests
        
        Detailed Project Description:
        {improved_description}
        
        Files available:
        {f'CSV file: {request.files.user_csv.name} - {request.files.user_csv.desc}' if request.files.user_csv else 'No CSV file provided'}
        {f'Document file: {request.files.user_doc.name} - {request.files.user_doc.desc}' if request.files.user_doc else 'No document file provided'}
        
        Available tools:
        {tools_formatted}
        
        Respond with ONLY ONE of these exact strings: "single_agent", "sequential", or "multi_agent".
        """
        
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are an expert AI agent architect."},
                {"role": "user", "content": design_pattern_prompt}
            ]
        )
        
        design_pattern = completion.choices[0].message.content.strip()
        
        # Ensure the design pattern is one of the valid options
        if design_pattern not in ["single_agent", "sequential", "multi_agent"]:
            design_pattern = "single_agent"  # Default to single_agent if invalid
        
        # Step 3: Generate the agent team configuration based on the design pattern
        agent_team_prompt = f"""
        You are an expert AI agent architect. Create a detailed implementation of an AI agent team
        using the "{design_pattern}" design pattern.
        
        Detailed Project Description:
        {improved_description}
        
        Files available:
        {f'CSV file: {request.files.user_csv.name} - {request.files.user_csv.desc}' if request.files.user_csv else 'No CSV file provided'}
        {f'Document file: {request.files.user_doc.name} - {request.files.user_doc.desc}' if request.files.user_doc else 'No document file provided'}
        
        Available tools:
        {tools_formatted}
        
        Design Pattern: {design_pattern}
        """
        
        # Add design pattern specific instructions
        if design_pattern == "single_agent":
            agent_team_prompt += """
            Create a single agent based on the project description:
            
            Important Points:
            1. Tools are not necessary, they are optional.
            2. If using any tools, make sure to include in instruction how and when to invoke the tool.
            3. If using RAG or ML tool, make sure to specify the collection and csv file name which should be passed to the tool hardcoded in the instructions.
            
            Give ONLY JSON output in the following format:
            {
                "team_name": "",
                "design_pattern": "single_agent",
                "agents": {
                    "name": "",
                    "instructions": "Agent's personality and objective",
                    "tools": ["list of tools from existing ones"]
                }
            }
            """
        elif design_pattern == "sequential":
            agent_team_prompt += """
            Create a workflow out of sequentially called AI Agents based on the project description:
            
            Important Points:
            1. Tools are not necessary, they are optional.
            2. If using any tools, make sure to include in instruction how and when to invoke the tool.
            3. If using RAG or ML tool, make sure to specify the collection and csv file name which should be passed to the tool hardcoded in the instructions.
            
            Give ONLY JSON output in the following format:
            {
                "team_name": "",
                "design_pattern": "sequential",
                "agents": {
                    "1": {
                        "name": "",
                        "instructions": "Agent's personality and objective",
                        "tools": ["list of tools from existing ones"]
                    },
                    "2": {
                        "name": "",
                        "instructions": "Agent's personality and objective",
                        "tools": ["list of tools from existing ones"]
                    },
                    ...
                }
            }
            """
        else:  # multi_agent
            agent_team_prompt += """
            Create a multi-agent team based on the project description:
            
            Important points:
            1. Triage Agent acts as a router.
            2. Triage Agent cannot have tools.
            3. Total number of handoff agents can't be more than 3.
            4. If using RAG or ML tool, make sure to specify the collection and csv file name which should be passed to the tool hardcoded in the instructions.
            
            Give ONLY JSON output in the following format:
            {
                "team_name": "",
                "design_pattern": "multi_agent",
                "agents": {
                    "handoffs": [
                        {
                            "name": "",
                            "instructions": "Agent's personality and objective",
                            "handoff_description": "When to be handed off to",
                            "tools": ["list of tools from existing ones"]
                        },
                        ...
                    ],
                    "triage": {
                        "name": "",
                        "instructions": "Instructions about personality and handoffs",
                        "handoffs": ["list of handoff agents names"]
                    }
                }
            }
            """
        
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are an expert AI agent architect. Return only valid JSON with no explanation."},
                {"role": "user", "content": agent_team_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        agent_team_config = json.loads(completion.choices[0].message.content)
        
        # Ensure team_name is present
        if "team_name" not in agent_team_config:
            agent_team_config["team_name"] = f"team_{uuid.uuid4().hex[:8]}"
        
        # Save the agent team configuration to a file
        team_name = agent_team_config.get("team_name")
        filename = f"{team_name}.json"
        file_path = os.path.join("agentTeamFiles", filename)
        
        with open(file_path, "w") as f:
            json.dump(agent_team_config, f, indent=2)
        
        return agent_team_config
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating agent team: {str(e)}")

@app.post("/inferenceAgentTeam", response_model=InferenceResponse)
async def inference_agent_team(request: InferenceRequest):
    team_name = request.agent_team_name
    user_query = request.user_query
    
    # Load the agent team configuration
    file_path = os.path.join("agentTeamFiles", f"{team_name}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Agent team '{team_name}' not found")
    
    try:
        with open(file_path, "r") as f:
            config = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading agent team configuration: {str(e)}")
    
    design_pattern = config.get("design_pattern")
    if not design_pattern or design_pattern not in ["single_agent", "sequential", "multi_agent"]:
        raise HTTPException(status_code=400, detail=f"Invalid design pattern: {design_pattern}")
    
    try:
        # Run the agent team based on the design pattern
        if design_pattern == "single_agent":
            result = await run_single_agent(config, user_query)
        elif design_pattern == "sequential":
            result = await run_sequential_agents(config, user_query)
        else:  # multi_agent
            result = await run_multi_agent(config, user_query)
        
        return InferenceResponse(
            result=result,
            design_pattern=design_pattern,
            team_name=team_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running agent team: {str(e)}")

async def run_single_agent(config: Dict, user_query: str) -> str:
    """Run a single agent with the given configuration and user query."""
    agent_config = config.get("agents", {})
    
    # Extract agent properties
    name = agent_config.get("name", "Assistant")
    instructions = agent_config.get("instructions", "You are a helpful assistant.")
    tool_names = agent_config.get("tools", [])
    
    # Map tool names to actual tool functions
    tools = [TOOL_MAP[tool_name] for tool_name in tool_names if tool_name in TOOL_MAP]
    
    # Create the agent
    agent = Agent(
        name=name,
        instructions=instructions,
        tools=tools
    )
    
    # Run the agent
    result = await Runner.run(agent, user_query)
    return result.final_output

async def run_sequential_agents(config: Dict, user_query: str) -> str:
    """Run sequential agents where the output of one becomes input to the next."""
    agents_config = config.get("agents", {})
    
    # Sort agents by their numerical keys (1, 2, 3, etc.)
    agent_keys = sorted(agents_config.keys(), key=lambda x: int(x) if x.isdigit() else float('inf'))
    
    current_query = user_query
    final_output = ""
    
    # Process each agent in sequence
    for key in agent_keys:
        agent_config = agents_config[key]
        
        # Extract agent properties
        name = agent_config.get("name", f"Agent {key}")
        instructions = agent_config.get("instructions", "You are a helpful assistant.")
        tool_names = agent_config.get("tools", [])
        
        # Map tool names to actual tool functions
        tools = [TOOL_MAP[tool_name] for tool_name in tool_names if tool_name in TOOL_MAP]
        
        # Create the agent
        agent = Agent(
            name=name,
            instructions=instructions,
            tools=tools
        )
        
        # Run the agent with the current query
        result = await Runner.run(agent, current_query)
        
        # Update the query for the next agent and accumulate output
        current_query = result.final_output
        if int(key) == len(agent_keys):  # If this is the last agent
            final_output = current_query
        
    return final_output

async def run_multi_agent(config: Dict, user_query: str) -> str:
    """Run a multi-agent system with a triage agent and specialists."""
    agents_config = config.get("agents", {})
    
    # Process handoff agents first
    handoff_agents = []
    for handoff_config in agents_config.get("handoffs", []):
        # Extract agent properties
        name = handoff_config.get("name", "Specialist")
        handoff_description = handoff_config.get("handoff_description", "")
        instructions = handoff_config.get("instructions", "You are a helpful specialist.")
        tool_names = handoff_config.get("tools", [])
        
        # Map tool names to actual tool functions
        tools = [TOOL_MAP[tool_name] for tool_name in tool_names if tool_name in TOOL_MAP]
        
        # Create the handoff agent
        handoff_agent = Agent(
            name=name,
            handoff_description=handoff_description,
            instructions=instructions,
            tools=tools
        )
        
        handoff_agents.append(handoff_agent)
    
    # Get triage agent configuration
    triage_config = agents_config.get("triage", {})
    triage_name = triage_config.get("name", "Triage Agent")
    triage_instructions = triage_config.get("instructions", "You determine which specialist to use based on the user's query.")
    
    # Create the triage agent
    triage_agent = Agent(
        name=triage_name,
        instructions=triage_instructions,
        handoffs=handoff_agents
    )
    
    # Run the triage agent
    result = await Runner.run(triage_agent, user_query)
    return result.final_output

@app.get("/listAgentTeams", response_model=AgentTeamList)
async def list_agent_teams():
    """List all available agent teams from the agentTeamFiles directory."""
    teams = []
    
    try:
        # Ensure directory exists
        if not os.path.exists("agentTeamFiles"):
            return AgentTeamList(teams=[])
        
        # Get all JSON files in the directory
        for filename in os.listdir("agentTeamFiles"):
            if filename.endswith(".json"):
                file_path = os.path.join("agentTeamFiles", filename)
                
                try:
                    # Read and parse JSON
                    with open(file_path, "r") as f:
                        config = json.load(f)
                    
                    # Extract team information
                    team_name = config.get("team_name", os.path.splitext(filename)[0])
                    design_pattern = config.get("design_pattern", "unknown")
                    
                    # Generate a description based on the design pattern
                    description = None
                    if design_pattern == "single_agent":
                        agent = config.get("agents", {})
                        if isinstance(agent, dict) and "name" in agent:
                            description = f"Single agent: {agent.get('name')}"
                    elif design_pattern == "sequential":
                        agents = config.get("agents", {})
                        agent_count = len(agents) if isinstance(agents, dict) else 0
                        description = f"Sequential workflow with {agent_count} agents"
                    elif design_pattern == "multi_agent":
                        agents_config = config.get("agents", {})
                        handoffs = agents_config.get("handoffs", [])
                        handoff_count = len(handoffs) if isinstance(handoffs, list) else 0
                        description = f"Multi-agent system with {handoff_count} specialist agents"
                    
                    # Add team to list
                    teams.append(AgentTeamSummary(
                        team_name=team_name,
                        design_pattern=design_pattern,
                        description=description
                    ))
                    
                except Exception as e:
                    # Skip invalid files but log the error
                    print(f"Error parsing file {filename}: {str(e)}")
                    continue
        
        # Sort teams alphabetically by name
        teams.sort(key=lambda x: x.team_name)
        
        return AgentTeamList(teams=teams)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing agent teams: {str(e)}")

@app.get("/listUploadedFiles", response_model=UploadedFileList)
async def list_uploaded_files():
    """List all files in the user_uploaded_files directory."""
    files = []
    
    try:
        # Ensure directory exists
        if not os.path.exists("user_uploaded_files"):
            return UploadedFileList(files=[])
        
        # Get all files in the directory
        for filename in os.listdir("user_uploaded_files"):
            file_path = os.path.join("user_uploaded_files", filename)
            
            # Skip directories
            if not os.path.isfile(file_path):
                continue
            
            # Get file stats
            file_stats = os.stat(file_path)
            
            # Determine file type based on extension
            file_extension = os.path.splitext(filename)[1].lower()
            file_type = file_extension[1:] if file_extension else "unknown"
            
            # Add file to list
            files.append(
                UploadedFile(
                    name=filename,
                    type=file_type,
                    size=file_stats.st_size,
                    uploadDate=datetime.datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                )
            )
        
        # Sort files by upload date (newest first)
        files.sort(key=lambda x: x.uploadDate, reverse=True)
        
        return UploadedFileList(files=files)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
