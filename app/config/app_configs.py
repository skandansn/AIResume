from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "AIResume"
    gemini_api_key: str = "gemini_api_key"
    output_resume_name: str = "AIResume"

    model_config = SettingsConfigDict(env_file="app/config/.env")

settings = Settings()
   
        

