from typing import Dict, List, Any, Optional, Callable
import json
import datetime
import requests
from pydantic import BaseModel, Field
import html

# Tool function type definition
ToolFunction = Callable[[Dict[str, Any]], str]

# Base class for tool parameters
class ToolParameters(BaseModel):
    pass

# Weather tool parameters
class WeatherParameters(ToolParameters):
    location: str = Field(..., description="The city and state, e.g. San Francisco, CA")
    unit: Optional[str] = Field("celsius", description="The temperature unit, either 'celsius' or 'fahrenheit'")

# Calculator tool parameters
class CalculatorParameters(ToolParameters):
    expression: str = Field(..., description="The mathematical expression to evaluate")

# Web search tool parameters
class WebSearchParameters(ToolParameters):
    query: str = Field(..., description="The search query")
    num_results: Optional[int] = Field(5, description="Number of results to return (max 10)")

# Calendar tool parameters
class CalendarParameters(ToolParameters):
    date: Optional[str] = Field(None, description="The date to check in YYYY-MM-DD format. Defaults to today.")

# Knowledge base tool parameters
class KnowledgeBaseParameters(ToolParameters):
    query: str = Field(..., description="The query to search in the knowledge base")

# Tool implementations

def weather_tool(params: Dict[str, Any]) -> str:
    """Get the current weather for a location."""
    try:
        location = params.get("location", "")
        unit = params.get("unit", "celsius")
        
        # In a real implementation, this would call a weather API
        # For now, we'll return a mock response
        temp = 22 if unit == "celsius" else 72
        return f"The current weather in {location} is {temp}°{unit[0].upper()}. It's partly cloudy with a 10% chance of rain."
    except Exception as e:
        return f"Error getting weather information: {str(e)}"

def calculator_tool(params: Dict[str, Any]) -> str:
    """Evaluate a mathematical expression."""
    try:
        expression = params.get("expression", "")
        # Use eval with caution - in a production environment, you'd want to use a safer alternative
        # or implement a proper parser
        result = eval(expression, {"__builtins__": {}}, {"abs": abs, "round": round, "max": max, "min": min})
        return f"The result of {expression} is {result}"
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"

def web_search_tool(params: Dict[str, Any]) -> str:
    """Perform a web search using DuckDuckGo."""
    try:
        query = params.get("query", "")
        num_results = min(params.get("num_results", 5), 10)  # Limit to max 10 results
        
        # Call DuckDuckGo search API
        url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_html': 1,
            'skip_disambig': 1
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        # Process DuckDuckGo API response
        results = []
        
        # Add abstract text if available
        if data.get('Abstract'):
            results.append(f"Summary: {data['Abstract']}")
        
        # Add related topics/results
        if data.get('RelatedTopics'):
            count = 0
            for topic in data['RelatedTopics']:
                if count >= num_results:
                    break
                    
                if 'Text' in topic:
                    # Clean and add the result
                    text = html.unescape(topic['Text'])
                    if topic.get('FirstURL'):
                        results.append(f"{count+1}. {text} [Source: {topic['FirstURL']}]")
                    else:
                        results.append(f"{count+1}. {text}")
                    count += 1
        
        # If no results found in related topics, try the Infobox
        if not results and data.get('Infobox') and data['Infobox'].get('content'):
            for item in data['Infobox']['content']:
                if 'data_type' in item and item['data_type'] == 'text' and 'value' in item:
                    results.append(f"Info: {item['label']}: {item['value']}")
        
        # If still no results, return a message
        if not results:
            # Try to get results from a simple web search using requests
            search_url = f"https://html.duckduckgo.com/html/?q={query}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            try:
                search_response = requests.get(search_url, headers=headers)
                
                # Very simple HTML parsing to extract results
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(search_response.text, 'html.parser')
                
                results_elements = soup.select('.result__title')
                snippets_elements = soup.select('.result__snippet')
                links_elements = soup.select('.result__url')
                
                for i in range(min(len(results_elements), num_results)):
                    title = results_elements[i].text.strip()
                    snippet = ""
                    if i < len(snippets_elements):
                        snippet = snippets_elements[i].text.strip()
                    
                    link = ""
                    if i < len(links_elements):
                        link = links_elements[i].text.strip()
                    
                    results.append(f"{i+1}. {title}\n   {snippet}\n   [Source: {link}]")
            except Exception as e:
                # If backup search fails, return a message
                results.append(f"No direct results found for '{query}'. Try refining your search query.")
        
        return f"Search results for '{query}':\n\n" + "\n\n".join(results)
    except Exception as e:
        return f"Error performing web search: {str(e)}"

def calendar_tool(params: Dict[str, Any]) -> str:
    """Get calendar information for a specific date."""
    try:
        date_str = params.get("date")
        if date_str:
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            date = datetime.date.today()
        
        # In a real implementation, this would access a calendar API
        # For now, we'll return a mock response
        day_of_week = date.strftime("%A")
        return f"Date: {date.strftime('%Y-%m-%d')} is a {day_of_week}. You have no scheduled events for this day."
    except Exception as e:
        return f"Error accessing calendar: {str(e)}"

def knowledge_base_tool(params: Dict[str, Any]) -> str:
    """Search a knowledge base for information."""
    try:
        query = params.get("query", "")
        # In a real implementation, this would search a knowledge base
        # For now, we'll return a mock response
        return f"Knowledge base results for '{query}':\n- The information you requested is available in our documentation.\n- Please refer to section 3.2 for more details."
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"

# Dictionary of available tools
AVAILABLE_TOOLS: Dict[str, Dict[str, Any]] = {
    "weather": {
        "name": "weather",
        "description": "Get the current weather for a location",
        "parameters_class": WeatherParameters,
        "function": weather_tool
    },
    "calculator": {
        "name": "calculator",
        "description": "Evaluate a mathematical expression",
        "parameters_class": CalculatorParameters,
        "function": calculator_tool
    },
    "web_search": {
        "name": "web_search",
        "description": "Perform a web search",
        "parameters_class": WebSearchParameters,
        "function": web_search_tool
    },
    "calendar": {
        "name": "calendar",
        "description": "Get calendar information for a specific date",
        "parameters_class": CalendarParameters,
        "function": calendar_tool
    },
    "knowledge_base": {
        "name": "knowledge_base",
        "description": "Search a knowledge base for information",
        "parameters_class": KnowledgeBaseParameters,
        "function": knowledge_base_tool
    }
}

# Function to get all available tools
def get_available_tools() -> Dict[str, Dict[str, Any]]:
    return AVAILABLE_TOOLS

# Function to get tool descriptions for display in the UI
def get_tool_descriptions() -> List[Dict[str, str]]:
    return [
        {
            "name": tool_info["name"],
            "description": tool_info["description"]
        }
        for tool_info in AVAILABLE_TOOLS.values()
    ]

# Function to execute a tool
def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> str:
    if tool_name not in AVAILABLE_TOOLS:
        return f"Error: Tool '{tool_name}' not found"
    
    tool = AVAILABLE_TOOLS[tool_name]
    try:
        # Validate parameters using the tool's parameter class
        validated_params = tool["parameters_class"](**parameters).dict()
        # Execute the tool function
        return tool["function"](validated_params)
    except Exception as e:
        return f"Error executing tool '{tool_name}': {str(e)}" 