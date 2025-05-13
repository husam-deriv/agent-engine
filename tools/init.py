# This file can be auto-generated or managed to register all tools.
from .csv_query_tool import csv_query
from .deep_search_tool import deep_research
from .mermaid_generator_tool import generate_mermaid_flowchart
from .interactive_ml_pipeline import run_interactive_pipeline
from .web_search_tool import search_web
from .rag_tool import rag_collection_query


all_defined_tools = {
    "query_csv_data": {
        "func": csv_query,
        "description": "Query and filter CSV data using pandas syntax, useful for analyzing tabular data without writing code or when you need to extract specific information based on conditions."
    },
    "create_mermaid_diagram": {
        "func": generate_mermaid_flowchart,
        "description": "Generate visual diagrams from text descriptions, useful for creating flowcharts, sequence diagrams, and other visualizations to explain complex processes or relationships."
    },
    "search_web": {
        "func": search_web,
        "description": "Search the internet for up-to-date information, useful when you need facts, current events, or domain knowledge that may not be in your training data."
    },
    "run_interactive_pipeline": {
        "func": run_interactive_pipeline,
        "description": "Automatically build and run machine learning models on CSV data using natural language queries, useful for making predictions or analyzing patterns in tabular data without ML expertise."
    },
    "deep_research": {
        "func": deep_research,
        "description": "Perform comprehensive research on complex topics with analysis and source verification, useful for in-depth exploration of subjects requiring evidence-based answers with proper citations."
    },
    "rag_collection_query": {
        "func": rag_collection_query,
        "description": "Search vector databases for semantically relevant information, useful for retrieving domain-specific knowledge from previously embedded document collections when exact keyword matching is insufficient."
    },
}
