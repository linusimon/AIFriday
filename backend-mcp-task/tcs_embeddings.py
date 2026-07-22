import os
import httpx
from langchain_openai import OpenAIEmbeddings
from config import Config

class TCSGenAIEmbeddings(OpenAIEmbeddings):
    """
    Custom embeddings class for TCS GenAI Lab integration.
    Extends OpenAIEmbeddings to work with TCS GenAI Lab's API.
    """
    def __init__(self, **kwargs):
        # Disable SSL verification for TCS GenAI Lab internal environment
        # Add timeout configuration (60 seconds for connect, 120 seconds for read)
        timeout = httpx.Timeout(60.0, connect=60.0, read=120.0)
        client = httpx.Client(verify=False, timeout=timeout)
        
        # Get the embedding model name from config or use the default one
        model_name = getattr(Config, "EMBEDDING_MODEL", "azure/genailab-maas-text-embedding-3-large")
        
        # Initialize OpenAIEmbeddings with GenAI Lab configuration
        super().__init__(
            model=model_name,
            openai_api_key=Config.GENAI_API_KEY,
            openai_api_base=Config.GENAI_BASE_URL,
            http_client=client,
            **kwargs
        )
