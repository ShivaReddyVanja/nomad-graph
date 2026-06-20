import os
import requests
from typing import Type, TypeVar
from pydantic import BaseModel
from src.agents.base import generate_structured_output

SERP_API_KEY = os.getenv("SERP_API_KEY", "").strip('"').strip("'")

T = TypeVar("T", bound=BaseModel)

def google_search_snippets(query: str, limit: int = 5) -> str:
    """
    Queries SerpAPI Google Search and aggregates snippets from the search results.
    """
    if not SERP_API_KEY:
        print("[Search Tool] Warning: SERP_API_KEY is missing.")
        return ""
        
    url = "https://serpapi.com/search.json"
    params = {
        "q": query,
        "api_key": SERP_API_KEY,
        "engine": "google"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        snippets = []
        
        # 1. Capture Google Answer Box if present
        answer_box = data.get("answer_box", {})
        if answer_box:
            ans = answer_box.get("answer") or answer_box.get("snippet") or answer_box.get("title")
            if ans:
                snippets.append(f"Answer Box: {ans}")
                
        # 2. Capture Google Knowledge Graph description if present
        kg = data.get("knowledge_graph", {})
        if kg:
            desc = kg.get("description")
            if desc:
                snippets.append(f"Knowledge Graph: {desc}")
                
        # 3. Capture organic results snippets
        organic = data.get("organic_results", [])
        for res in organic[:limit]:
            title = res.get("title", "")
            snippet = res.get("snippet", "")
            if title or snippet:
                snippets.append(f"Result Title: {title}\nSnippet: {snippet}")
                
        return "\n\n".join(snippets)
    except Exception as e:
        print(f"[Search Tool] Google Search failed for query '{query}': {e}")
        return ""

def search_and_extract_fact(
    query: str,
    system_prompt: str,
    extraction_prompt: str,
    output_schema: Type[T]
) -> T:
    """
    1. Runs a Google Search for the given query.
    2. Aggregates search snippets.
    3. Passes the search snippets to the LLM to extract the structured output conforming to output_schema.
    """
    # 1. Search Google
    search_context = google_search_snippets(query)
    
    # 2. Construct prompts
    final_system_prompt = (
        f"{system_prompt}\n\n"
        "You will be provided with Google search results (context) below. "
        "Use this context to accurately answer/extract the required fields. "
        "If the context is empty or unhelpful, use your pre-trained knowledge to answer as best as possible."
    )
    
    final_user_prompt = (
        f"Context from Google Search:\n"
        "=========================\n"
        f"{search_context or 'No search results available.'}\n"
        "=========================\n\n"
        f"{extraction_prompt}"
    )
    
    # 3. Call LLM for structured output extraction
    return generate_structured_output(
        system_prompt=final_system_prompt,
        user_prompt=final_user_prompt,
        output_schema=output_schema
    )
