import os
import requests
from agents import function_tool
import asyncio

@function_tool  
async def search_web(query: str) -> str:
    """
    Use Tavily Search API to search the web for a given query and return a formatted list of results.
    
    Args:
        query (str): The search query string.
    
    Returns:
        str: Formatted search results or error message.
    
    Raises:
        requests.exceptions.HTTPError: If HTTP request fails.
        requests.exceptions.RequestException: If any request-related error occurs.
        Exception: If any unexpected error occurs.
    """
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        return "Error: TAVILY_API_KEY not set for web search tool."
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "api_key": tavily_api_key,
        "query": query,
        "search_depth": "basic",
        "include_answer": False,
        "max_results": 3
    }
    
    try:
        response = requests.post("https://api.tavily.com/search", headers=headers, json=payload)
        response.raise_for_status()
        results_json = response.json()
        if not results_json.get("results"):
            return "No web search results found."
        formatted_results = []
        for item in results_json.get("results", []):
            title = item.get('title', 'N/A')
            url = item.get('url', 'N/A')
            snippet = item.get('content', 'N/A')[:150] + "..."
            formatted_results.append(f"Title: {title}\nURL: {url}\nSnippet: {snippet}\n---")
        return "\n".join(formatted_results) if formatted_results else "No results found."
    except requests.exceptions.HTTPError as http_err:
        return f"Web search HTTP error: {http_err} - Response: {response.text if response else 'No response'}"
    except requests.exceptions.RequestException as req_err:
        return f"Web search request error: {req_err}"
    except Exception as e:
        return f"An unexpected error occurred in web search: {e}" 
