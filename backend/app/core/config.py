from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()



class Settings(BaseSettings):
    # App
    APP_NAME: str = "LegalGPT API"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:halua12345@localhost:5432/deepagent_db"
    
    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "legal_documents"
    
    # Auth
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gpt-oss:120b-cloud"
    GEMINI_API_KEY:str = "your-gemini-api-key"
    GROQ_API_KEY:str = "your-groq-api-key"
    DEEPSEEK_API_KEY:str = "your-deepseek-api-key"
    TAVILY_API_KEY:str = "your-tavily-api-key"
    ASSEMBLY_AI:str = "your-assembly-ai-api-key"
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"


settings = Settings()
