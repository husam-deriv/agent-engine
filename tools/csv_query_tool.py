import pandas as pd
from agents import function_tool
import asyncio
import os

@function_tool  
async def csv_query(csv_path: str, query: str) -> str:
    """Query and filter CSV data using pandas DataFrame query syntax, enabling an AI Agent to extract specific information from tabular data without having to process the entire file or implement custom filtering logic; Args: csv_path (str): path to the CSV file, query (str): filter expression using pandas query syntax; Returns: str: formatted query results or error message."""
    try:
        # Adjust the path based on current working directory
        cwd = os.getcwd()
        adjusted_path = csv_path
        
        # If the path starts with backend/ but we're already in backend directory
        if cwd.endswith('/backend') and csv_path.startswith('backend/'):
            adjusted_path = csv_path[len('backend/'):]
        
        print(f"Reading CSV from: {adjusted_path}")
        df = pd.read_csv(adjusted_path)
        if df.empty:
            return "Error: The CSV file is empty or could not be read properly."
        result = df.query(query)
        
        if result.empty:
            return "Query returned no results."

        result_count = len(result)
        
        if result_count > 100:
            output_df = result.head(100)
            output_str = output_df.to_string()
            return f"{output_str}\n\nNote: Query returned {result_count} rows. Displaying the first 100 rows."
        else:
            return result.to_string()

    except FileNotFoundError:
        return f"Error: CSV file not found at '{adjusted_path}' (original path: '{csv_path}')."
    except pd.errors.ParserError:
        return f"Error: Could not parse the CSV file at '{adjusted_path}'. Ensure it is a valid CSV."
    except Exception as e:
        return f"Query error executing '{query}' on '{adjusted_path}': {e}" 
