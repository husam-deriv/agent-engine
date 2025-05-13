import os
import json
import importlib.util
import subprocess
import sys
from typing import Dict, List, Any, Optional, Callable
from pydantic import BaseModel
from openai import AsyncOpenAI

class CustomToolManager:
    """
    Manages custom tools for AI agents, including creation, installation of dependencies,
    and management of required API keys.
    """
    
    def __init__(self, tools_dir: str = "custom_tools"):
        self.tools_dir = tools_dir
        self.custom_tools = {}
        self.load_custom_tools()
    
    def load_custom_tools(self):
        """Load all custom tools from the tools directory"""
        os.makedirs(self.tools_dir, exist_ok=True)
        
        # Iterate through subdirectories in the tools directory
        for tool_name in os.listdir(self.tools_dir):
            tool_dir = os.path.join(self.tools_dir, tool_name)
            
            if not os.path.isdir(tool_dir):
                continue
                
            # Check for definition.json file
            definition_file = os.path.join(tool_dir, "definition.json")
            if not os.path.exists(definition_file):
                continue
                
            # Check for Python implementation file
            implementation_file = os.path.join(tool_dir, f"{tool_name}.py")
            if not os.path.exists(implementation_file):
                continue
                
            try:
                # Load tool definition
                with open(definition_file, 'r') as f:
                    definition = json.load(f)
                
                # Load implementation dynamically
                spec = importlib.util.spec_from_file_location(tool_name, implementation_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Get the main function from the module
                function = getattr(module, tool_name)
                
                # Register the tool
                self.custom_tools[tool_name] = {
                    "definition": definition,
                    "function": function,
                    "module": module
                }
                
                print(f"Loaded custom tool: {tool_name}")
            except Exception as e:
                print(f"Error loading custom tool {tool_name}: {str(e)}")
    
    def get_custom_tool_definitions(self) -> List[Dict]:
        """Get function definitions for all custom tools"""
        return [tool["definition"] for tool in self.custom_tools.values()]
    
    def get_custom_tool_function_map(self) -> Dict[str, Callable]:
        """Get a map of function names to their implementations"""
        return {
            tool_name: tool_info["function"] 
            for tool_name, tool_info in self.custom_tools.items()
        }
    
    def get_custom_tool_descriptions(self) -> List[Dict[str, str]]:
        """Get descriptions of all custom tools for display in the UI"""
        return [
            {
                "name": tool_info["definition"]["function"]["name"],
                "description": tool_info["definition"]["function"]["description"],
                "type": tool_info["definition"].get("type", "function")
            }
            for tool_info in self.custom_tools.values()
        ]
    
    async def create_custom_tool(self, description: str, openai_client: AsyncOpenAI) -> Dict:
        """
        Create a new custom tool based on a natural language description.
        
        Args:
            description: Natural language description of the tool
            openai_client: OpenAI client for generating tool definition and implementation
            
        Returns:
            Information about the created tool
        """
        # Create temporary generator instance
        from custom_tool_generator import CustomToolGenerator
        generator = CustomToolGenerator(openai_client=openai_client)
        
        # Generate tool definition
        tool_def = await generator.generate_tool_definition(description)
        
        # Extract function name from tool definition
        function_name = tool_def["function"]["name"]
        
        # Generate implementation
        implementation = await generator.generate_implementation(tool_def)
        
        # Create directory for the tool
        tool_dir = os.path.join(self.tools_dir, function_name)
        os.makedirs(tool_dir, exist_ok=True)
        
        # Save the tool definition
        definition_file = os.path.join(tool_dir, "definition.json")
        with open(definition_file, 'w') as f:
            json.dump(tool_def, f, indent=2)
        
        # Save the implementation
        implementation_file = os.path.join(tool_dir, f"{function_name}.py")
        with open(implementation_file, 'w') as f:
            f.write(implementation["code"])
        
        # Save requirements
        requirements = implementation.get("module_installation", [])
        if requirements:
            requirements_file = os.path.join(tool_dir, "requirements.txt")
            with open(requirements_file, 'w') as f:
                f.write("\n".join(requirements))
        
        # Save required secrets
        secrets = implementation.get("secret_keys", [])
        if secrets:
            secrets_file = os.path.join(tool_dir, "secrets.txt")
            with open(secrets_file, 'w') as f:
                f.write("\n".join(secrets))
        
        return {
            "name": function_name,
            "definition": tool_def,
            "requirements": requirements,
            "secrets": secrets,
            "directory": tool_dir
        }
    
    def install_tool_requirements(self, tool_name: str) -> Dict[str, Any]:
        """
        Install the requirements for a specific tool
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Status of the installation
        """
        tool_dir = os.path.join(self.tools_dir, tool_name)
        requirements_file = os.path.join(tool_dir, "requirements.txt")
        
        if not os.path.exists(requirements_file):
            return {"status": "no_requirements", "message": "No requirements to install"}
        
        try:
            # Install requirements using pip
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", requirements_file
            ])
            return {"status": "success", "message": f"Successfully installed requirements for {tool_name}"}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"Error installing requirements: {str(e)}"}
    
    def get_required_secrets(self, tool_name: str) -> List[str]:
        """
        Get the list of required secrets for a tool
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            List of required secret keys
        """
        tool_dir = os.path.join(self.tools_dir, tool_name)
        secrets_file = os.path.join(tool_dir, "secrets.txt")
        
        if not os.path.exists(secrets_file):
            return []
        
        with open(secrets_file, 'r') as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    
    def delete_custom_tool(self, tool_name: str) -> bool:
        """
        Delete a custom tool
        
        Args:
            tool_name: Name of the tool to delete
            
        Returns:
            True if successful, False otherwise
        """
        if tool_name not in self.custom_tools:
            return False
        
        # Remove from memory
        del self.custom_tools[tool_name]
        
        # Remove files
        import shutil
        tool_dir = os.path.join(self.tools_dir, tool_name)
        if os.path.exists(tool_dir) and os.path.isdir(tool_dir):
            shutil.rmtree(tool_dir)
            
        return True
    
    def execute_custom_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """
        Execute a custom tool with the given parameters
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            
        Returns:
            Result of the tool execution
        """
        if tool_name not in self.custom_tools:
            return f"Error: Tool '{tool_name}' not found"
        
        try:
            # Execute the tool function
            function = self.custom_tools[tool_name]["function"]
            return function(**parameters)
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

# Initialize the custom tool manager
custom_tool_manager = CustomToolManager() 