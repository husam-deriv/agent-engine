"""
Deep Research Utility for comprehensive research and analysis.

This module provides tools for performing in-depth research on a topic by:
1. Searching the web using Tavily and/or Google Search
2. Analyzing results with GPT-4.1 or Gemini 2.5 Flash
3. Providing detailed analysis with Chain of Thought reasoning
4. Generating comprehensive reports with sources and reliability ratings

Usage:
    result = deep_research("What are the latest advancements in quantum computing?")
    print(result["analysis"]["comprehensive_answer"])
"""

import os
import json
import requests
import hashlib
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import logging
import re
from agents import function_tool

from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import OpenAI (for LiteLLM)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available. Install with: pip install openai")

# Try to import Vertex AI (used as fallback)
# try:
#     # import vertexai
#     # from vertexai.generative_models import GenerativeModel
#     VERTEX_AI_AVAILABLE = True
#     logger.info("Vertex AI libraries loaded successfully")
# except ImportError:
#     VERTEX_AI_AVAILABLE = False
#     logger.info("Vertex AI libraries not available")

class DeepResearch:
    """Utility class for performing deep research using LiteLLM, Tavily and optionally Vertex AI."""
    
    def __init__(self, disable_cache=False):
        """
        Initialize the DeepResearch utility.
        
        Args:
            disable_cache (bool): If True, disables caching of results
        """
        # Initialize LiteLLM client if available
        self.litellm_api_key = os.environ.get("LITELLM_API_KEY")
        self.client = None
        
        if OPENAI_AVAILABLE and self.litellm_api_key:
            self.client = OpenAI(
                base_url="https://litellm.deriv.ai/v1",
                api_key=self.litellm_api_key
            )
            logger.info("LiteLLM API key found")
        else:
            logger.warning("LiteLLM API key not set or OpenAI library not available")
            
        # Initialize Tavily API
        self.tavily_api_key = os.environ.get("TAVILY_API_KEY")
        if self.tavily_api_key:
            logger.info("Tavily API key found")
        else:
            logger.warning("Tavily API key not set")
            
        # Initialize Google Search API
        self.google_api_key = os.environ.get("GOOGLE_API_KEY")
        self.search_engine_id = os.environ.get("GOOGLE_SEARCH_ENGINE_ID")
        if self.google_api_key and self.search_engine_id:
            logger.info("Google Search API configuration found")
        else:
            logger.warning("Google Search API not fully configured")
        
        # Vertex AI model (initialized only if needed)
        self.gemini_model = None
        
        # Cache configuration
        self.cache_enabled = not disable_cache
        self.cache_dir = "data/research_cache"
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
    
    # def _init_gemini_if_needed(self):
    #     """
    #     Initialize Gemini model if needed and not already initialized.
        
    #     Returns:
    #         bool: True if model was successfully initialized, False otherwise
    #     """
    #     if not self.gemini_model and VERTEX_AI_AVAILABLE:
    #         try:
    #             # Initialize vertexai
    #             vertexai.init()
                
    #             try:
    #                 logger.info("Initializing Gemini model: gemini-2.5-flash")
    #                 self.gemini_model = GenerativeModel("gemini-2.5-flash")
    #                 # Test the model with a simple prompt to ensure it's working
    #                 test_response = self.gemini_model.generate_content("Hello, this is a test.")
    #                 if test_response and test_response.text:
    #                     logger.info("Model test successful for gemini-2.5-flash")
    #                 else:
    #                     logger.warning("Model initialization succeeded but test failed")
    #                     self.gemini_model = None
    #             except Exception as e:
    #                 logger.warning(f"Failed to initialize Gemini 2.5 Flash model: {e}")
                    
    #         except Exception as e:
    #             logger.warning(f"Failed to initialize vertexai: {e}")
        
    #     return self.gemini_model is not None
    
    def _cache_key(self, query: str) -> str:
        """
        Generate a cache key for a query.
        
        Args:
            query (str): The research query
            
        Returns:
            str: MD5 hash of the query to use as cache key
        """
        return hashlib.md5(query.encode()).hexdigest()
    
    def _get_cached_result(self, query: str) -> Optional[Dict]:
        """
        Get cached result for a query if it exists and is not expired.
        
        Args:
            query (str): The research query
            
        Returns:
            Optional[Dict]: Cached result or None if not found/expired
        """
        if not self.cache_enabled:
            return None
            
        cache_key = self._cache_key(query)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            # Check if cache is expired (older than 1 day)
            cache_time = datetime.fromisoformat(data.get("timestamp", "2000-01-01T00:00:00"))
            now = datetime.now()
            if (now - cache_time).days > 1:
                return None
            
            return data
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return None
    
    def _save_to_cache(self, query: str, result: Dict) -> None:
        """
        Save result to cache.
        
        Args:
            query (str): The research query
            result (Dict): The research results to cache
        """
        if not self.cache_enabled:
            return
        
        cache_key = self._cache_key(query)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            # Add timestamp
            result["timestamp"] = datetime.now().isoformat()
            
            with open(cache_file, 'w') as f:
                json.dump(result, f)
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
    
    def tavily_search(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        Perform a web search using Tavily Search API.
        
        Args:
            query (str): The search query
            num_results (int): Maximum number of results to return
            
        Returns:
            List[Dict]: List of search results in standardized format
        """
        try:
            if not self.tavily_api_key:
                logger.warning("Tavily API key not set, skipping Tavily search")
                return []
            
            # Tavily API endpoint
            url = "https://api.tavily.com/search"
            
            # Prepare request parameters
            params = {
                "api_key": self.tavily_api_key,
                "query": query,
                "max_results": num_results,
                "include_domains": [],
                "exclude_domains": [],
                "search_depth": "advanced"  # Use 'advanced' for more comprehensive results
            }
            
            # Make the request
            response = requests.post(url, json=params, timeout=30)
            response.raise_for_status()
            
            # Parse the results
            data = response.json()
            
            # Convert to our standard format
            search_results = []
            if "results" in data:
                for item in data["results"]:
                    search_results.append({
                        "title": item.get("title", "Untitled"),
                        "link": item.get("url", "#"),
                        "snippet": item.get("content", "No description available"),
                        "displayLink": item.get("url", "#").split("/")[2] if "/" in item.get("url", "#") else "unknown source"
                    })
            
            logger.info(f"Tavily search returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Error in Tavily search: {e}")
            # Return empty list to signal fallback to other search methods
            return []
    
    def gpt41_analyze_search_results(self, query: str, search_results: List[Dict]) -> Dict:
        """
        Analyze search results using GPT-4.1 via LiteLLM.
        
        Args:
            query (str): The original research query
            search_results (List[Dict]): The search results to analyze
            
        Returns:
            Dict: Analysis with comprehensive answer, insights, and source evaluations,
                 or None if analysis failed
        """
        if not self.client or not self.litellm_api_key:
            logger.warning("LiteLLM client not available, skipping GPT-4.1 analysis")
            return None
            
        try:
            # Extract content from search results
            content = self.extract_content_from_search(search_results)
            
            # Prepare system prompt for Chain of Thought reasoning
            system_prompt = """You are an expert research analyst with comprehensive knowledge across various domains.
Your task is to analyze search results and produce detailed, thoughtful analyses with clear reasoning.
For each response, follow these steps:
1. Begin by understanding the query and identifying key concepts
2. Examine the search results methodically, noting both supporting evidence and contradictions
3. Compare information across sources, evaluating credibility and relevance
4. Synthesize findings into a coherent analysis
5. Organize insights by subtopic while maintaining connections between related concepts
6. Identify gaps in current knowledge and areas of conflicting information
7. Format your final response as structured JSON
"""

            # Create user prompt for analysis with Chain of Thought reasoning
            user_prompt = f"""
Research Query: {query}

Here are search results to analyze:

{content}

Follow this detailed Chain of Thought reasoning process:

Step 1: Analyze the query
- Break down what "{query}" is asking
- Identify key concepts and relationships
- Determine what a comprehensive answer requires

Step 2: Evaluate information quality
- Assess the credibility of provided sources
- Note information that appears in multiple sources
- Identify potential biases or limitations

Step 3: Synthesize comprehensive answer
- Connect key findings across sources
- Prioritize well-supported information
- Address nuances and complexities

Step 4: Organize insights by subtopic
- Create logical groupings of related information
- Assign confidence levels to each insight based on evidence quality

Step 5: Identify limitations and conflicts
- Note areas requiring more research
- Flag contradictory information across sources

Format your final analysis as a JSON object with this structure:
```json
{{
    "comprehensive_answer": "A detailed, nuanced answer that incorporates all key findings with reasoning",
    "reasoning_process": "Explicit description of how you reached your conclusions from the provided information",
    "insights": [
        {{
            "subtopic": "First subtopic name",
            "points": ["Detailed point 1", "Detailed point 2", ...],
            "confidence": 0-10 rating of confidence in these insights,
            "reasoning": "Explanation of how you derived these points and why you assigned this confidence score"
        }},
        ...
    ],
    "sources": [
        {{
            "title": "Source title",
            "url": "Source URL",
            "relevance_score": 0-10 integer score,
            "key_contribution": "What this source specifically contributes to the answer",
            "reliability": 0-10 rating of source reliability,
            "reasoning": "Why you assigned these scores to this source"
        }},
        ...
    ],
    "research_gaps": ["Area needing more research 1", "Area needing more research 2", ...],
    "conflicting_info": ["Point of conflict 1", "Point of conflict 2", ...]
}}
```

Return ONLY the JSON object, with no additional text before or after.
"""

            # Make the API call
            response = self.client.chat.completions.create(
                model="gpt-4.1",  # Use GPT-4.1 through LiteLLM
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                timeout=120  # Longer timeout for complex analysis
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                # Extract JSON if it's within markdown code blocks
                if "```json" in response_text:
                    json_match = re.search(r'```json\s+(.*?)\s+```', response_text, re.DOTALL)
                    if json_match:
                        json_content = json_match.group(1)
                    else:
                        json_content = response_text
                elif "```" in response_text:
                    json_match = re.search(r'```\s+(.*?)\s+```', response_text, re.DOTALL)
                    if json_match:
                        json_content = json_match.group(1)
                    else:
                        json_content = response_text
                else:
                    json_content = response_text
                
                # Find JSON object by locating matching braces
                if "{" in json_content and "}" in json_content:
                    # Find the first opening brace and the last closing brace
                    start_idx = json_content.find("{")
                    end_idx = json_content.rfind("}")
                    if start_idx >= 0 and end_idx > start_idx:
                        json_content = json_content[start_idx:end_idx+1]
                
                # Parse the JSON
                parsed = json.loads(json_content)
                
                # Ensure required fields are present
                self._ensure_required_fields(parsed, search_results)
                logger.info("GPT-4.1 analysis completed successfully")
                return parsed
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GPT-4.1 response as JSON: {e}")
                logger.error(f"Response content: {response_text[:200]}...")
                return None
                
        except Exception as e:
            logger.error(f"Error in GPT-4.1 analysis: {e}")
            return None
    
    def gemini_analyze_search_results(self, query: str, search_results: List[Dict]) -> Dict:
        """
        Analyze search results using Gemini 2.5 Flash (fallback method).
        
        Args:
            query (str): The original research query
            search_results (List[Dict]): The search results to analyze
            
        Returns:
            Dict: Analysis with comprehensive answer, insights, and source evaluations,
                 or None if analysis failed
        """
        if not self._init_gemini_if_needed():
            logger.error("Gemini model initialization failed")
            return None
            
        try:
            # Extract content from search results
            content = self.extract_content_from_search(search_results)
            
            # Create prompt for analysis with Chain of Thought reasoning
            prompt = f"""
Research Query: {query}

I'll provide you with search results from a web search. Please perform a detailed chain-of-thought analysis:

Step 1: Analyze the query "{query}"
- What are the key concepts and components?
- What would a comprehensive answer include?

Step 2: Evaluate the search results
- Which sources seem most credible and why?
- What are the key themes across multiple sources?
- What information appears contradictory or uncertain?

Step 3: Develop insights by subtopic
- What are the main subtopics related to this query?
- What are the most important points for each subtopic?
- How confident can we be in these insights based on the evidence?

Step 4: Identify limitations
- What key information is missing?
- Where do sources conflict?

Here are the search results:

{content}

Please format your response as a JSON object with the following structure:
{{
    "comprehensive_answer": "A detailed, nuanced answer to the original query that incorporates all key findings with reasoning.",
    "reasoning_process": "Explanation of how you analyzed the information and reached your conclusions",
    "insights": [
        {{
            "subtopic": "First subtopic name",
            "points": ["Detailed point 1", "Detailed point 2", ...],
            "confidence": 0-10 rating of confidence in these insights,
            "reasoning": "Why you believe these points and how you determined this confidence level"
        }},
        ...
    ],
    "sources": [
        {{
            "title": "Source title",
            "url": "Source URL",
            "relevance_score": 0-10 integer score,
            "key_contribution": "What this source specifically contributes to the answer",
            "reliability": 0-10 rating of source reliability,
            "reasoning": "Why you assigned these scores to this source"
        }},
        ...
    ],
    "research_gaps": ["Area needing more research 1", "Area needing more research 2", ...],
    "conflicting_info": ["Point of conflict 1", "Point of conflict 2", ...]
}}
"""
            
            # Add timeout to prevent hanging on model generation
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    response = self.gemini_model.generate_content(prompt, timeout=90)
                    break
                except Exception as e:
                    if attempt < max_retries:
                        logger.warning(f"Attempt {attempt+1} failed: {e}. Retrying...")
                        time.sleep(2)  # Wait before retrying
                    else:
                        raise
            
            # Try to parse the response as JSON
            try:
                # Extract JSON if it's within markdown code blocks
                response_text = response.text
                
                if "```json" in response_text:
                    json_match = re.search(r'```json\s+(.*?)\s+```', response_text, re.DOTALL)
                    if json_match:
                        json_content = json_match.group(1)
                    else:
                        json_content = response_text
                elif "```" in response_text:
                    json_match = re.search(r'```\s+(.*?)\s+```', response_text, re.DOTALL)
                    if json_match:
                        json_content = json_match.group(1)
                    else:
                        json_content = response_text
                else:
                    json_content = response_text
                
                # Find JSON object by locating matching braces
                if "{" in json_content and "}" in json_content:
                    # Find the first opening brace and the last closing brace
                    start_idx = json_content.find("{")
                    end_idx = json_content.rfind("}")
                    if start_idx >= 0 and end_idx > start_idx:
                        json_content = json_content[start_idx:end_idx+1]
                
                # Parse the JSON
                parsed = json.loads(json_content)
                
                # Ensure required fields are present
                self._ensure_required_fields(parsed, search_results)
                logger.info("Gemini analysis completed successfully")
                return parsed
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response as JSON: {e}")
                logger.error(f"Response content: {response_text[:200]}...")
                return self._create_fallback_analysis(query, search_results, f"Failed to parse model response: {e}")
                
        except Exception as e:
            logger.error(f"Error in Gemini analysis: {e}")
            return self._create_fallback_analysis(query, search_results, f"Error in analysis: {e}")
    
    def _ensure_required_fields(self, parsed: Dict, search_results: List[Dict]) -> None:
        """
        Ensure all required fields are present in the parsed result.
        
        Args:
            parsed (Dict): The parsed analysis result to check and modify
            search_results (List[Dict]): The original search results
        """
        if not isinstance(parsed, dict):
            logger.warning("Model returned non-dict JSON response")
            parsed = {"comprehensive_answer": str(parsed)}
        
        # Ensure comprehensive_answer
        if "comprehensive_answer" not in parsed:
            parsed["comprehensive_answer"] = "No comprehensive answer provided."
        
        # Add reasoning_process if missing
        if "reasoning_process" not in parsed:
            parsed["reasoning_process"] = "Analysis process not explicitly detailed by the model."
        
        # Ensure insights with confidence and reasoning
        if "insights" not in parsed or not isinstance(parsed["insights"], list):
            parsed["insights"] = [{
                "subtopic": "Key Points", 
                "points": ["No structured insights available."],
                "confidence": 5,
                "reasoning": "Default reasoning due to missing insights."
            }]
        else:
            # Ensure all insights have the required fields
            for insight in parsed["insights"]:
                if "confidence" not in insight:
                    insight["confidence"] = 5
                if "reasoning" not in insight:
                    insight["reasoning"] = "No explicit reasoning provided for this insight."
        
        # Ensure sources with ratings and reasoning
        if "sources" not in parsed or not isinstance(parsed["sources"], list):
            parsed["sources"] = [
                {
                    "title": result["title"], 
                    "url": result["link"], 
                    "relevance_score": 5, 
                    "key_contribution": "Source information",
                    "reliability": 5,
                    "reasoning": "Default assessment as specific evaluation was not provided."
                } for result in search_results[:5]
            ]
        else:
            # Ensure all sources have the required fields
            for source in parsed["sources"]:
                if "reliability" not in source:
                    source["reliability"] = 5
                if "reasoning" not in source:
                    source["reasoning"] = "No explicit reasoning provided for source assessment."
        
        # Add research gaps if missing
        if "research_gaps" not in parsed or not isinstance(parsed["research_gaps"], list):
            parsed["research_gaps"] = ["No specific research gaps identified."]
        
        # Add conflicting info if missing
        if "conflicting_info" not in parsed or not isinstance(parsed["conflicting_info"], list):
            parsed["conflicting_info"] = ["No conflicting information identified."]
    
    def _create_fallback_analysis(self, query: str, search_results: List[Dict], error_msg: str) -> Dict:
        """
        Create a fallback analysis when models fail.
        
        Args:
            query (str): The original research query
            search_results (List[Dict]): The search results to analyze
            error_msg (str): Error message explaining why fallback was needed
            
        Returns:
            Dict: Basic analysis created from search results
        """
        # Create a basic analysis from the search results
        comprehensive_answer = f"Analysis could not be completed properly: {error_msg}. However, search results were found."
        
        # Extract top keywords from query
        query_keywords = set(query.lower().split())
        
        # Create basic insights based on search result titles
        insights = []
        topics_seen = set()
        
        for result in search_results[:5]:
            # Extract potential topic from title
            title_words = result["title"].split()
            if len(title_words) > 2:
                potential_topic = " ".join(title_words[:3])
                if potential_topic not in topics_seen:
                    topics_seen.add(potential_topic)
                    insights.append({
                        "subtopic": potential_topic,
                        "points": [result["snippet"]],
                        "confidence": 3,
                        "reasoning": "Extracted directly from search result, low confidence due to limited analysis."
                    })
        
        # If no insights were created, add a default one
        if not insights:
            insights = [{
                "subtopic": "Search Results",
                "points": ["Information extracted directly from search results without analysis."],
                "confidence": 2,
                "reasoning": "Minimal processing of raw search results due to analysis failure."
            }]
        
        # Create basic source evaluations
        sources = [
            {
                "title": result["title"],
                "url": result["link"],
                "relevance_score": 5,
                "key_contribution": result["snippet"][:100] + "...",
                "reliability": 5,
                "reasoning": "Default rating as detailed analysis failed."
            } for result in search_results[:5]
        ]
        
        return {
            "comprehensive_answer": comprehensive_answer,
            "reasoning_process": f"Analysis process was limited due to error: {error_msg}",
            "insights": insights,
            "sources": sources,
            "research_gaps": ["Analysis incomplete due to error."],
            "conflicting_info": ["Analysis incomplete due to error."]
        }
    
    def google_search(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        Perform a web search using Google Search API.
        
        Args:
            query (str): The search query
            num_results (int): Maximum number of results to return
            
        Returns:
            List[Dict]: List of search results in standardized format
        """
        try:
            # Check if API key and Search Engine ID are available
            if not self.google_api_key or not self.search_engine_id:
                logger.error("Google Search API key or Search Engine ID not set")
                return []
            
            # Set up the API endpoint
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.google_api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": min(num_results, 10)  # API limit is 10
            }
            
            # Make the request
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Parse the results
            data = response.json()
            
            # Format results in the same structure as expected by other methods
            search_results = []
            if "items" in data:
                for item in data["items"]:
                    search_results.append({
                        "title": item.get("title", "Untitled"),
                        "link": item.get("link", "#"),
                        "snippet": item.get("snippet", "No description available"),
                        "displayLink": item.get("displayLink", "unknown source")
                    })
            
            logger.info(f"Google search returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Error in Google search: {e}")
            # Return empty list
            return []
    
    def extract_content_from_search(self, search_results: List[Dict]) -> str:
        """
        Extract and concatenate content from search results.
        
        Args:
            search_results (List[Dict]): The search results to process
            
        Returns:
            str: Formatted string containing all search result information
        """
        content = ""
        for i, result in enumerate(search_results):
            content += f"[{i+1}] {result['title']}\n"
            content += f"Source: {result['link']}\n"
            content += f"Summary: {result['snippet']}\n\n"
        
        return content
    
    def generate_visual_data(self, analysis: Dict) -> Dict:
        """
        Generate enhanced visualization data from the analysis.
        
        Args:
            analysis (Dict): The analysis results
            
        Returns:
            Dict: Structured data for visualization, including topics, sources, and connections
        """
        # Extract topics from insights
        topics = []
        for insight in analysis.get("insights", []):
            topics.append({
                "name": insight["subtopic"],
                "confidence": insight.get("confidence", 5),
                "points_count": len(insight.get("points", [])),
                "reasoning": insight.get("reasoning", "No reasoning provided")
            })
        
        # Create source ratings for visualization with reliability scores
        source_ratings = [
            {
                "name": source["title"][:30] + "..." if len(source["title"]) > 30 else source["title"],
                "url": source["url"],
                "score": source["relevance_score"],
                "contribution": source["key_contribution"],
                "reliability": source.get("reliability", 5),
                "reasoning": source.get("reasoning", "No reasoning provided")
            }
            for source in analysis.get("sources", [])
        ]
        
        # Create a connections graph between topics and sources
        connections = []
        for i, insight in enumerate(analysis.get("insights", [])):
            for j, source in enumerate(analysis.get("sources", [])):
                # Create connections based on keyword matching with strength proportional to relevance
                topic_keywords = set(insight["subtopic"].lower().split())
                source_keywords = set(source["key_contribution"].lower().split())
                
                # Calculate keyword overlap
                common_words = topic_keywords.intersection(source_keywords)
                if common_words or j < 3:  # Connect to top sources regardless
                    strength = 0.3  # Base strength
                    
                    # Add strength for keyword matches
                    strength += 0.1 * len(common_words)
                    
                    # Add strength based on source relevance
                    strength += source["relevance_score"] / 20
                    
                    # Ensure strength is in range [0.1, 1.0]
                    strength = min(max(strength, 0.1), 1.0)
                    
                    connections.append({
                        "from": f"topic_{i}",
                        "to": f"source_{j}",
                        "strength": strength,
                        "keywords": list(common_words)
                    })
        
        # Add research gaps and conflicting info to visualization
        research_gaps = analysis.get("research_gaps", [])
        conflicting_info = analysis.get("conflicting_info", [])
        
        return {
            "topics": topics,
            "source_ratings": source_ratings,
            "connections": connections,
            "research_gaps": research_gaps,
            "conflicting_info": conflicting_info,
            "reasoning_process": analysis.get("reasoning_process", "No reasoning process provided"),
            "query_complexity": len(topics) + len(source_ratings)  # A simple metric of research complexity
        }
    
    def _merge_search_results(self, search_results_list: List[List[Dict]]) -> List[Dict]:
        """
        Merge search results from multiple sources, removing duplicates.
        
        Args:
            search_results_list (List[List[Dict]]): List of search result lists to merge
            
        Returns:
            List[Dict]: Merged and deduplicated search results
        """
        merged_results = []
        seen_urls = set()
        
        for results in search_results_list:
            for result in results:
                url = result.get("link", "")
                # Skip results with no URL or already seen URLs
                if not url or url == "#" or url in seen_urls:
                    continue
                
                seen_urls.add(url)
                merged_results.append(result)
        
        return merged_results
    
    def perform_research(self, query: str, num_results: int = 10) -> Dict:
        """
        Perform deep research on a query using LiteLLM and search providers.
        
        Args:
            query (str): The research query
            num_results (int): Maximum number of search results to request
            
        Returns:
            Dict: Comprehensive research results including analysis, sources, and visualizations
        """
        try:
            # Check cache first
            cached_result = self._get_cached_result(query)
            if cached_result:
                logger.info(f"Using cached result for query: {query}")
                return cached_result
            
            # Search results collection
            all_search_results = []
            
            # Step 1: Try Tavily search first
            logger.info(f"Performing Tavily search for: {query}")
            tavily_results = []
            try:
                tavily_results = self.tavily_search(query, num_results)
                if tavily_results:
                    logger.info(f"Tavily search successful with {len(tavily_results)} results")
                    all_search_results.append(tavily_results)
                else:
                    logger.warning("Tavily search returned no results")
            except Exception as e:
                logger.error(f"Error in Tavily search: {e}")
            
            # Step 2: Try Google Search if Tavily returned insufficient results
            if len(tavily_results) < 5:
                logger.info("Tavily returned insufficient results, trying Google Search...")
                google_results = self.google_search(query, num_results)
                if google_results:
                    logger.info(f"Google search successful with {len(google_results)} results")
                    all_search_results.append(google_results)
            
            # Merge all search results and remove duplicates
            merged_results = self._merge_search_results(all_search_results)
            
            if not merged_results:
                return {
                    "success": False,
                    "error": "No search results found or API error",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 3: First try to analyze with GPT-4.1 via LiteLLM
            logger.info("Analyzing search results with GPT-4.1...")
            analysis = self.gpt41_analyze_search_results(query, merged_results)
            used_model = "gpt-4.1"
            
            # Step 4: If GPT-4.1 analysis fails, fall back to Gemini
            if not analysis:
                logger.info("GPT-4.1 analysis failed, falling back to Gemini...")
                analysis = self.gemini_analyze_search_results(query, merged_results)
                used_model = "gemini-2.5-flash"
            
            # Step 5: If both analyses fail, create a simple analysis
            if not analysis:
                logger.warning("Both GPT-4.1 and Gemini analyses failed, creating basic analysis...")
                analysis = self._create_fallback_analysis(
                    query, 
                    merged_results, 
                    "All analysis models failed"
                )
                used_model = "basic-extraction"
            
            # Step 6: Generate enhanced visualization data
            logger.info("Generating visualization data...")
            visual_data = self.generate_visual_data(analysis)
            
            # Combine everything into a comprehensive result
            result = {
                "success": True,
                "query": query,
                "search_results": merged_results,
                "analysis": analysis,
                "visual_data": visual_data,
                "timestamp": datetime.now().isoformat(),
                "sources_count": len(merged_results),
                "model_used": used_model,
                "search_providers_used": [
                    {"name": "Tavily", "results_count": len(tavily_results)},
                    {"name": "Google", "results_count": len(google_results) if 'google_results' in locals() else 0}
                ]
            }
            
            # Cache the result
            self._save_to_cache(query, result)
            
            return result
        except Exception as e:
            logger.error(f"Error in research process: {e}", exc_info=True)
            
            # Create minimal result with error information
            error_message = str(e)
            return {
                "success": False,
                "query": query,
                "error": error_message,
                "search_results": [],
                "analysis": {
                    "comprehensive_answer": f"An error occurred during the research process: {error_message}",
                    "reasoning_process": "Research process was interrupted by an error.",
                    "insights": [{"subtopic": "Error", "points": [error_message], "confidence": 0, "reasoning": "Error occurred during analysis."}],
                    "sources": [],
                    "research_gaps": ["Research incomplete due to error."],
                    "conflicting_info": ["Research incomplete due to error."]
                },
                "visual_data": {
                    "topics": [], 
                    "source_ratings": [], 
                    "connections": [], 
                    "research_gaps": [], 
                    "conflicting_info": [],
                    "reasoning_process": f"Research process failed: {error_message}"
                },
                "timestamp": datetime.now().isoformat()
            }

@function_tool
def deep_research(query: str) -> Dict:
    """Perform comprehensive web research on any topic with advanced analysis capabilities, delivering a structured report with chain-of-thought reasoning, reliability assessments, and properly cited sources that enable an AI Agent to provide thoroughly researched, evidence-based answers to complex questions; Args: query (str): the research question or topic to investigate; Returns: str: a markdown-formatted comprehensive research report with analysis and sources."""

    disable_cache: bool = False, 
    num_results: int = 10

    # Create researcher instance
    research_tool = DeepResearch(disable_cache=disable_cache)
    
    # Perform research
    temp_research_result = research_tool.perform_research(query, num_results=num_results)

    markdown_report = generate_markdown_report(temp_research_result, include_all_sources=True)

    return markdown_report

def print_research_report(result: Dict) -> None:
    """
    Print a formatted version of the research results to the console.
    
    Args:
        result (Dict): Research results from deep_research()
    """
    if not result.get("success"):
        print(f"\nResearch failed: {result.get('error')}")
        return
        
    print("\n===== Deep Research Result =====")
    print(f"Query: {result['query']}")
    
    print("\n--- Analysis Model Used ---")
    print(f"Model: {result.get('model_used', 'Unknown')}")
    
    print("\n--- Chain of Thought Reasoning ---")
    print(result['analysis'].get('reasoning_process', 'No reasoning process provided'))
    
    print("\n--- Comprehensive Answer ---")
    print(result['analysis']['comprehensive_answer'])
    
    print("\n--- Key Insights ---")
    for insight in result['analysis']['insights']:
        print(f"  Subtopic: {insight['subtopic']} (Confidence: {insight.get('confidence', 'N/A')}/10)")
        print(f"  Reasoning: {insight.get('reasoning', 'No reasoning provided')}")
        for point in insight['points']:
            print(f"    - {point}")
    
    print("\n--- Research Gaps ---")
    for gap in result['analysis'].get('research_gaps', ['None identified']):
        print(f"  - {gap}")
        
    print("\n--- Conflicting Information ---")
    for conflict in result['analysis'].get('conflicting_info', ['None identified']):
        print(f"  - {conflict}")
    
    print("\n--- Top Sources ---")
    for i, source in enumerate(result['analysis']['sources'][:5]): # Show top 5
        print(f"  {i+1}. Title: {source['title']}")
        print(f"     URL: {source['url']}")
        print(f"     Relevance: {source['relevance_score']}/10")
        print(f"     Reliability: {source.get('reliability', 'N/A')}/10")
        print(f"     Reasoning: {source.get('reasoning', 'No reasoning provided')}")
        print(f"     Contribution: {source['key_contribution']}")
    
    print(f"\n--- Search Providers Used ---")
    for provider in result.get('search_providers_used', []):
        print(f"  {provider['name']}: {provider['results_count']} results")

def generate_markdown_report(result: Dict, include_all_sources: bool = False) -> str:
    """
    Generate a nicely formatted Markdown report from research results.
    
    Args:
        result (Dict): Research results from deep_research()
        include_all_sources (bool): Whether to include all sources or just top 5
        
    Returns:
        str: Markdown formatted research report
    """
    if not result.get("success"):
        return f"# Research Failed\n\n**Error:** {result.get('error')}\n"
    
    # Start with the title and basic info
    md = f"# Deep Research: {result['query']}\n\n"
    md += f"*Analysis by {result.get('model_used', 'AI')} | "
    md += f"Generated on {result.get('timestamp', datetime.now().isoformat())}*\n\n"
    
    # Add the process overview
    md += "## Research Process\n\n"
    md += "This report was generated using an advanced research process:\n\n"
    md += "1. **Web Search**: Gathered information from multiple sources using "
    
    # Add search provider info
    search_providers = []
    for provider in result.get('search_providers_used', []):
        if provider['results_count'] > 0:
            search_providers.append(f"{provider['name']} ({provider['results_count']} results)")
    md += " and ".join(search_providers) + ".\n"
    
    md += "2. **Analysis**: Used AI to analyze and synthesize information with chain-of-thought reasoning.\n"
    md += "3. **Verification**: Cross-referenced sources and identified areas of consensus and conflict.\n"
    md += "4. **Synthesis**: Organized findings into a comprehensive answer with supporting evidence.\n\n"
    
    # Add comprehensive answer
    md += "## Executive Summary\n\n"
    md += f"{result['analysis']['comprehensive_answer']}\n\n"
    
    # Add reasoning process if available
    if result['analysis'].get('reasoning_process'):
        md += "## Analysis Methodology\n\n"
        md += f"{result['analysis']['reasoning_process']}\n\n"
    
    # Add key insights
    md += "## Key Insights\n\n"
    for insight in result['analysis']['insights']:
        # Add confidence emoji based on score
        confidence = insight.get('confidence', 5)
        if confidence >= 8:
            confidence_emoji = "🔍 **High Confidence**"
        elif confidence >= 5:
            confidence_emoji = "⚖️ **Medium Confidence**"
        else:
            confidence_emoji = "⚠️ **Low Confidence**"
            
        md += f"### {insight['subtopic']} ({confidence_emoji})\n\n"
        
        # Add reasoning if available
        if insight.get('reasoning'):
            md += f"*{insight['reasoning']}*\n\n"
        
        # Add points
        for point in insight['points']:
            md += f"- {point}\n"
        md += "\n"
    
    # Add research gaps
    if result['analysis'].get('research_gaps'):
        md += "## Areas Needing Further Research\n\n"
        for gap in result['analysis']['research_gaps']:
            if gap.lower() != "no specific research gaps identified.":
                md += f"- {gap}\n"
        md += "\n"
    
    # Add conflicting information
    if result['analysis'].get('conflicting_info'):
        conflicting_info = [item for item in result['analysis']['conflicting_info'] 
                          if item.lower() != "no conflicting information identified."]
        if conflicting_info:
            md += "## Conflicting Information\n\n"
            for item in conflicting_info:
                md += f"- {item}\n"
            md += "\n"
    
    # Add sources
    md += "## Sources\n\n"
    sources = result['analysis']['sources']
    source_limit = len(sources) if include_all_sources else min(5, len(sources))
    
    for i, source in enumerate(sources[:source_limit]):
        reliability = source.get('reliability', 5)
        rel_emoji = "⭐" * min(5, max(1, round(reliability/2)))
        
        md += f"### {i+1}. {source['title']}\n\n"
        md += f"**URL**: [{source['url']}]({source['url']})\n\n"
        md += f"**Reliability**: {rel_emoji} ({reliability}/10)\n\n"
        
        if source.get('reasoning'):
            md += f"**Assessment**: {source['reasoning']}\n\n"
            
        md += f"**Contribution**: {source['key_contribution']}\n\n"
    
    # Add note about additional sources if not showing all
    if not include_all_sources and len(sources) > source_limit:
        md += f"*Plus {len(sources) - source_limit} additional sources not shown.*\n\n"
    
    # Add footer
    md += "---\n\n"
    md += "*Generated by Deep Research Tool - An AI-powered research assistant.*\n"
    
    return md

# Example usage
# if __name__ == "__main__":
#     # Test with the specified query about Erling Haaland
#     query = "what are some of the best indicators for btc trading ?"
#     print(f"\nPerforming deep research for: '{query}'")
    
#     # Run with cache disabled to get fresh results
#     research_result = deep_research(query, disable_cache=True)
    
#     # Print the report to console
#     print_research_report(research_result)
    
#     # Generate markdown report
#     markdown_report = generate_markdown_report(research_result, include_all_sources=True)
    
#     # Create directory for reports if it doesn't exist
#     os.makedirs("reports", exist_ok=True)
    
#     # Save the markdown to a file
#     report_filename = f"reports/research_{int(time.time())}.md"
#     with open(report_filename, "w") as f:
#         f.write(markdown_report)
    
#     print(f"\nMarkdown report saved to: {report_filename}")
#     print("You can preview this report in any Markdown viewer or editor.")
    