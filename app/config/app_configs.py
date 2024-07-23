from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "AIResume"
    gemini_api_key: str = "gemini_api_key"
    firebase_api_key: str
    firebase_auth_domain: str
    firebase_project_id: str
    firebase_storage_bucket: str
    firebase_messaging_sender_id: str
    firebase_app_id: str
    firebase_measurement_id: str
    firebase_database_url: str

    model_config = SettingsConfigDict(env_file="app/config/.env")

settings = Settings()
   
        

