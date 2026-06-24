import os
from typing import Type, TypeVar, Any
from dotenv import load_dotenv
from google import genai
from google.genai.types import HttpOptions, GenerateContentConfig
from pydantic import BaseModel

# Load environment variables (force override of existing shell keys)
load_dotenv(override=True)

# Initialize the Google GenAI Client
# The SDK automatically detects GOOGLE_API_KEY and GOOGLE_GENAI_USE_ENTERPRISE from the environment variables.
client = genai.Client(http_options=HttpOptions(api_version="v1"))

T = TypeVar("T", bound=BaseModel)

def generate_structured_output(
    system_prompt: str,
    user_prompt: str,
    output_schema: Type[T]
) -> T:
    """
    Sends prompts to Gemini using the google-genai SDK and guarantees 
    the return matches the Pydantic output_schema.
    """
    config = GenerateContentConfig(
        system_instruction=system_prompt,
        response_mime_type="application/json",
        response_schema=output_schema,
        temperature=0.0
    )
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_prompt,
        config=config
    )
    
    return response.parsed

# Compatibility layer for captain.py to use `llm.invoke(...)`
class GoogleGenAiLLMWrapper:
    def invoke(self, messages: list) -> Any:
        system_instruction = ""
        user_prompt = ""
        
        for m in messages:
            if isinstance(m, tuple):
                role, content = m
            else:
                role = m.type if hasattr(m, 'type') else 'human'
                content = m.content if hasattr(m, 'content') else str(m)
                
            if role == "system":
                system_instruction = content
            elif role in ("human", "user"):
                user_prompt = content
                
        config = GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.0
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=config
        )
        
        class MockResponse:
            def __init__(self, content):
                self.content = content
                
        return MockResponse(response.text)

llm = GoogleGenAiLLMWrapper()