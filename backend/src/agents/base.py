import os
from typing import Type, TypeVar
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

# Load environment variables (force override of existing shell keys)
load_dotenv(override=True)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,  # 0 is best for structured extraction and logical tasks
    google_api_key=os.getenv("GEMINI_API_KEY")
)

T = TypeVar("T", bound=BaseModel)

def generate_structured_output(
    system_prompt: str,
    user_prompt: str,
    output_schema: Type[T]
) -> T:
    """
    Sends prompts to Gemini and guarantees the return matches the Pydantic output_schema.
    """
    # LangChain's built-in support for Gemini structured outputs
    structured_llm = llm.with_structured_output(output_schema)
    
    # Run the model
    messages = [
        ("system", system_prompt),
        ("human", user_prompt)
    ]
    return structured_llm.invoke(messages)