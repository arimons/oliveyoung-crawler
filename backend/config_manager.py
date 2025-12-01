import os
from dotenv import load_dotenv, set_key

# Project root directory (backend/.. -> project_root)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

class ConfigManager:
    """
    Configuration manager that loads API keys from .env file.
    Prompts are now hardcoded in the frontend.
    Supports both OpenAI (GPT) and Google (Gemini) models.
    """
    
    def __init__(self):
        # Load .env file from project root
        self.env_path = os.path.join(PROJECT_ROOT, '.env')
        load_dotenv(self.env_path)
    
    def reload_env(self):
        """
        Force reload environment variables from .env file
        """
        load_dotenv(self.env_path, override=True)

    def get_api_key(self, model: str = '') -> str:
        """
        Get appropriate API key based on model name.
        Always reloads .env to get the latest values.
        
        Args:
            model: Model name (e.g., 'gpt-4o-mini', 'gemini-2.5-flash')
        
        Returns:
            str: The API key for the specified model, or empty string if not set
        """
        # Reload environment variables to get latest values
        self.reload_env()
        
        # Determine which API key to use based on model name
        if model.startswith('gemini'):
            return os.getenv('GOOGLE_API_KEY', '')
        else:
            # Default to OpenAI for GPT models
            return os.getenv('OPENAI_API_KEY', '')

    def save_api_key(self, key_name: str, key_value: str) -> bool:
        """
        Save API key to .env file.
        """
        try:
            # Create .env if it doesn't exist
            if not os.path.exists(self.env_path):
                with open(self.env_path, 'w') as f:
                    f.write('')
            
            # set_key writes to the file
            # If the file is malformed, set_key might fail or fix it.
            # We'll assume it handles it or we catch the error.
            result = set_key(self.env_path, key_name, key_value)
            
            # Reload environment variables to reflect changes immediately
            load_dotenv(self.env_path, override=True)
            return True
        except Exception as e:
            print(f"Error saving API key: {e}")
            return False

