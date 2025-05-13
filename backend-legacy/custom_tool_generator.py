import json
from typing import Dict, List, Any
from openai import AsyncOpenAI

class CustomToolGenerator:
    """
    Generates custom tool definitions and implementations for AI agents 
    based on natural language descriptions.
    """
    
    def __init__(self, openai_client: AsyncOpenAI = None):
        self.openai_client = openai_client
        self.model = "gpt-4o"
    
    async def generate_tool_definition(self, description: str) -> Dict:
        """
        Generate a complete tool definition from a natural language description using LLM.
        
        Args:
            description: Natural language description of the tool
            
        Returns:
            A dictionary representing the tool in OpenAI function calling format
        """
        # Example tool definition to guide the LLM
        example_tool = {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "The temperature unit to use. Defaults to fahrenheit."
                        }
                    },
                    "required": ["location"]
                }
            }
        }
        
        prompt = f"""
You are an expert at creating tool definitions for AI agents. I need you to create a tool definition based on this description:

"{description}"

The tool definition should follow the OpenAI function calling format. Here's an example:

{json.dumps(example_tool, indent=2)}

Please create a complete tool definition that includes:
1. An appropriate function name
2. A clear description
3. Well-defined parameters with types and descriptions
4. Required parameters list

Return ONLY the JSON tool definition without any explanation or markdown formatting.
"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert at creating tool definitions for AI agents."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON from the response
            try:
                # Find JSON content in the response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    tool_def = json.loads(json_content)
                    return tool_def
                else:
                    raise ValueError("Could not extract valid JSON from LLM response")
            except json.JSONDecodeError:
                raise ValueError("Could not parse LLM response as JSON")
                
        except Exception as e:
            print(f"Error generating tool definition: {str(e)}")
            # Return a minimal default tool definition
            return {
                "type": "function",
                "function": {
                    "name": "custom_tool",
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
    
    async def generate_implementation(self, tool_def: Dict) -> Dict:
        """
        Generate Python code to implement the tool function.
        
        Args:
            tool_def: Tool definition dictionary
            
        Returns:
            Dictionary containing the implementation details including code, required modules, and secrets
        """
        function_name = tool_def["function"]["name"]
        description = tool_def["function"]["description"]
        parameters = tool_def["function"]["parameters"]["properties"]
        required_params = tool_def["function"]["parameters"].get("required", [])
        
        # Example implementation to guide the LLM
        example_implementation = {
            "code": """
import requests
from typing import Dict, Any, Optional

def get_weather(location: str, unit: Optional[str] = "fahrenheit") -> Dict[str, Any]:
    \"\"\"
    Get the current weather in a given location.
    
    Args:
        location: The city and state, e.g. San Francisco, CA
        unit: The temperature unit to use. Defaults to fahrenheit.
    
    Returns:
        Dictionary containing the weather information
    \"\"\"
    api_key = "YOUR_WEATHER_API_KEY"
    base_url = "https://api.weatherapi.com/v1/current.json"
    
    params = {
        "key": api_key,
        "q": location,
        "aqi": "no"
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract relevant weather information
        current = data["current"]
        location_data = data["location"]
        
        # Convert temperature if needed
        temp = current["temp_f"] if unit == "fahrenheit" else current["temp_c"]
        
        return {
            "location": f"{location_data['name']}, {location_data['region']}",
            "temperature": temp,
            "unit": unit,
            "condition": current["condition"]["text"],
            "humidity": current["humidity"],
            "wind_speed": current["wind_mph"] if unit == "fahrenheit" else current["wind_kph"]
        }
    except Exception as e:
        return {"error": str(e)}
""",
            "module_installation": ["requests"],
            "secret_keys": ["WEATHER_API_KEY"]
        }
        
        # Create a prompt for the LLM
        prompt = f"""
You are an expert Python developer. Create a complete implementation for a tool with the following specifications:

Tool Definition:
{json.dumps(tool_def, indent=2)}

Please provide a complete implementation of this function that fulfills its purpose.
Your response must be in this exact JSON format:
{{
  "code": "<complete Python code implementation>",
  "module_installation": ["list", "of", "modules", "to", "install"],
  "secret_keys": ["list", "of", "secret", "keys", "if", "needed"]
}}

Here's an example of a well-formatted response:
{json.dumps(example_implementation, indent=2)}

The code should be fully functional, handle edge cases appropriately, and include proper type hints and docstrings.
If the tool requires any API keys or credentials, make sure to include them in the secret_keys list.
"""
        
        # Call the LLM API using OpenAI client
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert Python developer who creates high-quality tool implementations."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.2
            )
            
            # Extract the content from the response
            content = response.choices[0].message.content
            
            # Parse the JSON response from the LLM
            try:
                # Find JSON content in the response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    implementation_details = json.loads(json_content)
                    return implementation_details
                else:
                    raise ValueError("Could not extract valid JSON from LLM response")
            except json.JSONDecodeError:
                raise ValueError("Could not parse LLM response as JSON")
                
        except Exception as e:
            print(f"Error generating implementation: {str(e)}")
            # Return a minimal implementation
            return {
                "code": f"def {function_name}():\n    \"\"\"Placeholder implementation\"\"\"\n    return {{'status': 'not implemented'}}",
                "module_installation": [],
                "secret_keys": []
            } 