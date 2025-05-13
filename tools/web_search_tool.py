import os
import requests
from agents import function_tool
import asyncio

@function_tool  
async def search_web(query: str) -> str:
    """Search the web for up-to-date information using Tavily's search API, enabling an AI Agent to access current, factual information from the internet and return formatted results with titles, URLs, and content snippets for most relevant matches; Args: query (str): the search query to look up on the web; Returns: str: formatted search results with titles, URLs, and content snippets or error message."""
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
