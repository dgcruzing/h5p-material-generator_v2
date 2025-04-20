"""Configuration management for H5P Material Generator."""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Union

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
TEMP_DIR = BASE_DIR / "temp"
DB_PATH = DATA_DIR / "prompt_frameworks.db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# API configuration
API_KEYS: Dict[str, str] = {
    "groq": os.getenv("GROQ_API_KEY", ""),
    "openai": os.getenv("OPENAI_API_KEY", ""),
    "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
    "google_gemini": os.getenv("GOOGLE_API_KEY", ""),
}

# Available models per provider (lowercase provider names)
AVAILABLE_MODELS: Dict[str, List[str]] = {
    "groq": [
        "mistral-saba-24b",
        "deepseek-r1-distill-llama-70b",
        "qwen-qwq-32b",
        "llama-3.3-70b-versatile",
        "gemma2-9b-it",
    ],
    "openai": ["gpt-4o-mini"],
    "anthropic": ["claude-3-5-sonnet-20241022"],
    "google gemini": ["gemini-1.5-flash"],
}

# Default models per provider
DEFAULT_MODELS: Dict[str, str] = {
    "groq": "mistral-saba-24b",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-20241022",
    "google_gemini": "gemini-1.5-flash",
}

# Token limits for different models (Context Window)
# Add limits for the new Groq models based on https://console.groq.com/docs/models
TOKEN_LIMITS: Dict[str, int] = {
    # Groq
    "mistral-saba-24b": 32 * 1024, # 32k
    "deepseek-r1-distill-llama-70b": 128 * 1024, # 128k
    "qwen-qwq-32b": 128 * 1024, # 128k
    "llama-3.3-70b-versatile": 128 * 1024, # 128k
    "gemma2-9b-it": 8192, # 8k
    # OpenAI
    "gpt-4o-mini": 16384,
    # Anthropic
    "claude-3-5-sonnet-20241022": 200000,
    # Google
    "gemini-1.5-flash": 32768,
}

# Error messages
ERROR_MESSAGES: Dict[str, str] = {
    "api_key_missing": "API key is required. Please provide a valid key.",
    "pdf_extraction_failed": "Failed to extract text from PDF. The file might be encrypted or corrupted.",
    "json_parsing_error": "Failed to parse JSON response from API. Try a different prompt or API.",
    "h5p_generation_error": "Failed to generate H5P package. Please try again.",
    "framework_exists": "Framework '{name}' already exists.",
    "framework_delete_failed": "Failed to delete framework '{name}'.",
    "generation_error_prefix": "Error generating content:",
    "unexpected_error_prefix": "An unexpected error occurred:",
}
