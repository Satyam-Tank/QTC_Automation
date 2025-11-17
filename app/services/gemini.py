import logging
import json  # <-- MOVED IMPORT TO THE TOP
import google.generativeai as genai
from typing import Dict, Any

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class GeminiService:
    """A service for interacting with the Google Gemini API."""
    
    def __init__(self, api_key: str):
        if not api_key:
            logger.error("GOOGLE_API_KEY is not set. The AI service cannot start.")
            raise ValueError("GOOGLE_API_KEY is required.")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-pro')
            logger.info("Gemini Service configured successfully.")
        except Exception as e:
            logger.error(f"Failed to configure Gemini: {e}")
            raise
            
    def get_structured_json(self, prompt: str) -> Dict[str, Any]:
        """
        Sends a prompt to Gemini and expects a clean JSON string in response.
        """
        logger.info("Sending prompt to Gemini...")
        raw_text = "" # Initialize in case of error
        try:
            response = self.model.generate_content(prompt)
            
            raw_text = response.text
            json_text = raw_text.strip().lstrip("```json").rstrip("```")
            
            data = json.loads(json_text)
            logger.info("Successfully received and parsed structured JSON from Gemini.")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from Gemini response: {e}")
            logger.error(f"Gemini raw response: {raw_text}")
            raise
        except Exception as e:
            # This will now correctly catch the API Key error
            logger.error(f"Error calling Gemini API: {e}", exc_info=True)
            raise

# --- Helper function for our job ---
def get_structured_data_from_ai(full_context: str) -> Dict[str, Any]:
    """
    A helper function that our processing.py job can call.
    It combines the context with the rulebook prompt.
    """
    from app.parsing.prompts import get_extraction_prompt
    
    service = GeminiService(api_key=settings.GOOGLE_API_KEY)
    prompt = get_extraction_prompt(full_context)
    structured_data = service.get_structured_json(prompt)
    
    return structured_data
