import os
from dotenv import load_dotenv

# Load dotenv relative to the directory of config.py
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_dir, '.env'))

class Config:
    # Flask Configuration
    FLASK_PORT = 5004
    FLASK_HOST = "0.0.0.0"
    DEBUG = True

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")

    # TCS GenAI Lab Configuration
    GENAI_API_KEY = os.getenv("HF_TOKEN")
    GENAI_BASE_URL = "https://genailab.tcs.in/"
    CHAT_MODEL = "azure/genailab-maas-gpt-4o"
    EMBEDDING_MODEL = "azure/genailab-maas-text-embedding-3-large"

    # Database Configuration
    DATABASE_PATH = "task_routing.db"

    # File Upload Configuration
    UPLOAD_FOLDER = "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'csv', 'json', 'xml', 'png', 'jpg', 'jpeg'}

    # RAG Configuration
    FAISS_INDEX_PATH = "faiss_index"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
