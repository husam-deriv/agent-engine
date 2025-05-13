# This file can be auto-generated or managed to register all tools.

from .ml_predictor_tool import ml_predictor
from .csv_query_tool import csv_query
from .python_executor_tool import run_python_code
from .mermaid_generator_tool import generate_mermaid_flowchart
from .rag_tool import query_rag_context
from .web_search_tool import search_web


all_defined_tools = {
    "ml_predictor": ml_predictor,
    "query_csv_data": csv_query,
    "execute_python_code": run_python_code,
    "create_mermaid_diagram": generate_mermaid_flowchart,
    "query_rag_pipeline": query_rag_context,
    "search_web": search_web,
}

def get_all_tools_map():
    """Returns a dictionary mapping tool names to their callable functions."""
    return all_defined_tools

# List of all tools that can be dynamically loaded by the agent
# It's often better to derive __all__ from the keys of the tools map
# to ensure consistency.
__all__ = list(all_defined_tools.keys()) 