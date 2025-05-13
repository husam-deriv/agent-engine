"""
Tool Registry for Gargash AI Builder
Manages registration and access to specialized tools for AI agents.
"""

from typing import Dict, List, Any, Optional, Callable, Union
import json
import os

# Tool categories matching the requested premade tools
TOOL_CATEGORIES = [
    "ML",
    "CSV_AGENT", 
    "DATA_ANALYSIS",
    "VISUALIZATION",
    "RAG",
    "WEB_SEARCH",
    "SUMMARIZATION"
]

class ToolRegistry:
    """Registry for managing AI tools."""
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
    
    def register_tool(self, 
                     name: str, 
                     category: str, 
                     description: str,
                     handler: Optional[Callable] = None,
                     requires_data_access: bool = False,
                     parameters: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Register a new tool with the registry.
        
        Args:
            name: Unique name for the tool
            category: Category from TOOL_CATEGORIES
            description: Description of what the tool does
            handler: Function to handle tool execution
            requires_data_access: Whether this tool needs access to company/sector data
            parameters: List of parameter definitions for the tool
        """
        if name in self.tools:
            raise ValueError(f"Tool '{name}' already exists in registry")
        
        if category not in TOOL_CATEGORIES:
            raise ValueError(f"Category '{category}' is not valid. Choose from {TOOL_CATEGORIES}")
        
        self.tools[name] = {
            "name": name,
            "category": category,
            "description": description,
            "handler": handler,
            "requires_data_access": requires_data_access,
            "parameters": parameters or []
        }
        
        print(f"Registered tool: {name} ({category})")
    
    def get_tools_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all tools in a specific category."""
        return [
            {k: v for k, v in tool.items() if k != 'handler'} 
            for tool in self.tools.values() 
            if tool["category"] == category
        ]
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all registered tools (without handler functions)."""
        return [
            {k: v for k, v in tool.items() if k != 'handler'} 
            for tool in self.tools.values()
        ]
    
    def get_tool_description(self, name: str) -> Dict[str, Any]:
        """Get a specific tool's description."""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found in registry")
        
        tool = self.tools[name]
        return {k: v for k, v in tool.items() if k != 'handler'}
    
    def execute_tool(self, 
                    name: str, 
                    parameters: Dict[str, Any],
                    company_id: Optional[int] = None,
                    sector_id: Optional[int] = None) -> Any:
        """Execute a tool with the given parameters."""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found in registry")
        
        tool = self.tools[name]
        handler = tool.get("handler")
        
        if not handler:
            raise ValueError(f"Tool '{name}' does not have a handler function")
        
        # Check if the tool requires data access and ensure company/sector is provided
        if tool["requires_data_access"] and not (company_id or sector_id):
            raise ValueError(f"Tool '{name}' requires company or sector ID")
        
        # Add company/sector ID to parameters if tool requires data access
        if tool["requires_data_access"]:
            parameters["company_id"] = company_id
            parameters["sector_id"] = sector_id
            
        # Execute the handler
        return handler(**parameters)
    
    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Get tool descriptions in a format suitable for LLM function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": {
                        "type": "object",
                        "properties": {
                            param["name"]: {
                                "type": param["type"],
                                "description": param["description"]
                            } 
                            for param in tool["parameters"]
                        },
                        "required": [
                            param["name"] for param in tool["parameters"] 
                            if param.get("required", False)
                        ]
                    }
                }
            }
            for tool in self.tools.values()
        ]

# Create the global registry instance
registry = ToolRegistry()

# Register the basic tools
def register_basic_tools():
    """Register the basic set of tools."""
    # CSV Agent
    registry.register_tool(
        name="csv_search",
        category="CSV_AGENT",
        description="Search and query data from CSV files",
        requires_data_access=True,
        parameters=[
            {
                "name": "query",
                "type": "string",
                "description": "Natural language query about the CSV data",
                "required": True
            },
            {
                "name": "file_name",
                "type": "string",
                "description": "Name of the CSV file to query",
                "required": True
            }
        ]
    )
    
    # Data Analysis
    registry.register_tool(
        name="data_analysis",
        category="DATA_ANALYSIS",
        description="Perform Python-based analysis on data",
        requires_data_access=True,
        parameters=[
            {
                "name": "code",
                "type": "string",
                "description": "Python code to execute for data analysis",
                "required": True
            },
            {
                "name": "data_file",
                "type": "string",
                "description": "Path to the data file to analyze",
                "required": True
            }
        ]
    )
    
    # Visualization
    registry.register_tool(
        name="create_visualization",
        category="VISUALIZATION",
        description="Create visual diagrams using MermaidJS syntax",
        parameters=[
            {
                "name": "diagram_type",
                "type": "string",
                "description": "Type of diagram (flowchart, sequence, etc.)",
                "required": True
            },
            {
                "name": "content",
                "type": "string",
                "description": "MermaidJS syntax for the diagram",
                "required": True
            }
        ]
    )
    
    # RAG Tool
    registry.register_tool(
        name="rag_query",
        category="RAG",
        description="Query company/sector knowledge base using RAG",
        requires_data_access=True,
        parameters=[
            {
                "name": "query",
                "type": "string",
                "description": "Natural language query for the knowledge base",
                "required": True
            },
            {
                "name": "corpus_name",
                "type": "string",
                "description": "Name of the knowledge corpus to query",
                "required": True
            }
        ]
    )
    
    # Web Search
    registry.register_tool(
        name="web_search",
        category="WEB_SEARCH",
        description="Search the web for information",
        parameters=[
            {
                "name": "query",
                "type": "string",
                "description": "Search query",
                "required": True
            },
            {
                "name": "num_results",
                "type": "integer",
                "description": "Number of results to return",
                "required": False
            }
        ]
    )
    
    # Summarization
    registry.register_tool(
        name="summarize_text",
        category="SUMMARIZATION",
        description="Summarize large text using Gemini 1.5",
        parameters=[
            {
                "name": "text",
                "type": "string",
                "description": "Text to summarize",
                "required": True
            },
            {
                "name": "max_length",
                "type": "integer",
                "description": "Maximum length of summary",
                "required": False
            }
        ]
    )
    
    # ML Tool
    registry.register_tool(
        name="ml_prediction",
        category="ML",
        description="Run machine learning prediction on data",
        requires_data_access=True,
        parameters=[
            {
                "name": "model_type",
                "type": "string",
                "description": "Type of ML model to use",
                "required": True
            },
            {
                "name": "data_file",
                "type": "string",
                "description": "Path to the data file",
                "required": True
            },
            {
                "name": "target_column",
                "type": "string",
                "description": "Target column for prediction",
                "required": True
            }
        ]
    )

# Initialize the registry with basic tools
register_basic_tools() 