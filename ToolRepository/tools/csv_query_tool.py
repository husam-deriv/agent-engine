import pandas as pd
from agents import function_tool
import asyncio

@function_tool  
async def csv_query(csv_path: str, query: str) -> str:
    """
    Query a CSV file using pandas DataFrame.query() syntax.
    
    Args:
        csv_path (str): The file path to the CSV file.
        query (str): The query string in pandas DataFrame.query() syntax (e.g., 'column_name > 5 and another_column == "some_value"').
    
    Returns:
        str: The head of the query result as a string or error message.
    
    Raises:
        FileNotFoundError: If the CSV file is not found.
        pd.errors.ParserError: If the CSV file cannot be parsed.
        Exception: If any other error occurs during query execution.
    """
    try:
        df = pd.read_csv(csv_path)
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
        return f"Error: CSV file not found at '{csv_path}'."
    except pd.errors.ParserError:
        return f"Error: Could not parse the CSV file at '{csv_path}'. Ensure it is a valid CSV."
    except Exception as e:
        return f"Query error executing '{query}' on '{csv_path}': {e}" 
